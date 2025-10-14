from pydantic import BaseModel
from typing import Literal, Optional

from src.travian_strategy.game_engine.data_models.resource_field_model import ResourceType


class ActionModel(BaseModel):
    """Model representing an action taken in the game."""
    type: Literal["build", "upgrade"]
    position: int

class BuildBuildingAction(ActionModel):
    building_id: str
    target_level: int

class UpgradeBuildingAction(ActionModel):
    building_id: str
    target_level: int

class BuildResourceField(ActionModel):
    field_type: ResourceType
    target_level: int

class UpgradeResourceField(ActionModel):
    field_type: ResourceType
    target_level: int