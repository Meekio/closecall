"""
Simple JSON-file profile store.
Keeps user display name, location preference, and style notes
without requiring an extra DB table for the prototype.
"""

import json
from pathlib import Path

_PROFILE_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "profile.json"

_DEFAULTS = {
    "name": "Your Name",
    "email": "user@example.com",
    "location": "Mumbai",
    "style_notes": "",
}


def load_profile() -> dict:
    if _PROFILE_PATH.exists():
        try:
            return {**_DEFAULTS, **json.loads(_PROFILE_PATH.read_text())}
        except Exception:
            pass
    return dict(_DEFAULTS)


def save_profile(data: dict) -> None:
    _PROFILE_PATH.parent.mkdir(parents=True, exist_ok=True)
    current = load_profile()
    current.update({k: v for k, v in data.items() if k in _DEFAULTS})
    _PROFILE_PATH.write_text(json.dumps(current, indent=2))
