# Design Principles & Development Methodology

This document is the authoritative reference for how this codebase is written and evolved.
All contributions — human or AI — must follow these rules.

---

## Design Principles

### 1. Don't Overengineer
Simple beats complex. Reach for the straightforward solution first.
Dead code, speculative abstractions, and unused features must be removed.

### 2. No Fallbacks
One correct path, no alternatives. If a required file or input is missing,
raise — don't silently substitute a default. Hidden fallbacks mask bugs.

### 3. One Way
One way to do things, not many. When a helper already exists (e.g. `find_supplier_column`),
call it — never duplicate its logic elsewhere.

### 4. Clarity Over Compatibility
Clear code beats backward compatibility. Rename, restructure, and break
interfaces whenever doing so makes intent more obvious.

### 5. Throw Errors
Fail fast when preconditions aren't met. Validate at the entry point and
raise a descriptive `ValueError` — never let bad data silently propagate.

### 6. No Backups
Trust the primary mechanism. Don't hedge with secondary paths
(e.g. `|| {}`, `os.path.exists` guards, try/except around expected files).

### 7. Separation of Concerns
Each function has a single responsibility. Loading data, transforming data,
and rendering data are distinct operations and must not be interleaved.

---

## Development Methodology

### 1. Surgical Changes Only
Make minimal, focused fixes. Change only what is necessary to satisfy the
requirement. Do not refactor opportunistically in the same commit.

### 2. Evidence-Based Debugging
Add minimal, targeted logging when diagnosing a problem. Remove it once
the root cause is confirmed. Never leave debug prints in production code.

### 3. Fix Root Causes
Address the underlying issue, not just the symptom. A workaround that
papers over a bug is not a fix.

### 4. Simple > Complex
Prefer the simpler implementation. If two solutions solve the same problem,
choose the one with fewer moving parts.

### 5. Collaborative Process
Work with the author to identify the most efficient solution before writing
code. Validate the approach first; implement second.
