"""Total Battle Brothers — rdzeń logiki gry (bez prezentacji).

Ten pakiet zawiera czystą, testowalną logikę gry (strategia + bitwa).
Nie importuj tu bibliotek prezentacji/UI — patrz docs/ARCHITECTURE.md.
"""

from tbb.rng import Rng

__version__ = "0.0.1"

__all__ = ["Rng", "__version__"]
