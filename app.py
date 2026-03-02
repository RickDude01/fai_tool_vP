import json
import os
import sys
import threading
import time
import uuid

from flask import Flask, flash, redirect, render_template, request, session, url_for
from markupsafe import Markup

from utils.aliases import expand_vendor, get_other_aliases, load_aliases
from utils.excel_parser import (
    find_pn_column,
    find_supplier_column,
    get_sheet_names,
    get_suggestions_for_sheet,
    load_sheet_rows,
    search_rows,
)
from utils.whitelist import check_whitelist, get_pn_segment_status, get_whitelist_status, load_whitelist
from utils.update_check import get as _get_update, start as _start_update_check
from version import VERSION


def _base_path() -> str:
    """Return the base directory for bundled resources.

    When frozen by PyInstaller, files are extracted to sys._MEIPASS.
    During normal development the project root directory is used.
    """
    return getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))


def _runtime_dir() -> str:
    """Return the directory of the running executable (or script when developing).

    Uploads must be written next to the .exe, not inside the temporary
    _MEIPASS extraction directory that PyInstaller deletes on exit.
    """
    if getattr(sys, "frozen", False):
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.dirname(os.path.abspath(__file__))


BASE_PATH = _base_path()

app = Flask(
    __name__,
    template_folder=os.path.join(BASE_PATH, "templates"),
    static_folder=os.path.join(BASE_PATH, "static"),
)

# Start background version check — runs once at import time.
_start_update_check()
app.secret_key = os.environ.get("SECRET_KEY", "fai-tool-dev-key-change-in-prod")

# Unique token for this server process — used by the browser ping to detect restarts.
_SERVER_START = str(time.time())


@app.route("/_ping")
def ping():
    """Heartbeat endpoint — lets the browser detect a server restart and auto-reload."""
    return _SERVER_START


@app.template_filter("highlight_segments")
def highlight_segments_filter(base_pn: str, segments: list) -> Markup:
    """Highlight every segment in *segments* that appears in base_pn."""
    segments_upper = {s.upper() for s in segments}
    parts = base_pn.split("-")
    result = []
    for part in parts:
        if part.upper() in segments_upper:
            result.append(f'<span class="seg-highlight">{part}</span>')
        else:
            result.append(part)
    return Markup("-".join(result))

UPLOAD_FOLDER = os.path.join(_runtime_dir(), "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def load_tooltips() -> dict:
    """Load section tooltip copy from tooltips.json."""
    path = os.path.join(BASE_PATH, "tooltips.json")
    with open(path, encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html", version=VERSION, update_info=_get_update())


@app.route("/upload", methods=["POST"])
def upload():
    workflow_file = request.files.get("workflow_file")
    whitelist_file = request.files.get("whitelist_file")

    if not workflow_file or not workflow_file.filename:
        flash("Workflow FAI Vendor file is required.", "danger")
        return redirect(url_for("index"))
    if not workflow_file.filename.lower().endswith(".xlsx"):
        flash("Workflow file must be a .xlsx file.", "danger")
        return redirect(url_for("index"))
    if not whitelist_file or not whitelist_file.filename:
        flash("FAI Whitelist file is required.", "danger")
        return redirect(url_for("index"))
    if not whitelist_file.filename.lower().endswith(".xlsx"):
        flash("Whitelist file must be a .xlsx file.", "danger")
        return redirect(url_for("index"))

    # BUG-7: Delete previous session's uploaded files before saving new ones.
    for key in ("workflow_path", "whitelist_path"):
        old_path = session.get(key)
        if old_path and os.path.exists(old_path):
            try:
                os.remove(old_path)
            except OSError:
                pass  # don't block the upload if deletion fails

    session_id = str(uuid.uuid4())
    workflow_path = os.path.join(UPLOAD_FOLDER, f"{session_id}_workflow.xlsx")
    whitelist_path = os.path.join(UPLOAD_FOLDER, f"{session_id}_whitelist.xlsx")

    workflow_file.save(workflow_path)
    whitelist_file.save(whitelist_path)

    session["workflow_path"] = workflow_path
    session["whitelist_path"] = whitelist_path
    session["sheet_names"] = get_sheet_names(workflow_path)
    return redirect(url_for("search"))


@app.route("/search", methods=["GET", "POST"])
def search():
    if "workflow_path" not in session:
        flash("Please upload your files first.", "warning")
        return redirect(url_for("index"))

    # BUG-4: Verify session file paths still exist (stale after server restart).
    if not os.path.exists(session["workflow_path"]) or \
       not os.path.exists(session.get("whitelist_path", "")):
        flash("Session files are no longer available. Please re-upload your files.", "warning")
        session.clear()
        return redirect(url_for("index"))

    sheet_names = session.get("sheet_names", [])
    report = None
    selected_sheet = sheet_names[0]
    vendor = ""
    part_number = ""

    # Build per-sheet suggestions; expand vendor_pns to include alias keys.
    # Sheets that lack the required columns get empty suggestions — the search
    # route's try/except surfaces the column error if the user searches that sheet.
    aliases = load_aliases()
    suggestions_by_sheet = {}
    for sheet in sheet_names:
        try:
            sugg = get_suggestions_for_sheet(session["workflow_path"], sheet)
        except ValueError:
            suggestions_by_sheet[sheet] = {"vendors": [], "pns": [], "vendor_pns": {}}
            continue
        vp = sugg["vendor_pns"]
        vp_lower = {k.lower(): pn_list for k, pn_list in vp.items()}
        expanded = dict(vp)
        for canonical, alias_list in aliases.items():
            all_names = [canonical] + alias_list
            combined = set()
            for name in all_names:
                combined.update(vp_lower.get(name.lower(), []))
            if combined:
                sorted_pns = sorted(combined)
                for name in all_names:
                    expanded[name] = sorted_pns
        sugg["vendor_pns"] = expanded
        suggestions_by_sheet[sheet] = sugg

    if request.method == "POST":
        raw_sheet = request.form.get("sheet", selected_sheet)
        # BUG-5: Only accept sheet names that actually exist in the workbook.
        selected_sheet = raw_sheet if raw_sheet in sheet_names else selected_sheet
        vendor = request.form.get("vendor", "").strip()
        part_number = request.form.get("part_number", "").strip()

        if not vendor and not part_number:
            flash("Enter at least a vendor or part number to search.", "warning")
        else:
            try:
                report = _build_report(
                    session["workflow_path"],
                    session["whitelist_path"],
                    selected_sheet,
                    vendor,
                    part_number,
                )
            except Exception as e:
                # BUG-6: Log raw details server-side only; show a generic message to the user.
                app.logger.error("Search error: %s", e, exc_info=True)
                flash("An error occurred while processing your search. Please check your files and try again.", "danger")

    return render_template(
        "search.html",
        sheet_names=sheet_names,
        selected_sheet=selected_sheet,
        vendor=vendor,
        part_number=part_number,
        report=report,
        suggestions_json=json.dumps(suggestions_by_sheet),
        tooltips=load_tooltips(),
        version=VERSION,
        update_info=_get_update(),
    )


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _build_report(
    workflow_path: str,
    whitelist_path: str,
    sheet_name: str,
    vendor: str,
    part_number: str,
) -> dict:
    headers, rows = load_sheet_rows(workflow_path, sheet_name)

    supplier_col = find_supplier_column(headers)
    pn_col = find_pn_column(headers)

    aliases = load_aliases()
    vendor_variants = expand_vendor(vendor, aliases)
    other_aliases = get_other_aliases(vendor, aliases)

    matched_rows = search_rows(rows, supplier_col, pn_col, vendor_variants, part_number)

    unique_pns = list(
        dict.fromkeys(row.get(pn_col, "") for row in matched_rows if row.get(pn_col, ""))
    )

    pn_to_supplier = {}
    for row in matched_rows:
        pn = row.get(pn_col, "")
        if pn and pn not in pn_to_supplier:
            pn_to_supplier[pn] = row.get(supplier_col, "")

    whitelist_rows = load_whitelist(whitelist_path)
    wl_status = get_whitelist_status(matched_rows, supplier_col, pn_col, whitelist_rows)

    # Re-check any None entries using the alias-expanded vendor list.
    # get_whitelist_status uses the raw workflow vendor string, which may be an alias
    # of the whitelist vendor and fail the direct equality check.  When a vendor was
    # searched we have all alias variants available and can retry safely.
    if vendor:
        for pn, status in list(wl_status.items()):
            if status is None:
                for v in vendor_variants:
                    match = check_whitelist(v, pn, whitelist_rows)
                    if match:
                        wl_status[pn] = match
                        break

    vendor_variants_lower = {v.lower().strip() for v in vendor_variants if v}
    debug_base_pns = sorted(
        {
            row.get("Base PN", "")
            for row in whitelist_rows
            if row.get("Vendor", "").lower().strip() in vendor_variants_lower
            and row.get("Base PN", "")
        }
    )

    # Ensure whitelist status exists for the searched PN (may not be in matched rows)
    if part_number and part_number not in wl_status and vendor:
        for v in vendor_variants:
            match = check_whitelist(v, part_number, whitelist_rows)
            if match:
                wl_status[part_number] = match
                break
        else:
            wl_status[part_number] = None

    # If the searched PN is whitelisted but absent from unique_pns (e.g. the workflow
    # only contains cable-length variants like HDM-FL-SM-LC-QSFP-M3 while the user
    # searched HDM-FL-SM-LC-QSFP), add it so the Whitelisted table surfaces it.
    # Cable-length suffixes are optional — the base PN is the canonical identifier.
    if part_number and part_number not in unique_pns and wl_status.get(part_number):
        unique_pns.append(part_number)

    # Sort unique_pns by whitelist creation date descending (newest first).
    # Not-Whitelisted PNs have no date — reverse=True pushes '' keys to the end,
    # keeping them grouped in their own table with stable insertion order.
    unique_pns.sort(
        key=lambda pn: wl_status[pn].get("Created on", "") if wl_status.get(pn) else "",
        reverse=True,
    )

    # Build checklist_pns: put the typed/searched PN first, then workflow PNs in sorted order.
    checklist_pns = (
        ([part_number] if part_number else [])
        + [pn for pn in unique_pns if pn != part_number]
    )

    pn_segment_status = {
        pn: get_pn_segment_status(pn, vendor_variants, whitelist_rows)
        for pn in checklist_pns
    }

    # Deduplicated checklist rows per PN.
    # Each entry is (whitelist_row, [segments_that_matched_this_row]), newest-first.
    # None for numeric sequential PNs (checklist n/a).
    pn_checklist_rows = {}
    for pn in checklist_pns:
        seg_status = pn_segment_status.get(pn)
        if seg_status is None:
            pn_checklist_rows[pn] = None
            continue
        seen = {}       # row_key -> list of matched segments
        row_by_key = {} # row_key -> row dict
        for segment, matches in seg_status.items():
            for row in matches:
                key = (
                    row.get("Base PN", ""),
                    row.get("Created on", ""),
                    row.get("Created by", ""),
                )
                if key not in seen:
                    seen[key] = []
                    row_by_key[key] = row
                if segment not in seen[key]:
                    seen[key].append(segment)
        sorted_keys = sorted(seen.keys(), key=lambda k: (len(seen[k]), k[1]), reverse=True)
        pn_checklist_rows[pn] = [(row_by_key[k], seen[k]) for k in sorted_keys if len(seen[k]) >= 2]

    # Re-derive segment status for chip display from qualifying rows only.
    # A chip turns green only if its segment appears in a whitelist entry that has
    # >= 2 matching segments (the same entries shown in "Show matched whitelist entries").
    for pn in checklist_pns:
        if pn_segment_status.get(pn) is None:
            continue
        display = {seg: [] for seg in pn_segment_status[pn]}
        for row, matched_segs in (pn_checklist_rows.get(pn) or []):
            for seg in matched_segs:
                if seg in display:
                    display[seg].append(row)
        pn_segment_status[pn] = display

    display_headers = [h for h in headers if h]

    return {
        "sheet_name": sheet_name,
        "vendor": vendor,
        "part_number": part_number,
        "other_aliases": other_aliases,
        "total_matched": len(matched_rows),
        "unique_pns": unique_pns,
        "checklist_pns": checklist_pns,
        "pn_to_supplier": pn_to_supplier,
        "whitelist_status": wl_status,
        "pn_segment_status": pn_segment_status,
        "pn_checklist_rows": pn_checklist_rows,
        "matched_rows": matched_rows,
        "display_headers": display_headers,
        "supplier_col": supplier_col,
        "pn_col": pn_col,
        "debug_base_pns": debug_base_pns,
    }


if __name__ == "__main__":
    from flaskwebgui import FlaskUI

    port = int(os.environ.get("PORT", 5000))

    FlaskUI(
        app=app,
        server="flask",
        port=port,
        width=1280,
        height=820,
    ).run()
