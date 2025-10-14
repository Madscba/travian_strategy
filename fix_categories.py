#!/usr/bin/env python3
"""Fix building categories in the JSON file."""

import json

# Load the data
with open("data/buildings.json") as f:
    data = json.load(f)

# Define correct categories
resource_buildings = {"g1", "g2", "g3", "g4", "g5", "g6", "g7", "g8", "g9"}  # Production buildings
military_buildings = {"g13", "g14", "g16", "g19", "g20", "g21", "g22", "g29", "g30", "g31", "g32", "g33", "g37"}

# Update categories
for building_id, building_data in data["buildings"].items():
    if building_id in resource_buildings:
        building_data["category"] = "Resources"
    elif building_id in military_buildings:
        building_data["category"] = "Military"
    else:
        building_data["category"] = "Infrastructure"

# Save updated data
with open("data/buildings.json", "w") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print("Categories updated successfully")
