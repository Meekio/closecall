"""
get_wardrobe_state tool — queries the wardrobe database on the agent's behalf.
"""

import json
from typing import Any
from src.database.db import query_items, get_all_items


def get_wardrobe_state(user_id: str = "default_user", filters: dict | str | None = None) -> dict:
    """
    Query the wardrobe database for items matching the given filters.

    Args:
        user_id:  The user's ID (default: "default_user").
        filters:  A dict (or JSON string) of filter criteria. Supported keys:
                    status          str    "clean" | "dirty"
                    category        str    "top" | "bottom" | "one_piece" | "footwear" | "outerwear"
                    categories      list   e.g. ["top", "bottom", "footwear"]
                    min_formality   int    1–5
                    max_formality   int    1–5
                    rain_suitable   bool
                    season          str    "summer" | "winter" | "monsoon" | "spring" | "all-season"

    Returns:
        dict with:
            items        list of item dicts
            total_count  int
            filters_used dict
    """
    # The LLM may pass filters as a JSON string
    if isinstance(filters, str):
        try:
            filters = json.loads(filters)
        except (json.JSONDecodeError, TypeError):
            filters = {}

    filters = filters or {}

    # Normalise types that the LLM might get wrong
    if "rain_suitable" in filters and isinstance(filters["rain_suitable"], str):
        filters["rain_suitable"] = filters["rain_suitable"].lower() == "true"

    if "min_formality" in filters:
        filters["min_formality"] = int(filters["min_formality"])

    if "max_formality" in filters:
        filters["max_formality"] = int(filters["max_formality"])

    items = query_items(user_id=user_id, filters=filters)

    return {
        "items": items,
        "total_count": len(items),
        "filters_used": filters,
    }


def get_full_wardrobe(user_id: str = "default_user") -> dict:
    """Return every item in the wardrobe with no filters."""
    items = get_all_items(user_id=user_id)
    return {"items": items, "total_count": len(items)}


def summarise_wardrobe(user_id: str = "default_user") -> str:
    """
    Returns a human-readable summary of the wardrobe for use in the agent's
    system prompt context.
    """
    items = get_all_items(user_id=user_id)
    if not items:
        return "The wardrobe is empty."

    lines = [f"Wardrobe contains {len(items)} item(s):\n"]
    for item in items:
        seasons = ", ".join(item.get("season") or [])
        lines.append(
            f"  [{item['item_id']}] {item['color']} {item['subtype']} "
            f"(category={item['category']}, formality={item['formality']}, "
            f"rain_suitable={item['rain_suitable']}, status={item['status']}, "
            f"seasons={seasons})"
        )
    return "\n".join(lines)
