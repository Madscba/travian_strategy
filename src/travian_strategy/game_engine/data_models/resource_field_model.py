
from enum import Enum
from pydantic import BaseModel, Field, computed_field

class ResourceType(str, Enum):
    """Enumeration of resource types in Travian."""
    WOOD = "wood"
    CLAY = "clay"
    IRON = "iron"
    CROP = "crop"


class ResourceField(BaseModel):
    """Model representing a resource field in a village."""

    field_type: ResourceType = Field(description="Type of resource field")
    level: int = Field(ge=0, le=10, description="Field level (0-10)")
    position: int = Field(ge=1, le=18, description="Field position in village (1-18)")
    culture_points_per_hour: int = Field(0, ge=0, description="Culture points produced per hour by this field")
    
    @computed_field
    @property
    def base_production_per_hour(self) -> int:
        """Calculate base production per hour for this field level."""
        if self.level == 0:
            return 0

        # Travian base production formula: base * level * multiplier
        # Base production varies by resource type
        base_rates = {
            ResourceType.WOOD: 30,
            ResourceType.CLAY: 30,
            ResourceType.IRON: 30,
            ResourceType.CROP: 30
        }

        base = base_rates[self.field_type]
        # Production increases with level using Travian's formula
        return int(base * self.level * (1.5 ** (self.level - 1)))