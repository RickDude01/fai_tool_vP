"""Background version checker.

On startup, fetches a small JSON file you control (hosted on GitHub Gist).
If the version listed there differs from the running version, stores the info
so the templates can display an update banner.

Hosted JSON format:
    {"version": "1.0.1", "download_url": "https://github.com/USER/REPO/releases/download/v1.0.1/FAI_Tool.exe"}

Update workflow:
    1. Build new FAI_Tool.exe → upload as a new GitHub Release (vX.X.X)
    2. Edit the Gist JSON: bump "version" and set "download_url" to the release asset URL
    3. Every running app shows the yellow update banner on its next launch
"""

import json
import threading
import urllib.request
from version import VERSION

# ---------------------------------------------------------------------------
# Replace this placeholder with your actual GitHub Gist stable raw URL.
# Format: https://gist.githubusercontent.com/USERNAME/GIST_ID/raw/latest_version.json
# (Remove the commit-hash segment so the URL always returns the latest content.)
# ---------------------------------------------------------------------------
UPDATE_URL = "https://github.com/RickDude01/fai_tool_vP/releases/download/v1.0.0/FAI_Tool.exe"

_update_info: "dict | None" = None


def _fetch() -> None:
    global _update_info
    try:
        with urllib.request.urlopen(UPDATE_URL, timeout=4) as resp:
            data = json.loads(resp.read())
            if data.get("version", "") != VERSION:
                _update_info = data
    except Exception:
        pass  # silent failure — no network, bad URL, firewall, etc.


def start() -> None:
    """Kick off the background update check. Call once at app startup."""
    threading.Thread(target=_fetch, daemon=True).start()


def get() -> "dict | None":
    """Return the update info dict if a newer version is available, else None."""
    return _update_info
