"""Pure transitions used by the headless game driver."""

from tbb.duchy import Duchy
from tbb.world import WorldMap


def _has_owned_party(world: WorldMap, owner_id: str) -> bool:
    return any(party.owner_id == owner_id for party in world.parties.values())


def resolve_hero_survival(
    duchy: Duchy, world_before: WorldMap, world_after: WorldMap
) -> Duchy:
    """Resolve succession when a duchy's deployed party disappears."""
    if _has_owned_party(world_before, duchy.duchy_id) and not _has_owned_party(
        world_after, duchy.duchy_id
    ):
        return duchy.succeed()
    return duchy
