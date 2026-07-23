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

    def state(self) -> tuple:
        """Return the internal state of the generator."""
        return self._random.getstate()

    @classmethod
    def from_state(cls, state: tuple) -> "Rng":
        """Build a new Rng from a state previously returned by ``state()``."""
        rng = cls.__new__(cls)
        rng._random = random.Random()
        rng._random.setstate(state)
        return rng
