from typing import Dict, List, Optional, Set

from utils.excel_parser import get_sheet_names, load_sheet_rows


def _is_numeric_sequential(pn: str) -> bool:
    """Return True if every dash-separated segment is purely numeric (e.g. 850-001234).
    Also matches single-segment all-digit PNs (e.g. '850001234').
    The segment checklist is not applicable to these sequential IDs."""
    parts = [p for p in pn.strip().split("-") if p]
    return bool(parts) and all(p.isdigit() for p in parts)


def get_pn_segment_status(
    pn: str,
    vendor_variants: List[str],
    whitelist_rows: List[Dict[str, str]],
) -> Optional[Dict[str, List[Dict[str, str]]]]:
    """
    Split the input PN by '-' into segments and check each against whitelisted
    Base PNs for this vendor group.

    Returns {segment: [matching_whitelist_rows]} — a non-empty list means the
    segment appears in a whitelisted PN (FAI not required for that attribute);
    an empty list means FAI required.
    Returns None when the PN is a numeric sequential ID (checklist n/a).
    """
    if _is_numeric_sequential(pn):
        return None

    vendors_lower: Set[str] = {v.lower().strip() for v in vendor_variants if v}
    input_segments = [s for s in pn.strip().split("-") if s]

    # Initialize empty match lists for each segment
    result: Dict[str, List[Dict[str, str]]] = {seg: [] for seg in input_segments}

    # For each vendor-matched whitelist row, record which segments it satisfies
    for row in whitelist_rows:
        wl_vendor = row.get("Vendor", "").lower().strip()
        wl_base_pn = row.get("Base PN", "").strip()
        if wl_vendor not in vendors_lower or not wl_base_pn:
            continue
        if len(wl_base_pn.split("-")) < 2:  # skip product-type-only entries (e.g. "FT", "FA")
            continue
        wl_segments = {s.upper() for s in wl_base_pn.split("-") if s}
        for i, seg in enumerate(input_segments):
            # Segment is only confirmed if every preceding segment also appears
            # in this same whitelist entry (validates the full product context).
            if all(input_segments[j].upper() in wl_segments for j in range(i + 1)):
                result[seg].append(row)

    # Sort each segment's matches newest-first by "Created on"
    for seg in result:
        result[seg].sort(key=lambda r: r.get("Created on", ""), reverse=True)

    return result


def load_whitelist(filepath: str) -> List[Dict[str, str]]:
    """Load the first sheet of the whitelist file and return rows as dicts."""
    first_sheet = get_sheet_names(filepath)[0]
    _headers, rows = load_sheet_rows(filepath, first_sheet)
    return rows


def check_whitelist(
    vendor: str,
    part_number_vp: str,
    whitelist_rows: List[Dict[str, str]],
) -> Optional[Dict[str, str]]:
    """
    Return the first matching whitelist row, or None.

    Match criteria (both case-insensitive, stripped):
      - whitelist Vendor == vendor
      - part_number_vp starts with whitelist Base PN
    """
    if not vendor or not vendor.strip():
        raise ValueError("check_whitelist called with empty vendor.")
    if not part_number_vp or not part_number_vp.strip():
        raise ValueError("check_whitelist called with empty part_number_vp.")

    vendor_lower = vendor.lower().strip()
    pn_lower = part_number_vp.lower().strip()

    for row in whitelist_rows:
        wl_vendor = row.get("Vendor", "").lower().strip()
        wl_base_pn = row.get("Base PN", "").lower().strip()

        if not wl_vendor or not wl_base_pn:
            continue  # skip malformed whitelist rows instead of crashing

        if len(wl_base_pn.split("-")) < 2:  # skip product-type-only entries (e.g. "FT", "FA")
            continue

        if vendor_lower == wl_vendor and pn_lower.startswith(wl_base_pn):
            return row

        wl_parts = wl_base_pn.split("-")
        pn_parts = pn_lower.split("-")

        # Match when the searched PN is the Base PN minus its cable-length
        # suffix: Base PN is exactly 1 segment longer (≥5 total) and starts with
        # the searched PN.  Requires ≥5 segments so short entries like "HDM-FL"
        # (2 segs) cannot be triggered by a bare "HDM" (1 seg) search.
        if (
            vendor_lower == wl_vendor
            and len(wl_parts) >= 5
            and len(wl_parts) == len(pn_parts) + 1
            and wl_base_pn.startswith(pn_lower + "-")
        ):
            return row

        # Match cable-length variants: same segment count, all segments identical
        # except the last (cable-length code).  No minimum segment threshold —
        # single-segment entries are already excluded by the < 2 skip above, and
        # wl_parts[:-1] == pn_parts[:-1] is specific enough on its own.
        # e.g. whitelist HDM-FL-SM-LC-QSFP-M3 matches HDM-FL-SM-LC-QSFP-M2 / -MX
        #      whitelist FA-SM-LC-M3            matches FA-SM-LC-M2
        if (
            vendor_lower == wl_vendor
            and len(wl_parts) == len(pn_parts)
            and wl_parts[:-1] == pn_parts[:-1]
        ):
            return row

    return None


def get_whitelist_status(
    matched_rows: List[Dict[str, str]],
    supplier_col: str,
    pn_col: str,
    whitelist_rows: List[Dict[str, str]],
) -> Dict[str, Optional[Dict[str, str]]]:
    """
    For each unique Part Number VP in matched_rows, check whitelist.
    Uses the actual Supplier value from the row.
    Returns {part_number_vp: whitelist_row_or_None}.
    """
    pn_supplier: Dict[str, str] = {}
    for row in matched_rows:
        pn = row.get(pn_col, "")
        if pn and pn not in pn_supplier:
            pn_supplier[pn] = row.get(supplier_col, "")

    return {
        pn: check_whitelist(supplier, pn, whitelist_rows) if supplier else None
        for pn, supplier in pn_supplier.items()
    }
