import json
import os
import sys
from typing import Dict, List


def _project_root() -> str:
    """Return the project root directory.

    When frozen by PyInstaller, bundled files live in sys._MEIPASS.
    During normal development we go one level up from utils/.
    """
    if getattr(sys, "_MEIPASS", None):
        return sys._MEIPASS
    return os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))


_ALIASES_FILE = os.path.join(_project_root(), "aliases.json")


def load_aliases() -> Dict[str, List[str]]:
    """Load aliases.json."""
    with open(_ALIASES_FILE, encoding="utf-8") as f:
        return json.load(f)


def expand_vendor(vendor: str, aliases: Dict[str, List[str]]) -> List[str]:
    """
    Return the vendor plus all its known aliases.
    Matching is case-insensitive against both canonical keys and alias values.
    If no alias group is found, returns [vendor] unchanged.
    """
    vendor_lower = vendor.lower().strip()
    for canonical, alias_list in aliases.items():
        all_names = [canonical] + (alias_list or [])
        if any(n.lower().strip() == vendor_lower for n in all_names):
            return all_names
    return [vendor]


def get_other_aliases(vendor: str, aliases: Dict[str, List[str]]) -> List[str]:
    """Return the alias names that are NOT the searched vendor (for display)."""
    vendor_lower = vendor.lower().strip()
    for canonical, alias_list in aliases.items():
        all_names = [canonical] + (alias_list or [])
        if any(n.lower().strip() == vendor_lower for n in all_names):
            return [n for n in all_names if n.lower().strip() != vendor_lower]
    return []
