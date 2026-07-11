"""Total Battle Brothers — rdzeń logiki gry (bez prezentacji).

Ten pakiet zawiera czystą, testowalną logikę gry (strategia + bitwa).
Nie importuj tu bibliotek prezentacji/UI — patrz docs/ARCHITECTURE.md.
"""

from tbb.building import Building, FARM, MARKET, SMITH
from tbb.hex import Hex
from tbb.rng import Rng
from tbb.resources import Resources
from tbb.settlement import Settlement
from tbb.unit import Unit

__version__ = "0.0.1"

__all__ = [
    "Building",
    "FARM",
    "Hex",
    "Resources",
    "Rng",
    "Settlement",
    "Unit",
    "MARKET",
    "SMITH",
    "__version__",
]
