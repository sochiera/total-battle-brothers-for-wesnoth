"""Pure calculations for combat rules."""

from tbb.terrain import Terrain
from tbb.unit import Unit


def melee_hit_chance(
    attacker: Unit,
    defender: Unit,
    attacker_terrain: Terrain,
    defender_terrain: Terrain,
    morale: int,
) -> int:
    """Return the attacker's melee hit chance as a percentage."""
    chance = (
        50
        + attacker.accuracy
        + attacker_terrain.accuracy_mod
        + morale
        - defender.defense
        - defender_terrain.defense_mod
    )
    return max(5, min(95, chance))
