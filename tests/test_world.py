"""Tests for the immutable strategic world graph."""

from dataclasses import FrozenInstanceError

import pytest

from tbb import Party, Region, Settlement, Unit, WorldMap


def test_neighbors_are_bidirectional_and_follow_region_order():
    north = Region("North")
    south = Region("South")
    wilds = Region("Wilds")
    world = WorldMap(
        [north, south, wilds],
        [(south, north), (south, wilds)],
    )

    assert world.neighbors(north) == (south,)
    assert world.neighbors(south) == (north, wilds)
    assert world.neighbors(wilds) == (south,)
    assert WorldMap([wilds]).neighbors(wilds) == ()


def test_settlement_lookup_returns_settlement_or_none():
    town_region = Region("Vale")
    empty_region = Region("March")
    town = Settlement("Oakrest", population=4)
    world = WorldMap([town_region, empty_region], settlements={town_region: town})

    assert world.settlement_at(town_region) == town
    assert world.settlement_at(empty_region) is None


@pytest.mark.parametrize(
    "regions, connections, settlements",
    [
        ([Region("A"), Region("A")], [], {}),
        ([Region("A")], [(Region("A"), Region("A"))], {}),
        ([Region("A")], [(Region("A"), Region("B"))], {}),
        ([Region("A")], [], {Region("B"): Settlement("B", 1)}),
    ],
    ids=["duplicate-region", "self-loop", "unknown-endpoint", "unknown-settlement"],
)
def test_invalid_world_definitions_are_rejected(regions, connections, settlements):
    with pytest.raises(ValueError):
        WorldMap(regions, connections, settlements)


def test_world_copies_inputs_and_exposes_only_immutable_collections():
    coast = Region("Coast")
    hills = Region("Hills")
    town = Settlement("Port", 3)
    regions = [coast, hills]
    connections = [(coast, hills)]
    settlements = {coast: town}
    world = WorldMap(regions, connections, settlements)

    with pytest.raises(FrozenInstanceError):
        coast.name = "Changed"
    with pytest.raises(AttributeError):
        world.regions.append(Region("New"))
    with pytest.raises(AttributeError):
        world.connections.append((coast, coast))
    with pytest.raises(TypeError):
        world.settlements[hills] = Settlement("Hillfort", 2)

    regions.clear()
    connections.clear()
    settlements.clear()

    assert world.regions == (coast, hills)
    assert world.connections == ((coast, hills),)
    assert world.neighbors(coast) == (hills,)
    assert world.settlement_at(coast) == town


def test_public_api_exports_world_types():
    from tbb import Region as PublicRegion, WorldMap as PublicWorldMap

    assert PublicRegion is Region
    assert PublicWorldMap is WorldMap


def test_party_lookup_returns_party_or_none_and_rejects_unknown_region():
    camp = Region("Camp")
    road = Region("Road")
    party = Party(Unit())
    world = WorldMap([camp, road], parties={camp: party})

    assert world.party_at(camp) == party
    assert world.party_at(road) is None
    with pytest.raises(ValueError):
        world.party_at(Region("Unknown"))


def test_place_party_returns_new_world_without_changing_original():
    camp = Region("Camp")
    party = Party(Unit())
    world = WorldMap([camp])

    placed = world.place_party(party, camp)

    assert placed.party_at(camp) == party
    assert world.party_at(camp) is None


def test_place_party_rejects_occupied_and_unknown_regions():
    camp = Region("Camp")
    occupying_party = Party(Unit())
    world = WorldMap([camp], parties={camp: occupying_party})

    with pytest.raises(ValueError):
        world.place_party(Party(Unit()), camp)
    with pytest.raises(ValueError):
        world.place_party(Party(Unit()), Region("Unknown"))


def test_world_copies_party_input_and_exposes_immutable_mapping():
    camp = Region("Camp")
    party = Party(Unit())
    parties = {camp: party}
    world = WorldMap([camp], parties=parties)

    parties.clear()

    assert world.parties == {camp: party}
    with pytest.raises(TypeError):
        world.parties[camp] = Party(Unit())


def test_party_and_settlement_can_share_a_region():
    vale = Region("Vale")
    settlement = Settlement("Oakrest", population=4)
    party = Party(Unit())
    world = WorldMap(
        [vale], settlements={vale: settlement}, parties={vale: party}
    )

    assert world.settlement_at(vale) == settlement
    assert world.party_at(vale) == party
