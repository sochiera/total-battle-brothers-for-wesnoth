"""Immutable resource values and safe arithmetic for game economy."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Resources:
    """Store non-negative amounts of wheat and gold."""

    wheat: int
    gold: int

    def __post_init__(self) -> None:
        """Reject resource amounts below zero."""
        if self.wheat < 0 or self.gold < 0:
            raise ValueError("resource amounts cannot be negative")

    def add(self, other: "Resources") -> "Resources":
        """Return a new value containing the sum of both resources."""
        return Resources(self.wheat + other.wheat, self.gold + other.gold)

    def subtract(
        self, other: "Resources", *, allow_negative: bool = False
    ) -> "Resources":
        """Subtract resources, optionally clamping shortages to zero."""
        wheat = self.wheat - other.wheat
        gold = self.gold - other.gold
        if allow_negative:
            return Resources(max(0, wheat), max(0, gold))
        return Resources(wheat, gold)

    def can_afford(self, cost: "Resources") -> bool:
        """Return whether both available amounts cover ``cost``."""
        return self.wheat >= cost.wheat and self.gold >= cost.gold
