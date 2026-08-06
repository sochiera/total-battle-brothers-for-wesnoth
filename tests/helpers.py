"""Shared assertions for immutable strategic test fixtures."""

from tbb.party import Party
from tbb.world import Region, WorldMap


def assert_moved_party(world: WorldMap, region: Region, original: Party) -> None:
    """Assert that ``original`` moved to ``region`` and consumed its move."""
    moved = world.party_at(region)
    assert moved is not None
    assert moved is not original
    assert moved.hero is original.hero
    assert moved.units == original.units
    assert moved.owner_id == original.owner_id
    assert moved.acted_this_month is True
