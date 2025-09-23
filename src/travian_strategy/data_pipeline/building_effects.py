"""
Building effects mapping for Travian buildings.

This module contains mappings between building IDs and their specific effects,
as well as functions to parse and interpret building effect values from HTML content.
"""

import logging
import re
from typing import Any, Dict, Optional, Union

from src.travian_strategy.data_pipeline.static import EFFECT_ICON_MAPPING, BUILDING_EFFECTS_MAPPING

logger = logging.getLogger(__name__)


def parse_effect_value(effect_text: str, effect_type: str) -> Union[int, float, None]:
    """
    Parse effect value from text content based on effect type.

    Args:
        effect_text: Raw text content from HTML (e.g., "+25%", "1,200", "90.0%")
        effect_type: Type of effect to determine parsing strategy

    Returns:
        Parsed numeric value or None if parsing fails
    """
    if not effect_text:
        return None

    # Clean the text
    clean_text = effect_text.strip()

    try:
        # Handle percentage values
        if "%" in clean_text:
            # Extract numeric part (handles +25%, 90.0%, etc.)
            percent_match = re.search(r'([+-]?\d+(?:\.\d+)?)', clean_text)
            if percent_match:
                value = float(percent_match.group(1))
                # For training time reduction, values like "90.0%" mean 90% of original time (10% reduction)
                if effect_type == "training_time_reduction":
                    return 100 - value  # Convert to reduction percentage
                return value

        # Handle absolute numeric values (with potential commas)
        elif effect_type in ["storage_capacity", "population_bonus", "merchant_capacity"]:
            # Remove commas and extract numbers
            numeric_match = re.sub(r'[^\d]', '', clean_text)
            if numeric_match:
                return int(numeric_match)

        # Handle other numeric values
        else:
            numeric_match = re.search(r'([+-]?\d+(?:\.\d+)?)', clean_text)
            if numeric_match:
                return float(numeric_match.group(1))

    except (ValueError, AttributeError) as e:
        logger.warning(f"Failed to parse effect value '{effect_text}' for type '{effect_type}': {e}")

    return None


def get_building_effects_info(building_id: str) -> Optional[Dict[str, Any]]:
    """
    Get effect information for a specific building ID.

    Args:
        building_id: Building identifier (e.g., 'g9', 'g19')

    Returns:
        Dictionary containing building effects info or None if not found
    """
    return BUILDING_EFFECTS_MAPPING.get(building_id)


def get_effect_type_from_icon(icon_class: str) -> Optional[Dict[str, Any]]:
    """
    Get effect type information from icon class.

    Args:
        icon_class: CSS class name of the effect icon

    Returns:
        Dictionary containing effect type info or None if not found
    """
    return EFFECT_ICON_MAPPING.get(icon_class)


def categorize_effect_by_icon(icon_classes: list[str]) -> Optional[str]:
    """
    Determine effect category from a list of icon classes.

    Args:
        icon_classes: List of CSS class names

    Returns:
        Effect type string or None if no known effect found
    """
    for icon_class in icon_classes:
        if icon_class in EFFECT_ICON_MAPPING:
            return EFFECT_ICON_MAPPING[icon_class]["type"]
    return None


def create_effect_summary(building_id: str, effects_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create a summary of building effects for a specific building.

    Args:
        building_id: Building identifier
        effects_data: Raw effects data extracted from HTML

    Returns:
        Structured effects summary
    """
    building_info = get_building_effects_info(building_id)

    summary = {
        "building_id": building_id,
        "category": building_info.get("category", "Unknown") if building_info else "Unknown",
        "effects": {}
    }

    # Process each effect found in the HTML data
    for effect_key, effect_value in effects_data.items():
        if effect_key.startswith("f"):  # Effect grid areas (f0, f1, f2, etc.)
            effect_info = effects_data.get(f"{effect_key}_info", {})
            effect_type = effect_info.get("type")

            if effect_type and effect_value is not None:
                summary["effects"][effect_type] = {
                    "value": effect_value,
                    "unit": effect_info.get("unit", "unknown"),
                    "description": effect_info.get("description", ""),
                    "category": effect_info.get("category", "unknown")
                }

    return summary

