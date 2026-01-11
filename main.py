from src.travian_strategy.game_engine.village_factory import create_village_from_type
from src.travian_strategy.game_engine.game_engine import GameEngine
from src.travian_strategy.configs.directories import Directories

if __name__ == "__main__":
   
    base_line_strategy = "https://www.reddit.com/r/travian/comments/v0uv35/settling_first_new_village_lets_make_a_general/"
    advanced_strategy = "https://docs.google.com/spreadsheets/d/1gJ7qLDjXCv4dHzJvbkDWBbSUJfoM1ouZzqDNwUdh7xE/edit?gid=1784539195#gid=1784539195"
    advanced_strategy_video = "https://www.youtube.com/watch?v=j-IT1O8HSBs"


    #task reward
    #"https://docs.google.com/spreadsheets/d/16u0A1Z7OJBX8yyf4gi4CusIhyjhHWt9xGgR2nrgfG-I/edit?gid=0#gid=0"

    village = create_village_from_type("4-4-4-6")
    engine = GameEngine(village=village, server_speed=1)
    engine.main()
    print(engine.get_current_state())
    actions = engine.get_valid_actions()
    [print(a) for a in actions]