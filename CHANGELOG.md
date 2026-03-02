# Changelog

All notable changes to the FAI Inspection Tool will be documented here.

---

## [1.5.13] — 2026-03-01

### Changed
- **Option A "Polished Pro" visual redesign** — full UI refresh across `style.css`,
  `search.html`, and `index.html`:
  - Navbar: deep navy (`#0f172a`) with a `#3b82f6` blue bottom accent border.
  - Cards: borderless with a soft layered box-shadow and `border-radius: 10px`.
  - Card headers: slate `#1e293b` replacing flat dark grey.
  - Section headings: left blue border accent (`#3b82f6`) replacing bottom rule.
  - Checklist chips: vivid green with green border (pass) / slate grey with grey border
    (n/a); `font-weight: 600` for both states.
  - Buttons: accent blue `#2563eb` (`btn-primary`) on Search, Upload, and View Raw Records.
  - Autocomplete suggestion hover/active: accent blue `#2563eb`.
  - PN table sticky headers: slate `#1e293b`.
  - Segment highlight: `#dbeafe` background / `#1d4ed8` text.
  - Info icon hover: `#3b82f6`.
  - Overall background: `#f1f5f9` (slightly cooler off-white).

---

## [1.5.12] — 2026-03-01

### Fixed
- **Checklist chip colours now driven by qualifying whitelist entries only** — a
  segment chip was previously coloured green if the segment appeared in ANY whitelist
  row for the vendor, including rows that only matched a single segment of the searched
  PN. Those single-segment rows are filtered out of the "Show matched whitelist entries"
  table (which requires ≥ 2 matching segments), creating a visual inconsistency where
  a chip showed green for a segment backed by no visible evidence.

  `pn_segment_status` is now re-derived from `pn_checklist_rows` after the latter is
  built: a segment is green only when it appears in at least one qualifying whitelist
  row (≥ 2 matching segments). Chip colours are now fully consistent with the expanded
  whitelist entries table.

---

## [1.5.11] — 2026-03-01

### Changed
- **Searched PN appears first in Inspection Checklist** — the part number typed into
  the search field is now always listed at the top of the Inspection Checklist section,
  regardless of where it appears (or doesn't appear) in the matched workflow rows.
- **Part Number Status tables sorted by date descending** — both the Whitelisted and
  Not Whitelisted tables are now ordered newest-first by whitelist Created on date.
  Not-Whitelisted entries (which carry no date) follow after the dated entries and
  retain their stable insertion order.

---

## [1.5.10] — 2026-03-01

### Fixed
- **Alias-aware whitelist check for Part Number Status** — `get_whitelist_status`
  compared the raw vendor string from each workflow row directly against whitelist
  vendor names. When the two strings were known aliases of the same company (e.g.
  `"WE SUM TECHNOLOGY VINH PHUC LIMITED"` in the workflow vs.
  `"WE SUM TECHNOLOGY VIETNAM COMPANY LIMITED"` in the whitelist) the equality check
  failed silently and the PN was shown as **Not Whitelisted** even though a matching
  whitelist entry existed.

  `_build_report` now performs a second pass immediately after `get_whitelist_status`:
  for every PN that returned `None`, it retries the check using the full
  alias-expanded `vendor_variants` list. Only triggered when a vendor was entered;
  PN-only searches are unaffected. Existing Whitelisted results are never overwritten.

---

## [1.5.9] — 2026-03-01

### Fixed
- **Bidirectional whitelist prefix matching** — `check_whitelist` previously used
  `pn_lower.startswith(wl_base_pn)`, which only matched when the searched PN was at
  least as long as the whitelist Base PN. Searching with a shorter prefix such as
  `FT-72SMR-M8FM8FBW` (3 segments) would silently miss a whitelist entry whose Base
  PN is `FT-72SMR-M8FM8FBW-ZP34` (4 segments) because the shorter string can never
  start with the longer one.

  The match condition is now bidirectional: a whitelist entry is considered a match
  when either (a) the searched PN starts with the Base PN (existing behaviour) **or**
  (b) the Base PN starts with the searched PN **and** the very next character in the
  Base PN is a dash (dash-boundary guard). The dash-boundary guard prevents a partial
  segment like `ZP3` from falsely matching `ZP34`.

---

## [1.5.8] — 2026-03-01

### Fixed
- **Base-prefix PN matching now scoped to 5+ segment PNs** — the v1.5.7 length-
  agnostic search stripped the last segment from any PN containing a dash, which
  caused 4-segment searches (e.g. `FT-72SMR-M8FM8FBW-ZP34`) to produce a base
  prefix of `FT-72SMR-M8FM8FBW-` and match records with a completely different
  breakout spec (e.g. `FT-72SMR-M8FM8FBW-ZP64-M12`). This produced false
  Whitelisted results for the 4-segment search while the equivalent 5-segment
  search (`FT-72SMR-M8FM8FBW-ZP34-M64`) correctly showed Not Whitelisted —
  a confusing inconsistency.

  Base-prefix matching now only activates when the searched PN has **5 or more
  segments**. For 4-segment and shorter PNs the last segment is part of the product
  spec (breakout, connector type, etc.), not the cable length, so stripping it would
  produce overly broad matches. For 5-segment PNs the last segment is always the
  length designator (e.g. `-M64`, `-MXX`) and stripping it is safe and correct.

---

## [1.5.7] — 2026-03-01

### Changed
- **Length-agnostic PN search** — when searching for a part number, the last
  dash-separated segment (the cable length designator, e.g. `-M64`, `-MXX`,
  `-M100`) is now treated as irrelevant. Searching for
  `FT-72SMR-M8FM8FBW-ZP34-M64` will find workflow rows containing
  `FT-72SMR-M8FM8FBW-ZP34-MXX` and any other length variant of the same base PN.
  Rows with a different base (e.g. `FT-72SMR-M8FM8FBW-ZP12-MXX`) are not affected.
  The existing substring and exact-match behaviour is preserved — this only adds
  matches for length variants that would previously have been missed.
- `utils/excel_parser.py` — `search_rows` now computes a `pn_base_prefix` (all
  segments except the last, followed by `-`) and ORs it into the `pn_match`
  condition alongside the existing `pn_lower in pn_val` substring check.

---

## [1.5.6] — 2026-03-01

### Fixed
- **Matched whitelist entries no longer appear when only a single segment matches** —
  `pn_checklist_rows` now requires a whitelist row to share **at least 2 segments**
  with the searched PN before it appears in the "Show matched whitelist entries"
  table. Previously, entries like `FT-144SMR-M8PFM8PFBW-E808` would appear for a
  search of `FT-12SMR-LCULCUBW-ZP01-MXX` with only `FT` highlighted, giving a
  misleading impression of relevance. The "Show matched whitelist entries" button
  disappears automatically when the filtered list is empty.
- **Static asset cache-busting** — `style.css` and `autocomplete.js` are now
  referenced with a `?v={{ version }}` query param in both `search.html` and
  `index.html`. The URL changes with every version bump, so browsers always fetch
  the latest file instead of serving a stale cached copy. This fixes the debug
  panel toggle not working after the v1.5.5 update.

---

## [1.5.5] — 2026-02-27

### Fixed
- **Single-segment whitelist Base PNs no longer cause false Whitelisted status** —
  entries like `"FT"` or `"FA"` (product-type designators with no dash) are now
  skipped in both `check_whitelist` and `get_pn_segment_status`. Previously, any
  PN starting with `"FT"` matched these entries via `startswith`, incorrectly
  marking it as Whitelisted. Multi-segment entries such as `"FT-72SMR"` continue
  to match as before. The chips still render in the Inspection Checklist — they
  simply remain grey rather than turning green when only a single-segment entry
  would have matched.

### Added
- **Secret debug panel** — clicking the version badge in the navbar toggles a
  panel that lists all whitelist Base PNs for the searched vendor group. Entries
  with no dash (single-segment) are highlighted amber so they are immediately
  visible. The panel is hidden by default and only appears after a search has been
  run.

---

## [1.5.4] — 2026-02-27

### Fixed
- **Internal server error on multi-sheet workbooks** — workbooks with sheets that
  lack "Supplier" or "Part Number VP" columns (e.g. non-FAI inspection sheets)
  caused an unhandled `ValueError` crash on page load. The suggestions loop now
  catches `ValueError` per sheet and stores empty suggestions for unsupported
  sheets. If the user searches an unsupported sheet, the existing `try/except` in
  `_build_report` surfaces a clear error message.

---

## [1.5.3] — 2026-02-27

### Removed (dead code)
- `utils/ratio.py` — `calculate_ratios` / `_categorize` were no longer imported
  after the Inspection Ratios section was removed in v1.4.7.
- `excel_parser.py` — `LOGIC_NODE_PATTERNS` constant and `detect_logic_node_columns`
  function; neither was called after the ratio removal.
- `static/style.css` — removed 39 lines of ratio-related dead rules:
  `.ratio-table`, `.pass-label`, `.fail-label`, `.np-label`, `.ratio-bar`,
  `.bar-np`, `.bar-stats`, `.stat-sep`.

### Fixed (design-principle violations)
- **No fallbacks (#7 / #11)** — `load_tooltips()` no longer catches
  `FileNotFoundError`; `load_aliases()` no longer guards with `os.path.exists`.
  Both now raise immediately if their config file is missing.
- **No fallbacks (#7 / #11)** — `autocomplete.js`: removed `|| {}` from
  `SUGGESTIONS` initialisation and `|| { vendors: [], pns: [], vendor_pns: {} }`
  from `currentSuggestions()`. The template always seeds `window.FAI_SUGGESTIONS`
  before the script runs.
- **One way (#8)** — `get_suggestions_for_sheet` now calls `find_supplier_column`
  and `find_pn_column` instead of duplicating their regex logic inline.

### Added
- `DESIGN.md` — authoritative reference for the project's 7 Design Principles
  and 5 Development Methodology rules.

---

## [1.5.2] — 2026-02-27

### Changed
- **"View Raw Records" button toggles to "Hide Raw Records"** — clicking the
  button now swaps its label to "Hide Raw Records"; clicking again restores
  "View Raw Records". Driven by Bootstrap 5's `show.bs.collapse` /
  `hide.bs.collapse` events on `#rawRecords`.
- `static/autocomplete.js` — added the toggle handler after the tooltip
  initializer (outside the autocomplete IIFE).

---

## [1.5.1] — 2026-02-27

### Fixed
- **Scroll containment in matched whitelist entries table** — scrolling inside
  the "Show matched whitelist entries" panel no longer bubbles up to the outer
  Inspection Checklist scroll wrapper when the table reaches its top or bottom
  edge. Fixed by adding `overscroll-behavior: contain` to `.checklist-match-wrapper`.

---

## [1.5.0] — 2026-02-27

### Changed
- **Inspection Checklist — scrollable PN list** — when more than ~5 part number
  entries are shown in the checklist, the list is capped at `575px` and the
  remaining items scroll within the panel. Each collapsed entry is ~115 px tall,
  so 5 fit comfortably before scrolling begins.
- `static/style.css` — added `.checklist-scroll-wrapper` (`max-height: 575px`,
  `overflow-y: auto`).
- `templates/search.html` — checklist PN loop wrapped in
  `<div class="checklist-scroll-wrapper">`.

---

## [1.4.9] — 2026-02-27

### Changed
- **"Part Numbers Found" renamed to "Part Number Status"** — better reflects
  that the module communicates the whitelist/FAI status of each part number, not
  merely that records were found.
- `templates/search.html` — heading text updated; tooltip key updated to
  `part_number_status`.
- `tooltips.json` — key renamed from `part_numbers_found` to `part_number_status`.

---

## [1.4.8] — 2026-02-26

### Added
- **Section tooltips** — an ℹ icon now appears to the right of "Part Numbers
  Found", "Inspection Checklist", and "View Raw Records". Hovering reveals a
  short description of what the section does and how it works.
- `tooltips.json` — single source of truth for all tooltip copy. Edit this file
  to update any tooltip text without touching HTML or Python.
- `app.py` — `load_tooltips()` helper loads `tooltips.json` and passes the dict
  to the search template on every request (graceful fallback to `{}` if missing).
- `static/style.css` — `.info-icon` and `.info-icon:hover` rules for the circled
  italic "i" badge.
- `static/autocomplete.js` — Bootstrap tooltip initializer appended after the
  IIFE; initializes all `[data-bs-toggle="tooltip"]` elements on page load.

---

## [1.4.7] — 2026-02-26

### Removed
- **`highlight_segment` template filter** — superseded by `highlight_segments`
  (plural) introduced in v1.4.6. The singular version was no longer called
  anywhere in the templates.
- **Inspection Ratios section** — removed the 47-line `{% if false %}` block
  from `search.html` and stopped computing ratios in `_build_report`. Removed
  the `calculate_ratios` import and the `detect_logic_node_columns` call that
  existed solely to feed the ratio calculation.

### Changed
- **Autocomplete JS extracted** — the 126-line inline autocomplete script in
  `search.html` has been moved to `static/autocomplete.js`. The template now
  seeds `window.FAI_SUGGESTIONS` in a one-liner `<script>` tag and loads the
  logic via `<script src="...autocomplete.js">`. No behaviour change.

---

## [1.4.6] — 2026-02-26

### Changed
- **Inspection Checklist — Segment column removed** — the "Segment" column is
  gone from the matched whitelist entries table. Instead, every segment from the
  searched PN that is present in a Base PN is highlighted in blue directly inside
  the Base PN cell, so a single row now shows all matched segments at once.
- **Inspection Checklist — deduplicated rows** — whitelist entries that satisfy
  multiple segments previously appeared once per segment. They now appear exactly
  once, with all matched segments highlighted together.
- `app.py` — added `highlight_segments` Jinja2 filter (plural); `_build_report`
  now builds `pn_checklist_rows` (`{pn: [(row, [matched_segs]), ...] | None}`)
  — deduplicated and sorted newest-first — and includes it in the report dict.
- `templates/search.html` — table iterates `pn_checklist_rows` instead of the
  raw `seg_status` loop; Segment `<th>` / `<td>` removed; filter changed from
  `highlight_segment` to `highlight_segments`.

---

## [1.4.5] — 2026-02-26

### Changed
- **Inspection Checklist — scrollable match table** — the "Show matched
  whitelist entries" table is now capped at ~10 visible rows (`max-height:
  310px`). Any additional rows scroll within the panel; the header row stays
  sticky so columns remain labeled during scroll.
- `static/style.css` — added `.checklist-match-wrapper` with `max-height` and
  `overflow-y: auto`; added `position: sticky` + `z-index` to
  `.checklist-match-table thead th` so the header stays fixed while scrolling.
- `templates/search.html` — replaced `<div class="table-responsive">` wrapper
  on the match table with `<div class="checklist-match-wrapper">`.

---

## [1.4.4] — 2026-02-26

### Changed
- **Matched whitelist entries sorted newest-first** — in the Inspection
  Checklist's "Show matched whitelist entries" table, rows for each segment
  are now ordered by `Created on` descending (most recent at the top).
- `utils/whitelist.py` — `get_pn_segment_status` sorts each segment's match
  list by `"Created on"` with `reverse=True` before returning.

---

## [1.4.3] — 2026-02-26

### Fixed
- **Inspection Checklist missing for 0-match searches** — the checklist was
  only rendered when the workflow contained records for the searched PN. A PN
  that exists in the whitelist but has no workflow entries would show no
  checklist. The checklist is now driven by `checklist_pns` (always includes
  the searched PN) rather than `unique_pns` (workflow matches only).

### Changed
- `app.py` — `_build_report` builds `checklist_pns` = `unique_pns` ∪
  `[searched PN]`, backfills `wl_status` for the searched PN via
  `check_whitelist` + `vendor_variants` when no matched row supplies it, and
  computes `pn_segment_status` over `checklist_pns`.
- `templates/search.html` — Inspection Checklist moved outside the
  `total_matched == 0` guard; Raw Records wrapped in a separate
  `{% if total_matched > 0 %}` block; checklist loops use `checklist_pns`.

---

## [1.4.2] — 2026-02-26

### Changed
- **Inspection Checklist — Base PN highlight** — in the "Show matched whitelist
  entries" table, the segment that triggered the green chip is now highlighted in
  blue within the Base PN cell (bold, `#cfe2ff` background, `#084298` text).
- `app.py` — registered `highlight_segment` Jinja2 template filter using
  `markupsafe.Markup` to safely inject the `<span class="seg-highlight">` wrapper.
- `static/style.css` — added `.seg-highlight` rule.

---

## [1.4.1] — 2026-02-26

### Changed
- **Inspection Checklist — matched whitelist entries** — green chips now expose
  the whitelist records behind the match. A collapsible "Show matched whitelist
  entries" link appears below the chip grid whenever at least one chip is green.
  The expanded table shows one row per (segment, whitelist entry) pair:
  Segment · Base PN · Created By · Date · Via.
- `utils/whitelist.py` — `get_pn_segment_status` now returns
  `{segment: [matching_whitelist_rows]}` instead of `{segment: bool}`. An
  empty list indicates no match (grey); a non-empty list indicates a match
  (green) and carries the rows to display.
- `static/style.css` — added `.checklist-match-table` rules.

---

## [1.4.0] — 2026-02-26

### Added
- **Inspection Checklist** — after a search, each unique Part Number in the
  result renders a chip row. The input PN is split by `"-"` into segments;
  each segment is checked against the pool of segments found in all whitelisted
  Base PNs for the searched vendor group (aliases included). A chip is
  **green ✓** when the segment appears in a whitelisted PN (FAI not required
  for that attribute) and **grey —** when it does not (FAI required).
  Numeric sequential PNs (e.g. `850-001234`) are skipped — the checklist
  is not applicable to those IDs.
- `utils/whitelist.py` — `_is_numeric_sequential(pn)` and
  `get_pn_segment_status(pn, vendor_variants, whitelist_rows)`.
- `app.py` — `_build_report` now computes and returns `pn_segment_status`
  (`{pn: {segment: bool} | None}`).
- `static/style.css` — `.checklist-grid`, `.checklist-node`,
  `.checklist-node-pass`, `.checklist-node-grey`.

### Changed
- **Part Numbers Found** — restored to visible (was hidden in draft).
- **Inspection Ratios** — hidden from the UI (`{% if false %}`). Code is
  preserved in `search.html` for future return.

---

## [1.3.0] — 2026-02-26

### Added
- **Vendor-scoped PN suggestions** — after filling the Vendor field with an exact
  match, the Part Number dropdown filters to only show part numbers associated
  with that vendor. Falls back to the full list when the vendor field is empty or
  unrecognized. Alias groups are fully supported: any alias spelling of a vendor
  maps to the combined PN list of the entire group.

### Changed
- **Inspection ratio bar labels** — bar-stats line now reads
  `✓ Pass: N (X%) · ✗ Fail: N (X%) · − Not Performed: N (X%)` so the orange
  segment is self-explanatory without a separate legend.
- **Navbar** — "AI-Assisted" renamed to "Co-built with AI" on both pages.
- `utils/excel_parser.py` — `get_suggestions_for_sheet` now returns a third key
  `vendor_pns` (`{supplier: [sorted PNs]}`).
- `app.py` — `/search` GET route expands `vendor_pns` with alias keys so every
  spelling of a vendor name resolves to the full group PN list before the JSON
  is sent to the page.

---

## [1.2.1] — 2026-02-26

### Changed
- **Navbar** — both pages now display "AI-Assisted · Author: Ricardo Munoz Jr · vX.X.X"
  in the top-right of the navbar.
- **Tab autofill** — pressing Tab in the vendor or part number field now fills the
  top suggestion (or the highlighted one if arrow-key navigation was used) and
  advances focus to the next field naturally.

---

## [1.2.0] — 2026-02-26

### Changed
- **Part Numbers Found — table layout** — Whitelisted and Not Whitelisted entries
  are now rendered as separate tables instead of badge rows. Each table shows a
  count in its header (e.g., "WHITELISTED (12)").
- **Part Numbers Found — Whitelisted columns** — Part Number, Vendor, Created By,
  Date, Via.
- **Part Numbers Found — Not Whitelisted columns** — Part Number, Vendor (sourced
  from the workflow supplier column).
- **Part Numbers Found — scrollable tables** — tables with more than ~5 rows gain
  a vertical scrollbar; the header row stays sticky during scroll.
- **Part Numbers Found — cell wrapping** — cells wrap to a maximum of two lines;
  no horizontal scrollbar is introduced.
- `app.py` — `_build_report` now builds and returns `pn_to_supplier`
  (`{part_number: supplier}`) used by the Not Whitelisted table.

---

## [1.1.1] — 2026-02-26

### Changed
- **Part Numbers Found — categories** — Whitelisted and Not Whitelisted entries
  are now rendered in separate labeled groups. A group is omitted entirely when
  it has no items.
- **Part Numbers Found — vendor display** — each Whitelisted entry now shows the
  vendor name stored in the whitelist row alongside the other metadata.
- **Part Numbers Found — date format** — "Created on" now shows only the date
  portion (`yyyy-mm-dd`), dropping the time component.
- **Part Numbers Found — no strikethrough** — removed the line-through style from
  whitelisted part numbers; the green "Whitelisted" badge and the group header
  provide sufficient visual distinction.

---

## [1.1.0] — 2026-02-26

### Added
- **Version display** — current version shown in the navbar on all pages.
- **Auto-suggest dropdowns** — vendor and part number inputs now show a live
  filtered dropdown as you type. Arrow keys navigate, Tab or Enter (with a
  highlighted item) autofill the value. Suggestions update immediately when the
  Worksheet dropdown changes.
- **Vendor aliases** — a new `aliases.json` config file maps canonical vendor
  names to their known variants. Searching for any name in a group automatically
  expands the query to include all aliases. The report shows an "Also searched
  aliases" notice listing every alias that was included.
- **Option B distribution bar** — the Inspection Ratios table now uses two
  columns (Inspection Item + Results). The Results cell shows a stacked
  pass/fail/not-performed bar with colored count and percentage labels directly
  below it, replacing the previous four-column layout.
- **Striped ratio table** — `table-striped` applied to the Inspection Ratios
  table for easier row scanning.
- **`version.py`** — single source of truth for the version string, imported by
  `app.py` and passed to all templates.

### Changed
- `utils/excel_parser.py` — `search_rows` now accepts `vendors: List[str]`
  instead of a single `vendor: str` to support alias expansion.
- `utils/excel_parser.py` — added `get_suggestions_for_sheet()` for autocomplete
  data, used by the `/search` route on every GET request.
- `app.py` — `/search` GET builds per-sheet suggestion data and passes it to the
  template as a JSON blob (`suggestions_json`).
- `app.py` — `_build_report` calls `expand_vendor` and `get_other_aliases` before
  running `search_rows`.
- `static/style.css` — removed `.pass-cell`, `.fail-cell`, `.np-cell`,
  `.ratio-pct`, and `.ratio-legend` rules that are no longer referenced. Added
  `.suggest-wrap`, `.suggest-list`, `.bar-stats`, `.stat-sep`, `.alias-notice`,
  and `.alias-badge` rules.

---

## [1.0.0] — 2026-02-25

### Added
- Initial release.
- Upload page for Workflow FAI Vendor (`.xlsx`) and FAI Whitelist (`.xlsx`) files.
- Worksheet selector with per-sheet search by vendor (supplier) and part number.
- Whitelist matching — prefix match on Part Number VP against whitelist Base PN
  with exact vendor match; matched part numbers shown with strikethrough and a
  "Whitelisted" badge including creator, date, and approval method.
- Three-way inspection ratio — PASS / FAIL / NOT PERFORMED counts and percentages
  per detected logic node column (Optical Test, Polarity Test, Components,
  Fitment, Form, Cable Type, Labels, Drawing, Length, Optical Performance Data,
  Packaging).
- Stacked progress bar per logic node for visual distribution at a glance.
- Collapsible raw records table showing all matched rows with full column data.
- Fail-fast error handling throughout — missing columns, bad file formats, and
  blank searches all surface clear messages rather than silent fallbacks.
