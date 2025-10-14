"""
Factory functions for creating Travian villages.

This module provides convenient functions to create village instances
from standard configurations and village type strings.
"""

from typing import Optional

from src.travian_strategy.game_engine.data_models.village_model import Village
from src.travian_strategy.game_engine.data_models.building_model import VillageBuilding
from src.travian_strategy.game_engine.data_models.resource_field_model import  ResourceField, ResourceType



def parse_village_type(village_type: str) -> dict[str, int]:
    """
    Parse village type string into resource field counts.

    Args:
        village_type: String like "4-4-4-6" representing wood-clay-iron-crop counts

    Returns:
        Dictionary mapping resource types to field counts

    Raises:
        ValueError: If village type format is invalid
    """
    try:
        parts = [int(x) for x in village_type.split('-')]
        if len(parts) != 4:
            raise ValueError(f"Village type must have 4 numbers: {village_type}")

        if sum(parts) != 18:
            raise ValueError(f"Village type numbers must sum to 18: {village_type}")

        if any(x < 1 for x in parts):
            raise ValueError(f"Each resource type must have at least 1 field: {village_type}")

        return {
            ResourceType.WOOD.value: parts[0],
            ResourceType.CLAY.value: parts[1],
            ResourceType.IRON.value: parts[2],
            ResourceType.CROP.value: parts[3]
        }
    except (ValueError, IndexError) as e:
        raise ValueError(f"Invalid village type format: {village_type}") from e


def create_resource_fields(village_type: str) -> list[ResourceField]:
    """
    Create resource fields based on village type.

    Args:
        village_type: String like "4-4-4-6" representing field distribution

    Returns:
        List of 18 ResourceField objects in standard positions
    """
    field_counts = parse_village_type(village_type)
    fields = []
    position = 1

    # Create fields in order: wood, clay, iron, crop
    resource_order = [ResourceType.WOOD, ResourceType.CLAY, ResourceType.IRON, ResourceType.CROP]

    for resource_type in resource_order:
        count = field_counts[resource_type.value]
        for _ in range(count):
            fields.append(ResourceField(
                field_type=resource_type,
                level=0,  # Start at level 0
                position=position
            ))
            position += 1

    return fields


def create_default_buildings() -> list[VillageBuilding]:
    """
    Create default buildings that every village starts with.

    Returns:
        List of VillageBuilding objects for starter buildings
    """
    return [
        VillageBuilding(
            building_id="g15",
            building_name="Main Building",
            level=1,
            position=19  # Main building is always at position 19
        )
    ]


def create_village_from_type(village_type: str, village_name: str = "New Village") -> Village:
    """
    Create a village from a village type string.

    Args:
        village_type: String like "4-4-4-6" representing field distribution
        village_name: Optional name for the village

    Returns:
        Village instance with the specified configuration

    Examples:
        >>> village = create_village_from_type("4-4-4-6")
        >>> village.village_type
        "4-4-4-6"
        >>> len(village.resource_fields)
        18
        >>> village.get_village_type_breakdown()
        {'wood': 4, 'clay': 4, 'iron': 4, 'crop': 6}
    """
    resource_fields = create_resource_fields(village_type)
    buildings = create_default_buildings()


    return Village(
        village_type=village_type,
        resource_fields=resource_fields,
        buildings=buildings,
        troops={}
    )


def create_developed_village(
    village_type: str,
    field_levels: Optional[dict[int, int]] = None,
    additional_buildings: Optional[list[dict]] = None
) -> Village:
    """
    Create a more developed village with specified field levels and buildings.

    Args:
        village_type: String like "4-4-4-6" representing field distribution
        field_levels: Dict mapping field positions to levels
        additional_buildings: List of building dicts with keys: building_id, building_name, level, position

    Returns:
        Village instance with developed infrastructure

    Examples:
        >>> village = create_developed_village(
        ...     "4-4-4-6",
        ...     field_levels={1: 5, 2: 5, 15: 8, 16: 8},  # Develop some crop fields
        ...     additional_buildings=[
        ...         {"building_id": "g10", "building_name": "Warehouse", "level": 5, "position": 20},
        ...         {"building_id": "g11", "building_name": "Granary", "level": 5, "position": 21}
        ...     ]
        ... )
    """
    village = create_village_from_type(village_type)

    # Set field levels if provided
    if field_levels:
        for field in village.resource_fields:
            if field.position in field_levels:
                field.level = field_levels[field.position]

    # Add additional buildings if provided
    if additional_buildings:
        for building_data in additional_buildings:
            village.add_building(
                building_id=building_data["building_id"],
                building_name=building_data["building_name"],
                level=building_data["level"],
                position=building_data["position"]
            )

    return village


# Predefined village type configurations
STANDARD_VILLAGE_TYPES = {
    "start": "4-4-4-6",                # Starting Resource Layout
    "wood5_clay3_iron4_crop6": "5-3-4-6",
    "wood5_clay4_iron3_crop6": "5-4-3-6",
    "wood3_clay5_iron4_crop6": "3-5-4-6",
    "wood4_clay5_iron3_crop6": "4-5-3-6",
    "wood3_clay4_iron5_crop6": "3-4-5-6",
    "wood4_clay3_iron5_crop6": "4-3-5-6",
    "wood3_clay4_iron4_crop7": "3-4-4-7",  # Only on 3.5 and 4 edition
    "wood4_clay3_iron4_crop7": "4-3-4-7",  # Only on 3.5 and 4 edition
    "wood4_clay4_iron3_crop7": "4-4-3-7",  # Only on 3.5 and 4 edition
    "cropper9": "3-3-3-9",                 # 9-cropper
    "cropper15": "1-1-1-15",               # 15-cropper
}



def create_standard_village(village_preset: str) -> Village:
    """
    Create a village from a standard preset.

    Args:
        village_preset: One of the keys from STANDARD_VILLAGE_TYPES

    Returns:
        Village instance with the preset configuration

    Raises:
        ValueError: If preset is not recognized
    """
    if village_preset not in STANDARD_VILLAGE_TYPES:
        available = list(STANDARD_VILLAGE_TYPES.keys())
        raise ValueError(f"Unknown village preset: {village_preset}. Available: {available}")

    village_type = STANDARD_VILLAGE_TYPES[village_preset]
    return create_village_from_type(village_type)
