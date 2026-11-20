"""
Helper validation and formatting utilities.
"""
from typing import Dict, Any


def validate_item_payload(item: Dict[str, Any]) -> bool:
    """Verifies that an item dictionary has required valid fields."""
    if not isinstance(item, dict):
        return False
    if "price" not in item or "quantity" not in item:
        return False
    return item["price"] >= 0 and item["quantity"] > 0