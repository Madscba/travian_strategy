from src.travian_strategy.game_engine.data_models.village_model import Village
from src.travian_strategy.configs.data_sources import DataSources
import pandas as pd

from src.travian_strategy.game_engine.village_factory import create_village_from_type


class GameEngine:
    village: Village
    server_speed: int
    building_data: dict

    def __init__(self, village: Village, server_speed: int = 1):
        self.village = village
        self.server_speed = server_speed
        self.building_data = self.construct_buildings_from_data()

    def get_current_state(self) -> dict:
        "resource production, building levels, troop counts, etc."
        return {
            "village": self.village
        }
    
    def get_valid_actions(self) -> list:
        "list of possible actions the player can take"
        return self.village.get_valid_actions()

    def construct_buildings_from_data(self):
        buildings_data_path = DataSources().BUILDINGS_DATA
        df = pd.read_csv(buildings_data_path)


        buildings = []
        for _, row in df.iterrows():

            buildings.append(row.to_dict())
    
    def main(self):
        self.construct_buildings_from_data()

if __name__ == "__main__":
    village = create_village_from_type("4-4-4-6")
    engine = GameEngine(village=village, server_speed=1)
    engine.main()
    print(engine.get_current_state())
    print(engine.get_valid_actions())