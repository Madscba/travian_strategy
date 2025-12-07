from src.travian_strategy.configs.directories import Directories
from dataclasses import dataclass

@dataclass
class DataSources:
    """Class to manage data sources for the game engine."""
    DATAPATH = Directories().DATA_FOLDER
    BUILDINGS_DATA = DATAPATH / "building_resource_costs_old.csv"
    TASK_REWARDS = DATAPATH / "task_rewards.xlsx"


