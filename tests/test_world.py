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


def test_move_party_to_adjacent_region_preserves_input_and_settlement():
    camp = Region("Camp")
    vale = Region("Vale")
    garrison = (Unit(training=1),)
    settlement = Settlement("Oakrest", population=4, garrison=garrison)
    party = Party(Unit(equipment=1), [Unit(experience=1)])
    world = WorldMap(
        [camp, vale],
        [(camp, vale)],
        settlements={vale: settlement},
        parties={camp: party},
    )

    moved = world.move_party(camp, vale, move_points=1)

    assert world.party_at(camp) is party
    assert world.party_at(vale) is None
    assert moved.party_at(camp) is None
    assert moved.party_at(vale) is party
    assert world.settlement_at(vale) is settlement
    assert moved.settlement_at(vale) is settlement
    assert moved.settlement_at(vale).garrison == garrison


@pytest.mark.parametrize(
    "source_name, destination_name, move_points",
    [
        ("Camp", "Wilds", 1),
        ("Camp", "Vale", 0),
        ("Vale", "Camp", 1),
        ("Camp", "Vale", 1),
    ],
    ids=["not-adjacent", "no-budget", "no-source-party", "occupied-target"],
)
def test_move_party_rejects_illegal_moves(
    source_name, destination_name, move_points
):
    camp = Region("Camp")
    vale = Region("Vale")
    wilds = Region("Wilds")
    regions = {region.name: region for region in (camp, vale, wilds)}
    parties = {camp: Party(Unit())}
    if source_name == "Camp" and destination_name == "Vale" and move_points == 1:
        parties[vale] = Party(Unit(training=1))
    world = WorldMap(
        [camp, vale, wilds], [(camp, vale)], parties=parties
    )

    with pytest.raises(ValueError):
        world.move_party(
            regions[source_name], regions[destination_name], move_points
        )


@pytest.mark.parametrize("unknown_endpoint", ["source", "destination"])
def test_move_party_rejects_region_outside_map(unknown_endpoint):
    camp = Region("Camp")
    vale = Region("Vale")
    unknown = Region("Unknown")
    world = WorldMap(
        [camp, vale], [(camp, vale)], parties={camp: Party(Unit())}
    )
    source = unknown if unknown_endpoint == "source" else camp
    destination = unknown if unknown_endpoint == "destination" else vale

    with pytest.raises(ValueError):
        world.move_party(source, destination, move_points=1)
