#!/usr/bin/env python3
"""
Script to enhance the building_resource_costs.csv with building effects data.

This script reads the existing CSV and adds effect-related columns based on the
building effects mapping in the data pipeline module.
"""

import csv
import sys
from pathlib import Path
from typing import Dict, Optional, Tuple

# Add the src directory to the path to import the data pipeline modules
sys.path.insert(0, str(Path(__file__).parent / "src"))

from travian_strategy.data_pipeline.building_effects import (
    BUILDING_EFFECTS_MAPPING,
    EFFECT_ICON_MAPPING,
    EXAMPLE_BUILDING_EFFECTS,
    get_building_effects_info
)


# Building name to ID mapping based on the building_effects.py file
BUILDING_NAME_TO_ID = {
    # Resource buildings
    "Woodcutter": "g1",
    "Clay Pit": "g2",
    "Iron Mine": "g3",
    "Cropland": "g4",
    "Sawmill": "g5",
    "Brickyard": "g6",
    "Iron Foundry": "g7",
    "Grain Mill": "g8",
    "Bakery": "g9",

    # Infrastructure buildings
    "Warehouse": "g10",
    "Granary": "g11",
    "Main Building": "g15",
    "Marketplace": "g17",
    "Town Hall": "g24",
    "Residence": "g25",
    "Palace": "g26",
    "Treasury": "g27",
    "Trade Office": "g28",
    "Stonemason's Lodge": "g34",
    "Great Warehouse": "g38",
    "Great Granary": "g39",

    # Military buildings
    "Smithy": "g13",
    "Tournament Square": "g14",
    "Barracks": "g19",
    "Stable": "g20",
    "Workshop": "g21",
    "Academy": "g22",
    "Great Barracks": "g29",
    "Great Stable": "g30",
    "City Wall": "g31",
    "Earth Wall": "g32",
    "Palisade": "g33",
    "Hero's Mansion": "g37",

    # Additional buildings that might be in CSV but not in effects mapping
    "Rally Point": "g16",
    "Embassy": "g18",
    "Cranny": "g23",
    "Trapper": "g35",
    "Command Center": "g36",
    "Waterworks": "g40",
    "Hospital": "g41",
    "Asclepeion": "g42",
    "Brewery": "g43",
    "Harbor": "g44",
    "Wonder Of The World": "g45",
    "Horse Drinking Trough": "g46",

    # Wall types (additional)
    "Stone Wall": "g47",
    "Makeshift Wall": "g48",
    "Defensive Wall": "g49",
    "Barricade": "g50"
}


def calculate_effect_value(building_id: str, level: int) -> Tuple[Optional[str], Optional[float], Optional[str]]:
    """
    Calculate the effect value for a building at a specific level.

    Returns:
        Tuple of (effect_type, effect_value, effect_unit)
    """
    # Check if we have example data for this building
    if building_id in EXAMPLE_BUILDING_EFFECTS:
        example_data = EXAMPLE_BUILDING_EFFECTS[building_id]
        level_data = example_data.get("levels", {}).get(level)
        if level_data:
            # Return the first effect found in the level data
            for effect_type, value in level_data.items():
                unit = "percentage" if "bonus" in effect_type or "reduction" in effect_type else "absolute"
                return effect_type, value, unit

    # Use building effects mapping for general patterns
    building_info = get_building_effects_info(building_id)
    if not building_info:
        return None, None, None

    primary_effects = building_info.get("primary_effects", [])
    if not primary_effects:
        return None, None, None

    # Get the first primary effect
    primary_effect = primary_effects[0]

    # Handle different effect types with level-based calculations
    if primary_effect == "wood_production":
        return "resource_production", level * 30, "absolute"  # Base production + 30 per level
    elif primary_effect == "clay_production":
        return "resource_production", level * 30, "absolute"
    elif primary_effect == "iron_production":
        return "resource_production", level * 30, "absolute"
    elif primary_effect == "crop_production":
        return "resource_production", level * 30, "absolute"
    elif primary_effect == "icon-woodBonus":
        return "production_bonus", level * 5, "percentage"  # 5% per level
    elif primary_effect == "icon-clayBonus":
        return "production_bonus", level * 5, "percentage"
    elif primary_effect == "icon-ironBonus":
        return "production_bonus", level * 5, "percentage"
    elif primary_effect == "icon-cropBonus":
        return "production_bonus", level * 5, "percentage"
    elif primary_effect == "icon-warehouseCap":
        # Warehouse capacity - exponential growth
        base_capacity = 800
        return "storage_capacity", int(base_capacity * (1.2295 ** level)), "absolute"
    elif primary_effect == "icon-granaryCap":
        # Granary capacity - similar to warehouse
        base_capacity = 800
        return "storage_capacity", int(base_capacity * (1.2295 ** level)), "absolute"
    elif primary_effect == "icon-buildingTimeReduction":
        return "build_time_reduction", min(level * 0.5, 25), "percentage"  # Max 25%
    elif primary_effect == "icon-merchantCapacity":
        return "merchant_capacity", 500 + (level * 100), "absolute"
    elif primary_effect == "icon-culturePointsBonus":
        return "culture_points_bonus", level * 2, "percentage"
    elif primary_effect == "icon-populationBonus":
        return "population_bonus", level * 500, "absolute"
    elif primary_effect == "icon-buildingCostReduction":
        return "build_cost_reduction", min(level * 1, 15), "percentage"  # Max 15%
    elif primary_effect == "icon-fasterUpgrade":
        return "upgrade_speed_bonus", level * 3, "percentage"
    elif primary_effect == "icon-infantryBonusTime":
        return "training_time_reduction", min(level * 2, 50), "percentage"  # Max 50%
    elif primary_effect == "icon-cavalryBonusTime":
        return "training_time_reduction", min(level * 2, 50), "percentage"
    elif primary_effect == "icon-siegeBonusTime":
        return "training_time_reduction", min(level * 2, 50), "percentage"
    elif primary_effect == "icon-defensiveStrength":
        return "defensive_bonus", level * 5, "percentage"
    elif primary_effect == "icon-offensiveStrength":
        return "offensive_bonus", level * 3, "percentage"

    return None, None, None


def get_effect_description(effect_type: str, building_name: str) -> str:
    """Get a human-readable description of the effect."""
    descriptions = {
        "resource_production": f"{building_name} resource production",
        "production_bonus": f"{building_name.split()[-1].lower()} production bonus",
        "storage_capacity": f"{building_name.lower()} storage capacity",
        "build_time_reduction": "Building construction time reduction",
        "merchant_capacity": "Merchant carrying capacity",
        "culture_points_bonus": "Culture points production bonus",
        "population_bonus": "Population capacity bonus",
        "build_cost_reduction": "Building cost reduction",
        "upgrade_speed_bonus": "Upgrade speed bonus",
        "training_time_reduction": "Training time reduction",
        "defensive_bonus": "Defensive strength bonus",
        "offensive_bonus": "Offensive strength bonus"
    }
    return descriptions.get(effect_type, f"{effect_type.replace('_', ' ').title()}")


def enhance_csv_with_effects(input_file: str, output_file: str):
    """
    Enhance the CSV file with building effects data.
    """
    rows_processed = 0
    rows_with_effects = 0

    with open(input_file, 'r', newline='', encoding='utf-8') as infile, \
         open(output_file, 'w', newline='', encoding='utf-8') as outfile:

        reader = csv.DictReader(infile)

        # Create new fieldnames with effect columns
        fieldnames = list(reader.fieldnames) + [
            'effect_type', 'effect_value', 'effect_unit', 'effect_description'
        ]

        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()

        for row in reader:
            building_name = row['building_name']
            level = int(row['level'])

            # Fix building_id using the mapping
            correct_building_id = BUILDING_NAME_TO_ID.get(building_name)
            if correct_building_id:
                row['building_id'] = correct_building_id

            # Calculate effects
            effect_type, effect_value, effect_unit = calculate_effect_value(
                row['building_id'], level
            )

            # Add effect data to row
            row['effect_type'] = effect_type or ""
            row['effect_value'] = effect_value if effect_value is not None else ""
            row['effect_unit'] = effect_unit or ""
            row['effect_description'] = get_effect_description(effect_type, building_name) if effect_type else ""

            writer.writerow(row)
            rows_processed += 1

            if effect_type:
                rows_with_effects += 1

    print(f"Enhanced CSV created: {output_file}")
    print(f"Rows processed: {rows_processed}")
    print(f"Rows with effects: {rows_with_effects}")
    print(f"Coverage: {rows_with_effects/rows_processed*100:.1f}%")


if __name__ == "__main__":
    input_csv = "building_resource_costs.csv"
    output_csv = "building_resource_costs_with_effects.csv"

    enhance_csv_with_effects(input_csv, output_csv)

    # Also create the enhanced version in the data pipeline directory
    data_pipeline_input = "src/travian_strategy/data_pipeline/building_resource_costs.csv"
    data_pipeline_output = "src/travian_strategy/data_pipeline/building_resource_costs_with_effects.csv"

    if Path(data_pipeline_input).exists():
        enhance_csv_with_effects(data_pipeline_input, data_pipeline_output)