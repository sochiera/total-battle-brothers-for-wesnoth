"""Unit tests for pure map-lookup helpers (tbbui.maplookup)."""

from tbb.party import Party
from tbb.unit import Unit
from tbb.world import Region, WorldMap
from tbbui.maplookup import first_party_region


def test_first_party_region_returns_first_match_none_when_absent_no_mutation():
    """first_party_region(world, owner_id) is the first region in
    world.regions whose party_at has that owner_id; otherwise None.
    Pure: does not mutate world.
    """
    west = Region("West")
    east = Region("East")
    north = Region("North")
    world = WorldMap(
        [west, east, north],
        [],
        parties={
            # first matching region for "alpha" is west (regions order)
            west: Party(hero=Unit(), units=(), owner_id="alpha"),
            east: Party(hero=Unit(), units=(), owner_id="beta"),
            # second alpha party later in order must not win
            north: Party(hero=Unit(), units=(), owner_id="alpha"),
        },
    )
    regions_before = world.regions
    parties_before = {r: world.party_at(r) for r in world.regions}

    assert first_party_region(world, "alpha") is west
    assert first_party_region(world, "beta") is east
    assert first_party_region(world, "missing") is None

    assert world.regions is regions_before
    for r in world.regions:
        assert world.party_at(r) is parties_before[r]
