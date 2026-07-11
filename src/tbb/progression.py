"""Deterministic diminishing-return progression for unit quality pillars."""

from math import isqrt


def pillar_level(investment: int) -> int:
    """Return the pillar level reached by a cumulative investment."""
    if investment < 0:
        raise ValueError("investment cannot be negative")
    return (isqrt(8 * investment + 1) - 1) // 2


def investment_for_level(level: int) -> int:
    """Return the cumulative investment required to reach ``level``."""
    if level < 0:
        raise ValueError("level cannot be negative")
    return level * (level + 1) // 2
