"""
Style memory — a wardrobe that survives between runs.

The wardrobe is saved as JSON in data/my_wardrobe.json (gitignored: it is the
user's own closet, not project data). The file has the same shape as
utils/data_loader.py's wardrobes, so run_agent() and suggest_outfit() need no
changes — they just receive a wardrobe that was loaded instead of hard-coded.

    load_wardrobe()                 saved wardrobe, or None if nothing is saved
    save_wardrobe(wardrobe)         write it (atomically)
    add_item(wardrobe, item)        append an item, assigning the next w_NNN id
    remove_item(wardrobe, ref)      drop an item by id or by name
    listing_to_item(listing)        turn a thrifted listing into a wardrobe item
"""

import json
import os
import tempfile

WARDROBE_PATH = os.path.join(os.path.dirname(__file__), "data", "my_wardrobe.json")

_CATEGORIES = {"tops", "bottoms", "outerwear", "shoes", "accessories"}


def load_wardrobe(path: str = WARDROBE_PATH) -> dict | None:
    """
    The saved wardrobe, or None when there isn't a usable one.

    A missing file is normal (first run). A corrupt or wrongly-shaped file is
    treated the same way rather than crashing `ask`; the file is left alone so
    nothing the user saved is silently overwritten by a read.
    """
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return None
    if not isinstance(data, dict) or not isinstance(data.get("items"), list):
        return None
    return {"items": data["items"]}


def save_wardrobe(wardrobe: dict, path: str = WARDROBE_PATH) -> None:
    """Write the wardrobe via a temp file + rename so a crash can't truncate it."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(path), suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump({"items": wardrobe["items"]}, f, indent=2, ensure_ascii=False)
            f.write("\n")
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


def _next_id(items: list[dict]) -> str:
    nums = []
    for it in items:
        sid = str(it.get("id", ""))
        if sid.startswith("w_") and sid[2:].isdigit():
            nums.append(int(sid[2:]))
    return f"w_{max(nums, default=0) + 1:03d}"


def add_item(wardrobe: dict, item: dict) -> dict:
    """Append item (assigning a fresh id) and return the stored copy. Rejects duplicate names."""
    name = item["name"].strip()
    if any(it["name"].strip().lower() == name.lower() for it in wardrobe["items"]):
        raise ValueError(f"{name!r} is already in your wardrobe.")
    if item.get("category") not in _CATEGORIES:
        raise ValueError(f"category must be one of: {', '.join(sorted(_CATEGORIES))}")
    stored = {
        "id": _next_id(wardrobe["items"]),
        "name": name,
        "category": item["category"],
        "colors": list(item.get("colors") or []),
        "style_tags": list(item.get("style_tags") or []),
        "notes": item.get("notes"),
    }
    wardrobe["items"].append(stored)
    return stored


def remove_item(wardrobe: dict, ref: str) -> dict:
    """Remove and return the item whose id or name (case-insensitive) matches ref."""
    ref_l = ref.strip().lower()
    for i, it in enumerate(wardrobe["items"]):
        if it["id"].lower() == ref_l or it["name"].strip().lower() == ref_l:
            return wardrobe["items"].pop(i)
    raise KeyError(f"nothing in your wardrobe matches {ref!r}.")


def listing_to_item(listing: dict) -> dict:
    """A thrifted listing as a wardrobe item (no id yet — add_item assigns it)."""
    return {
        "name": listing["title"],
        "category": listing["category"],
        "colors": listing.get("colors") or [],
        "style_tags": listing.get("style_tags") or [],
        "notes": f"Thrifted on {listing['platform']} for ${listing['price']:g}",
    }
