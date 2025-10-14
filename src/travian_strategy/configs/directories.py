from dataclasses import dataclass
from pathlib import Path

from src import travian_strategy


@dataclass
class Directories:
    """Class with all paths used in the repository."""
    MODULE_PATH = Path(travian_strategy.__file__).parent
    REPOSITORY_PATH = Path(travian_strategy.__file__).parent.parent
    DATA_FOLDER = MODULE_PATH / "data"
