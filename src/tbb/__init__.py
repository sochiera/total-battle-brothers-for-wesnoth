"""Total Battle Brothers — rdzeń logiki gry (bez prezentacji).

Ten pakiet zawiera czystą, testowalną logikę gry (strategia + bitwa).
Nie importuj tu bibliotek prezentacji/UI — patrz docs/ARCHITECTURE.md.
"""

from tbb.building import Building, FARM, MARKET, SMITH
from tbb.battlefield import Battlefield
from tbb.battle import BattleSide, HexBattle
from tbb.combat import melee_hit_chance
from tbb.hex import Hex
from tbb.progression import investment_for_level, pillar_level
from tbb.rng import Rng
from tbb.resources import Resources
from tbb.settlement import Settlement
from tbb.terrain import FOREST, HILLS, PLAINS, Terrain
from tbb.unit import Unit

__version__ = "0.0.1"

__all__ = [
    "Building",
    "Battlefield",
    "BattleSide",
    "FARM",
    "FOREST",
    "Hex",
    "HexBattle",
    "HILLS",
    "investment_for_level",
    "melee_hit_chance",
    "Resources",
    "Rng",
    "Settlement",
    "Unit",
    "MARKET",
    "pillar_level",
    "PLAINS",
    "SMITH",
    "Terrain",
    "__version__",
]
