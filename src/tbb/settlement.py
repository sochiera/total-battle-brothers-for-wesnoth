"""Immutable settlement state and its population pool."""

from dataclasses import dataclass, replace


@dataclass(frozen=True)
class Settlement:
    """Represent a settlement with free and occupied population."""

    name: str
    population: int
    occupied: int = 0

    def __post_init__(self) -> None:
        """Reject an inconsistent population pool."""
        if self.population < 0:
            raise ValueError("population cannot be negative")
        if self.occupied < 0 or self.occupied > self.population:
            raise ValueError("occupied must be between zero and population")

    @property
    def free(self) -> int:
        """Return population currently available for assignment."""
        return self.population - self.occupied

    def occupy(self, amount: int) -> "Settlement":
        """Return a new settlement with ``amount`` population assigned."""
        if amount < 0:
            raise ValueError("amount to occupy cannot be negative")
        if amount > self.free:
            raise ValueError("not enough free population")
        return replace(self, occupied=self.occupied + amount)

    def release(self, amount: int) -> "Settlement":
        """Return a new settlement with ``amount`` population released."""
        if amount < 0:
            raise ValueError("amount to release cannot be negative")
        if amount > self.occupied:
            raise ValueError("cannot release more than occupied population")
        return replace(self, occupied=self.occupied - amount)
