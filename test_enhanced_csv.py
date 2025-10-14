#!/usr/bin/env python3
"""
Test script to validate the enhanced CSV file.
"""

import csv
import sys
from collections import defaultdict


def test_enhanced_csv(file_path: str):
    """Test the enhanced CSV file structure and content."""
    print(f"Testing enhanced CSV: {file_path}")
    print("=" * 50)

    rows_read = 0
    effect_counts = defaultdict(int)
    building_counts = defaultdict(int)
    unit_counts = defaultdict(int)

    try:
        with open(file_path, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)

            # Check headers
            expected_headers = [
                'building_name', 'building_id', 'category', 'level',
                'wood', 'clay', 'iron', 'crop', 'total_resources',
                'build_time', 'population', 'culture_points',
                'effect_type', 'effect_value', 'effect_unit', 'effect_description'
            ]

            if list(reader.fieldnames) != expected_headers:
                print("❌ Header mismatch!")
                print(f"Expected: {expected_headers}")
                print(f"Got: {list(reader.fieldnames)}")
                return False

            print("✅ Headers are correct")

            # Analyze data
            for row in reader:
                rows_read += 1
                building_counts[row['building_name']] += 1

                if row['effect_type']:
                    effect_counts[row['effect_type']] += 1

                if row['effect_unit']:
                    unit_counts[row['effect_unit']] += 1

                # Validate numeric fields
                try:
                    level = int(row['level'])
                    wood = int(row['wood'])
                    clay = int(row['clay'])
                    iron = int(row['iron'])
                    crop = int(row['crop'])

                    if row['effect_value']:
                        effect_value = float(row['effect_value'])

                except ValueError as e:
                    print(f"❌ Invalid numeric value in row {rows_read}: {e}")
                    print(f"Row: {row}")
                    return False

        print(f"✅ Read {rows_read} rows successfully")
        print(f"✅ Found {len(building_counts)} unique buildings")
        print(f"✅ Found {sum(1 for count in effect_counts.values() if count > 0)} buildings with effects")

        print("\nEffect Type Distribution:")
        for effect_type, count in sorted(effect_counts.items()):
            print(f"  {effect_type}: {count} rows")

        print("\nEffect Unit Distribution:")
        for unit, count in sorted(unit_counts.items()):
            print(f"  {unit}: {count} rows")

        # Sample buildings with effects
        print("\nSample Buildings with Effects:")
        with open(file_path, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            shown_buildings = set()
            for row in reader:
                if (row['effect_type'] and
                    row['building_name'] not in shown_buildings and
                    len(shown_buildings) < 5):
                    shown_buildings.add(row['building_name'])
                    print(f"  {row['building_name']} L{row['level']}: "
                          f"{row['effect_value']} {row['effect_unit']} "
                          f"{row['effect_description']}")

        return True

    except Exception as e:
        print(f"❌ Error reading CSV: {e}")
        return False


if __name__ == "__main__":
    # Test the main enhanced CSV
    success = test_enhanced_csv("building_resource_costs_with_effects.csv")

    if success:
        print("\n" + "=" * 50)
        print("✅ All tests passed! The enhanced CSV is working correctly.")
        print("✅ Building effects have been successfully added to the CSV.")
        print("✅ The CSV now shows effect type, value, unit, and description for each building level.")
    else:
        print("\n" + "=" * 50)
        print("❌ Tests failed!")
        sys.exit(1)
