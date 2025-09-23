#!/usr/bin/env python3
"""
Convert CSV building data with effects to a single consolidated JSON file.
"""

import csv
import json
from collections import defaultdict
from pathlib import Path


def convert_csv_to_json(csv_file: str, output_file: str):
    """Convert the enhanced CSV to consolidated JSON format."""
    buildings = {}

    with open(csv_file, 'r', newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)

        for row in reader:
            building_id = row['building_id']

            # Initialize building if not exists
            if building_id not in buildings:
                buildings[building_id] = {
                    'name': row['building_name'],
                    'category': row['category'],
                    'effect_type': row['effect_type'] or None,
                    'effect_unit': row['effect_unit'] or None,
                    'effect_description': row['effect_description'] or None,
                    'levels': []
                }

            # Add level data
            level_data = {
                'level': int(row['level']),
                'wood': int(row['wood']),
                'clay': int(row['clay']),
                'iron': int(row['iron']),
                'crop': int(row['crop']),
                'total_resources': int(row['total_resources']),
                'build_time': int(row['build_time']),
                'population': int(row['population']),
                'culture_points': int(row['culture_points'])
            }

            # Add effect value if present
            if row['effect_value']:
                try:
                    level_data['effect_value'] = float(row['effect_value'])
                except ValueError:
                    level_data['effect_value'] = row['effect_value']

            buildings[building_id]['levels'].append(level_data)

    # Sort levels within each building
    for building in buildings.values():
        building['levels'].sort(key=lambda x: x['level'])

    # Create final structure
    data = {
        'version': '1.0',
        'description': 'Travian building data with costs and effects',
        'buildings': buildings
    }

    # Write to JSON file
    with open(output_file, 'w', encoding='utf-8') as jsonfile:
        json.dump(data, jsonfile, indent=2, ensure_ascii=False)

    # Print summary
    total_buildings = len(buildings)
    buildings_with_effects = sum(1 for b in buildings.values() if b['effect_type'])
    total_levels = sum(len(b['levels']) for b in buildings.values())

    print(f"Conversion completed:")
    print(f"- Total buildings: {total_buildings}")
    print(f"- Buildings with effects: {buildings_with_effects}")
    print(f"- Total building levels: {total_levels}")
    print(f"- Output file: {output_file}")


if __name__ == "__main__":
    # Convert the enhanced CSV to JSON
    convert_csv_to_json(
        "building_resource_costs_with_effects.csv",
        "data/buildings.json"
    )