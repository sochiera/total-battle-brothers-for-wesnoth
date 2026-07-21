"""Pure combat strength aggregation for sequences of units."""

from __future__ import annotations

from collections.abc import Iterable
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tbb.unit import Unit


def combat_totals(units: Iterable[Unit]) -> tuple[int, int, int]:
    """Return ``(hp, attack, defense)`` sums over *units*.

    Aggregates ``Unit.hp`` / ``Unit.damage`` / ``Unit.defense``. Pure and
    deterministic: does not mutate inputs; empty sequence yields ``(0, 0, 0)``.
    """
    total_hp = 0
    total_attack = 0
    total_defense = 0
    for unit in units:
        total_hp += unit.hp
        total_attack += unit.damage
        total_defense += unit.defense
    return (total_hp, total_attack, total_defense)
