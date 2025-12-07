from src.travian_strategy.data_pipeline.data_models import BuildingData, BuildingDataCollection, BuildingLevel, \
    ResourceCosts, BuildingEffects
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

        all_building_info_dict = {}

        buildings = []
        for building_id in df['building_id'].unique():
            df_building = df[df['building_id'] == building_id].sort_values(by='level')
            building_levels = df_building.apply(self.constructing_level_from_row, axis=1).tolist()
            bd_temp = BuildingData(building_levels)
            all_building_info_dict[building_id] = bd_temp

        return all_building_info_dict

    def constructing_level_from_row(self, row):
        res_req = ResourceCosts(
            wood=row['wood'],
            clay=row['clay'],
            iron=row['iron'],
            crop=row['crop']
        )
        building_effect = BuildingEffects(
            production_bonus={
                'wood': row['prod_bonus_wood'],
                'clay': row['prod_bonus_clay'],
                'iron': row['prod_bonus_iron'],
                'crop': row['prod_bonus_crop']
            },
            storage_capacity=row['storage_capacity'],
            population_bonus=row['population_bonus'],
            training_time_reduction=row['training_time_reduction'],
            build_time_reduction=row['build_time_reduction'],
            build_cost_reduction=row['build_cost_reduction'],
            offensive_bonus=row['offensive_bonus'],
            defensive_bonus=row['defensive_bonus'],
            merchant_capacity=row['merchant_capacity'],
            culture_points_bonus=row['culture_points_bonus'],
            other_effects={}  # Placeholder for any additional effects
        )
        return BuildingLevel(
            level= row['level'],
            resource_cost= res_req,
            build_time= row['build_time'],
            population= row['population'],
            culture_points= row['culture_points'],
            effects= building_effect
        )

    def main(self):
        self.construct_buildings_from_data()

if __name__ == "__main__":
    village = create_village_from_type("4-4-4-6")
    engine = GameEngine(village=village, server_speed=1)
    engine.main()
    print(engine.get_current_state())
    print(engine.get_valid_actions())