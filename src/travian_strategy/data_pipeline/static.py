EFFECT_ICON_MAPPING = {
    # Storage and capacity effects
    "icon-warehouseCap": {
        "type": "storage_capacity",
        "category": "storage",
        "unit": "absolute",
        "description": "Warehouse storage capacity"
    },
    "icon-granaryCap": {
        "type": "storage_capacity",
        "category": "storage",
        "unit": "absolute",
        "description": "Granary storage capacity"
    },

    # Resource production bonuses
    "icon-cropBonus": {
        "type": "production_bonus",
        "category": "production",
        "resource": "crop",
        "unit": "percentage",
        "description": "Crop production bonus"
    },
    "icon-woodBonus": {
        "type": "production_bonus",
        "category": "production",
        "resource": "wood",
        "unit": "percentage",
        "description": "Wood production bonus"
    },
    "icon-clayBonus": {
        "type": "production_bonus",
        "category": "production",
        "resource": "clay",
        "unit": "percentage",
        "description": "Clay production bonus"
    },
    "icon-ironBonus": {
        "type": "production_bonus",
        "category": "production",
        "resource": "iron",
        "unit": "percentage",
        "description": "Iron production bonus"
    },
    "icon-allResourcesBonus": {
        "type": "production_bonus",
        "category": "production",
        "resource": "all",
        "unit": "percentage",
        "description": "All resources production bonus"
    },

    # Military and training effects
    "icon-infantryBonusTime": {
        "type": "training_time_reduction",
        "category": "military",
        "unit": "percentage",
        "description": "Infantry training time reduction"
    },
    "icon-cavalryBonusTime": {
        "type": "training_time_reduction",
        "category": "military",
        "unit": "percentage",
        "description": "Cavalry training time reduction"
    },
    "icon-siegeBonusTime": {
        "type": "training_time_reduction",
        "category": "military",
        "unit": "percentage",
        "description": "Siege weapons training time reduction"
    },
    "icon-offensiveStrength": {
        "type": "offensive_bonus",
        "category": "military",
        "unit": "percentage",
        "description": "Offensive strength bonus"
    },
    "icon-defensiveStrength": {
        "type": "defensive_bonus",
        "category": "military",
        "unit": "percentage",
        "description": "Defensive strength bonus"
    },

    # Building and construction effects
    "icon-buildingTimeReduction": {
        "type": "build_time_reduction",
        "category": "construction",
        "unit": "percentage",
        "description": "Building construction time reduction"
    },
    "icon-buildingCostReduction": {
        "type": "build_cost_reduction",
        "category": "construction",
        "unit": "percentage",
        "description": "Building cost reduction"
    },

    # Population and capacity effects
    "icon-populationBonus": {
        "type": "population_bonus",
        "category": "population",
        "unit": "absolute",
        "description": "Population capacity bonus"
    },
    "icon-merchantCapacity": {
        "type": "merchant_capacity",
        "category": "trade",
        "unit": "absolute",
        "description": "Merchant carrying capacity"
    },

    # Special effects
    "icon-culturePointsBonus": {
        "type": "culture_points_bonus",
        "category": "special",
        "unit": "percentage",
        "description": "Culture points production bonus"
    },
    "icon-fasterUpgrade": {
        "type": "upgrade_speed_bonus",
        "category": "special",
        "unit": "percentage",
        "description": "Faster upgrade speed"
    },
}
BUILDING_EFFECTS_MAPPING = {
    # Resource buildings
    "g1": {"primary_effects": ["wood_production"], "category": "Resources"},  # Woodcutter
    "g2": {"primary_effects": ["clay_production"], "category": "Resources"},  # Clay Pit
    "g3": {"primary_effects": ["iron_production"], "category": "Resources"},  # Iron Mine
    "g4": {"primary_effects": ["crop_production"], "category": "Resources"},  # Cropland
    "g5": {"primary_effects": ["icon-woodBonus"], "category": "Resources"},  # Sawmill
    "g6": {"primary_effects": ["icon-clayBonus"], "category": "Resources"},  # Brickyard
    "g7": {"primary_effects": ["icon-ironBonus"], "category": "Resources"},  # Iron Foundry
    "g8": {"primary_effects": ["icon-cropBonus"], "category": "Resources"},  # Grain Mill
    "g9": {"primary_effects": ["icon-cropBonus"], "category": "Resources"},  # Bakery

    # Infrastructure buildings
    "g10": {"primary_effects": ["icon-warehouseCap"], "category": "Infrastructure"},  # Warehouse
    "g11": {"primary_effects": ["icon-granaryCap"], "category": "Infrastructure"},  # Granary
    "g15": {"primary_effects": ["icon-buildingTimeReduction"], "category": "Infrastructure"},  # Main Building
    "g17": {"primary_effects": ["icon-merchantCapacity"], "category": "Infrastructure"},  # Marketplace
    "g24": {"primary_effects": ["icon-culturePointsBonus"], "category": "Infrastructure"},  # Town Hall
    "g25": {"primary_effects": ["icon-populationBonus"], "category": "Infrastructure"},  # Residence
    "g26": {"primary_effects": ["icon-populationBonus"], "category": "Infrastructure"},  # Palace
    "g27": {"primary_effects": ["icon-culturePointsBonus"], "category": "Infrastructure"},  # Treasury
    "g28": {"primary_effects": ["icon-merchantCapacity"], "category": "Infrastructure"},  # Trade Office
    "g34": {"primary_effects": ["icon-buildingCostReduction"], "category": "Infrastructure"},  # Stonemason's Lodge
    "g38": {"primary_effects": ["icon-warehouseCap"], "category": "Infrastructure"},  # Great Warehouse
    "g39": {"primary_effects": ["icon-granaryCap"], "category": "Infrastructure"},  # Great Granary

    # Military buildings
    "g13": {"primary_effects": ["icon-fasterUpgrade"], "category": "Military"},  # Smithy
    "g14": {"primary_effects": ["icon-fasterUpgrade"], "category": "Military"},  # Tournament Square
    "g19": {"primary_effects": ["icon-infantryBonusTime"], "category": "Military"},  # Barracks
    "g20": {"primary_effects": ["icon-cavalryBonusTime"], "category": "Military"},  # Stable
    "g21": {"primary_effects": ["icon-siegeBonusTime"], "category": "Military"},  # Workshop
    "g22": {"primary_effects": ["icon-fasterUpgrade"], "category": "Military"},  # Academy
    "g29": {"primary_effects": ["icon-infantryBonusTime"], "category": "Military"},  # Great Barracks
    "g30": {"primary_effects": ["icon-cavalryBonusTime"], "category": "Military"},  # Great Stable
    "g31": {"primary_effects": ["icon-defensiveStrength"], "category": "Military"},  # City Wall
    "g32": {"primary_effects": ["icon-defensiveStrength"], "category": "Military"},  # Earth Wall
    "g33": {"primary_effects": ["icon-defensiveStrength"], "category": "Military"},  # Palisade
    "g37": {"primary_effects": ["icon-offensiveStrength"], "category": "Military"},  # Hero's Mansion
}
EXAMPLE_BUILDING_EFFECTS = {
    "g9": {  # Bakery
        "name": "Bakery",
        "levels": {
            1: {"crop_bonus": 5},
            2: {"crop_bonus": 10},
            3: {"crop_bonus": 15},
            4: {"crop_bonus": 20},
            5: {"crop_bonus": 25}
        }
    },
    "g19": {  # Barracks
        "name": "Barracks",
        "levels": {
            1: {"training_time_reduction": 0},
            2: {"training_time_reduction": 10},
            3: {"training_time_reduction": 19},
            4: {"training_time_reduction": 27.1},
            5: {"training_time_reduction": 34.4}
        }
    },
    "g10": {  # Warehouse
        "name": "Warehouse",
        "levels": {
            1: {"storage_capacity": 1200},
            2: {"storage_capacity": 1700},
            3: {"storage_capacity": 2300},
            4: {"storage_capacity": 3100},
            5: {"storage_capacity": 4000}
        }
    }
}
