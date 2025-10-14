from datetime import datetime
from typing import Dict, List
from src.travian_strategy.game_engine.data_models.building_model import VillageBuilding

class BuildingConstruction:
    building_position: int
    target_level: int
    completion_time: datetime
    resource_cost: Dict[str, int]

class GameState:
    current_time: datetime
    village_resources: Dict[str, int]
    hero_resources: Dict[str, int]
    resource_production_per_hour: Dict[str, int]
    buildings: List[VillageBuilding]
    constructions_in_progress: List[BuildingConstruction]

    def advance_to_next_event(self) -> 'GameState':
        #order events
        #retrieve and pop event from queue
        pass
        



        
    def advance_time_to(self, building_time: datetime) -> 'GameState':
        """Create new state with time advanced and resources/buildings updated."""
        self.current_time += building_time
        
       