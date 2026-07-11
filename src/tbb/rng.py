"""Deterministic random number generation for game logic."""

import random


class Rng:
    """Seeded random number generator isolated from Python's global state."""

    def __init__(self, seed: int) -> None:
        self._random = random.Random(seed)

    def randint(self, a: int, b: int) -> int:
        """Return an integer from the inclusive interval ``[a, b]``."""
        return self._random.randint(a, b)

    def chance(self, p: float) -> bool:
        """Return whether an event with probability ``p`` occurs."""
        if p <= 0.0:
            return False
        if p >= 1.0:
            return True
        return self._random.random() < p
