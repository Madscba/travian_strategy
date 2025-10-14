"""
Data models for Travian building data structures.

This module contains Pydantic models used to represent and validate building data
extracted from the Travian knowledge base.
"""

from typing import Any, Optional

from pydantic import BaseModel, Field


class ResourceCosts(BaseModel):
    """Model representing the resource costs for building a level."""

    wood: int = Field(ge=0, description="Wood resource cost")
    clay: int = Field(ge=0, description="Clay resource cost")
    iron: int = Field(ge=0, description="Iron resource cost")
    crop: int = Field(ge=0, description="Crop resource cost")

    @property
    def total(self) -> int:
        """Calculate total resource cost."""
        return self.wood + self.clay + self.iron + self.crop


class BuildingEffects(BaseModel):
    """Model representing building effects and bonuses."""

    production_bonus: Optional[dict[str, float]] = Field(
        default=None, description="Resource production bonuses (percentage)"
    )
    storage_capacity: Optional[int] = Field(
        default=None, description="Storage capacity increase (absolute value)"
    )
    population_bonus: Optional[int] = Field(
        default=None, description="Population bonus (absolute value)"
    )
    training_time_reduction: Optional[float] = Field(
        default=None, description="Training time reduction percentage"
    )
    build_time_reduction: Optional[float] = Field(
        default=None, description="Building construction time reduction percentage"
    )
    build_cost_reduction: Optional[float] = Field(
        default=None, description="Building cost reduction percentage"
    )
    offensive_bonus: Optional[float] = Field(
        default=None, description="Offensive strength bonus percentage"
    )
    defensive_bonus: Optional[float] = Field(
        default=None, description="Defensive strength bonus percentage"
    )
    merchant_capacity: Optional[int] = Field(
        default=None, description="Merchant carrying capacity increase"
    )
    culture_points_bonus: Optional[float] = Field(
        default=None, description="Culture points production bonus percentage"
    )
    other_effects: dict[str, Any] = Field(
        default_factory=dict, description="Other building effects not covered by specific fields"
    )

    @property
    def has_effects(self) -> bool:
        """Check if this building level has any effects."""
        return any([
            self.production_bonus,
            self.storage_capacity is not None,
            self.population_bonus is not None,
            self.training_time_reduction is not None,
            self.build_time_reduction is not None,
            self.build_cost_reduction is not None,
            self.offensive_bonus is not None,
            self.defensive_bonus is not None,
            self.merchant_capacity is not None,
            self.culture_points_bonus is not None,
            bool(self.other_effects)
        ])

    def get_effect_summary(self) -> dict[str, Any]:
        """Get a summary of all effects for this building level."""
        summary = {}

        if self.production_bonus:
            summary["production_bonus"] = self.production_bonus
        if self.storage_capacity is not None:
            summary["storage_capacity"] = self.storage_capacity
        if self.population_bonus is not None:
            summary["population_bonus"] = self.population_bonus
        if self.training_time_reduction is not None:
            summary["training_time_reduction"] = self.training_time_reduction
        if self.build_time_reduction is not None:
            summary["build_time_reduction"] = self.build_time_reduction
        if self.build_cost_reduction is not None:
            summary["build_cost_reduction"] = self.build_cost_reduction
        if self.offensive_bonus is not None:
            summary["offensive_bonus"] = self.offensive_bonus
        if self.defensive_bonus is not None:
            summary["defensive_bonus"] = self.defensive_bonus
        if self.merchant_capacity is not None:
            summary["merchant_capacity"] = self.merchant_capacity
        if self.culture_points_bonus is not None:
            summary["culture_points_bonus"] = self.culture_points_bonus
        if self.other_effects:
            summary["other_effects"] = self.other_effects

        return summary


class BuildingLevel(BaseModel):
    """Model representing a single building level with all its properties."""

    level: int = Field(ge=1, le=100, description="Building level (1-100)")
    resource_cost: ResourceCosts = Field(description="Resources required to build this level")
    build_time: int = Field(ge=0, description="Build time in seconds")
    population: int = Field(ge=0, description="Population required")
    culture_points: int = Field(ge=0, description="Culture points gained")
    effects: Optional[BuildingEffects] = Field(
        default=None, description="Building effects at this level"
    )


class BuildingData(BaseModel):
    """Model representing complete building data with all levels."""

    building_name: str = Field(description="Name of the building")
    building_id: str = Field(description="Building identifier (e.g., 'g15')")
    category: str = Field(description="Building category (Resources, Infrastructure, Military)")
    max_level: int = Field(ge=1, le=25, description="Maximum building level")
    levels: list[BuildingLevel] = Field(description="List of all building levels")

