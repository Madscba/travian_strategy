from pydantic import BaseModel, Field, field_validator, computed_field
import re

class VillageBuilding(BaseModel):
    """Model representing a building instance in a village."""

    building_id: str = Field(description="Building identifier (e.g., 'g15', 'g19')")
    building_name: str = Field(description="Human-readable building name")
    level: int = Field(ge=0, le=25, description="Current building level (0-25)")
    position: int = Field(ge=19, le=40, description="Building position in village (19-40)")
    singleton: bool = Field(
        default=False,
        description="Whether this building is a singleton (only one allowed per village)",
    )
    

    @field_validator('building_id')
    @classmethod
    def validate_building_id(cls, v: str) -> str:
        """Validate building ID format."""
        if not re.match(r'^g\d+$', v):
            raise ValueError(f"Invalid building ID format: {v}")
        return v



