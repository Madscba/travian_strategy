"""
Travian village simulation data models.

This module contains Pydantic models for representing village state in Travian simulations,
including resource fields, buildings, and overall village configuration.
"""

import re
from datetime import datetime
from enum import Enum
from typing import Optional, List

from pydantic import BaseModel, Field, computed_field, field_validator

from src.travian_strategy.game_engine.data_models.action_model import ActionModel, BuildBuildingAction, UpgradeBuildingAction, BuildResourceField, UpgradeResourceField
from src.travian_strategy.game_engine.data_models.resource_field_model import ResourceField, ResourceType
from src.travian_strategy.game_engine.data_models.building_model import VillageBuilding



class Village(BaseModel):
    """Model representing a complete Travian village for simulation."""

    village_type: str = Field(description="Village type (e.g., '4-4-4-6', '3-3-3-9')")
    capital: bool = Field(False, description="Is this village the capital?")
    resource_fields: list[ResourceField] = Field(
        description="List of 18 resource fields",
        min_length=18,
        max_length=18
    )
    buildings: list[VillageBuilding] = Field(
        default_factory=list,
        description="List of buildings in the village"
    )
    troops: dict = Field(
        default_factory=dict,
        description="Troops stationed in village (placeholder for future use)"
    )
    start_time : datetime = Field(default_factory=datetime.now, description="Simulation start date and time")
    seconds_since_creation: int = Field(default=0, description="Village creation date and time")
    current_resources: dict[str, int] = Field(
        default_factory=lambda: {"wood": 0, "clay": 0, "iron": 0, "crop": 0},
        description="Current resources in the village"
    )
    resource_caps: dict[str, int] = Field(
        default_factory=lambda: {"wood": 800, "clay": 800, "iron": 800, "crop": 800},
        description="Resource storage capacities"
    )
    population: int = Field(0, description="Current population of the village")
    culture_points: int = Field(0, description="Total culture points of the village")


    @field_validator('village_type')
    @classmethod
    def validate_village_type(cls, v: str) -> str:
        """Validate village type format."""
        pattern = r'^\d+-\d+-\d+-\d+$'
        if not re.match(pattern, v):
            raise ValueError(f"Invalid village type format: {v}. Expected format like '4-4-4-6'")

        # Parse and validate the numbers
        parts = [int(x) for x in v.split('-')]
        if len(parts) != 4:
            raise ValueError(f"Village type must have 4 numbers: {v}")

        if sum(parts) != 18:
            raise ValueError(f"Village type numbers must sum to 18: {v}")

        # Each resource type must have at least 1 field
        if any(x < 1 for x in parts):
            raise ValueError(f"Each resource type must have at least 1 field: {v}")

        return v

    @field_validator('resource_fields')
    @classmethod
    def validate_resource_fields(cls, v: list[ResourceField]) -> list[ResourceField]:
        """Validate resource fields configuration."""
        if len(v) != 18:
            raise ValueError(f"Village must have exactly 18 resource fields, got {len(v)}")

        # Check that positions are unique and cover 1-18
        positions = [field.position for field in v]
        if set(positions) != set(range(1, 19)):
            raise ValueError("Resource field positions must be unique and cover 1-18")

        return v

    @computed_field
    @property
    def culture_points_per_hour(self) -> int:
        """Calculate total culture points production per hour."""
        total = 0
        for building in self.buildings:
            total += building.culture_points_per_hour
        return total

    @computed_field
    @property
    def resource_production_per_hour(self) -> dict[str, int]:
        """Calculate total resource production per hour."""
        production = {
            ResourceType.WOOD: 0,
            ResourceType.CLAY: 0,
            ResourceType.IRON: 0,
            ResourceType.CROP: 0
        }

        # Add base production from fields
        for field in self.resource_fields:
            production[field.field_type] += field.base_production_per_hour

        # TODO: Add building bonuses from BuildingEffects
        # This would require integration with the existing BuildingData models

        return {k.value: v for k, v in production.items()}

    def get_village_type_breakdown(self) -> dict[str, int]:
        """Get breakdown of resource field types matching village_type."""
        breakdown = {
            ResourceType.WOOD: 0,
            ResourceType.CLAY: 0,
            ResourceType.IRON: 0,
            ResourceType.CROP: 0
        }

        for field in self.resource_fields:
            breakdown[field.field_type] += 1

        return {k.value: v for k, v in breakdown.items()}

    def add_building(self, building_id: str, building_name: str, level: int, position: int) -> None:
        """Add a building to the village."""
        # Check if position is already occupied
        occupied_positions = [b.position for b in self.buildings]
        if position in occupied_positions:
            raise ValueError(f"Position {position} is already occupied")

        # Validate position is in building area (19-40)
        if not (19 <= position <= 40):
            raise ValueError(f"Building position must be between 19-40, got {position}")

        building = VillageBuilding(
            building_id=building_id,
            building_name=building_name,
            level=level,
            position=position
        )
        self.buildings.append(building)

    def get_building_by_position(self, position: int) -> Optional[VillageBuilding]:
        """Get building at specific position."""
        for building in self.buildings:
            if building.position == position:
                return building
        return None

    def get_building_by_id(self, building_id: str) -> Optional[VillageBuilding]:
        """Get first building with specific building_id."""
        for building in self.buildings:
            if building.building_id == building_id:
                return building
        return None

    def get_valid_actions(self) -> List[ActionModel]:

        """List of possible actions the player can take"""
        actions = []

        # Example actions based on current village state
        # 1. Upgrade resource fields if not at max level
        for field in self.resource_fields:
            max_resource_level = 10 if not self.capital else 20
            if field.level == 0:
                actions.append(BuildResourceField(
                    type='build',
                    position=field.position,
                    field_type=field.field_type,
                    target_level=field.level+1,
                ))

            elif field.level < max_resource_level:
                actions.append(UpgradeResourceField(
                    type='upgrade',
                    position=field.position,
                    field_type=field.field_type,
                    target_level=field.level+1,
                ))


        # 2. Build new buildings if there are free slots
        occupied_positions = [b.position for b in self.buildings]

        for pos in range(19, 41):
            if pos not in occupied_positions:
                #actions.append(f"Build new building at position {pos}")
                actions.append(BuildBuildingAction(
                    type='build',
                    position=pos,
                    building_id='Empty',
                    target_level=1)
                )

        # 3. Upgrade existing buildings if not at max level
        for building in self.buildings:
            if building.level < 25:
                actions.append(f"Upgrade {building.building_name} (ID: {building.building_id}) at position {building.position} from level {building.level} to {building.level + 1}")

        return actions
