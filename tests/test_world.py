"""Tests for the immutable strategic world graph."""

from dataclasses import FrozenInstanceError

import pytest

from tbb import (
    BattleResult,
    BattleSide,
    Battlefield,
    BRUISE,
    HexBattle,
    FARM,
    Hex,
    MARKET,
    Party,
    PLAINS,
    Region,
    Resources,
    Rng,
    Settlement,
    Unit,
    WorldMap,
)


def _battle_with_fallen_subordinates(attacker, defender):
    battle = HexBattle(Battlefield())
    for row, unit in enumerate((attacker.hero, *attacker.units)):
        battle = battle.deploy(unit, Hex(0, row), BattleSide.ATTACKER)
    for row, unit in enumerate((defender.hero, *defender.units)):
        battle = battle.deploy(unit, Hex(2, row), BattleSide.DEFENDER)
    for position in (Hex(0, 2), Hex(2, 2)):
        battle = battle.damage(position, battle.unit_at(position).hp)
        battle = battle.resolve_defeat(position, Rng(1))
    return battle


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


def test_tick_settlements_applies_economy_births_then_immigration():
    farms = Region("Farms")
    market = Region("Market")
    farming_town = Settlement(
        "Oakrest",
        population=2,
        active_buildings=(FARM, MARKET),
        storage=Resources(wheat=1, gold=0),
        capacity=4,
    )
    market_town = Settlement(
        "Goldport",
        population=2,
        active_buildings=(MARKET,),
        storage=Resources(wheat=2, gold=0),
        capacity=5,
    )
    world = WorldMap(
        [farms, market],
        settlements={farms: farming_town, market: market_town},
    )

    ticked = world.tick_settlements()

    assert ticked.settlement_at(farms).storage == Resources(wheat=2, gold=2)
    assert ticked.settlement_at(farms).population == 4
    assert ticked.settlement_at(market).storage == Resources(wheat=0, gold=2)
    assert ticked.settlement_at(market).population == 2


def test_tick_settlements_chains_phase_results_in_required_order(monkeypatch):
    vale = Region("Vale")
    initial = Settlement("Initial", population=1)
    after_economy = Settlement("After economy", population=2)
    after_growth = Settlement("After growth", population=3)
    after_immigration = Settlement("After immigration", population=4)
    calls = []

    def tick_economy(settlement):
        calls.append(("economy", settlement))
        return after_economy

    def tick_growth(settlement):
        calls.append(("growth", settlement))
        return after_growth

    def tick_immigration(settlement):
        calls.append(("immigration", settlement))
        return after_immigration

    monkeypatch.setattr(Settlement, "tick_economy", tick_economy)
    monkeypatch.setattr(Settlement, "tick_growth", tick_growth)
    monkeypatch.setattr(Settlement, "tick_immigration", tick_immigration)
    world = WorldMap([vale], settlements={vale: initial})

    ticked = world.tick_settlements()

    assert [phase for phase, _ in calls] == [
        "economy",
        "growth",
        "immigration",
    ]
    assert calls[0][1] is initial
    assert calls[1][1] is after_economy
    assert calls[2][1] is after_growth
    assert ticked.settlement_at(vale) is after_immigration


def test_tick_settlements_preserves_graph_empty_region_and_party_positions():
    town = Region("Town")
    empty = Region("Wilds")
    party = Party(Unit(), owner_id="north")
    world = WorldMap(
        [town, empty],
        [(town, empty)],
        settlements={town: Settlement("Oakrest", population=1)},
        parties={empty: party},
    )

    ticked = world.tick_settlements()

    assert ticked.regions == world.regions
    assert ticked.connections == world.connections
    assert ticked.neighbors(town) == (empty,)
    assert ticked.settlement_at(empty) is None
    assert ticked.party_at(empty) is party


def test_tick_settlements_does_not_mutate_input_and_returns_immutable_mapping():
    vale = Region("Vale")
    original_settlement = Settlement(
        "Oakrest", population=1, storage=Resources(wheat=2, gold=1)
    )
    world = WorldMap([vale], settlements={vale: original_settlement})
    settlements_before = dict(world.settlements)

    ticked = world.tick_settlements()

    assert dict(world.settlements) == settlements_before
    assert world.settlement_at(vale) is original_settlement
    assert original_settlement.population == 1
    assert original_settlement.storage == Resources(wheat=2, gold=1)
    assert ticked.settlement_at(vale) is not original_settlement
    with pytest.raises(TypeError):
        ticked.settlements[vale] = original_settlement


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


def test_start_battle_deploys_adjacent_parties_in_deterministic_rows():
    camp = Region("Camp")
    vale = Region("Vale")
    attacker = Party(Unit(training=3), [Unit(equipment=1), Unit(experience=2)], "north")
    defender = Party(Unit(training=4), [Unit(equipment=2)], "south")
    world = WorldMap(
        [camp, vale],
        [(camp, vale)],
        parties={camp: attacker, vale: defender},
    )

    battle = world.start_battle(camp, vale)

    expected = (
        (Hex(0, 0), attacker.hero, BattleSide.ATTACKER),
        (Hex(0, 1), attacker.units[0], BattleSide.ATTACKER),
        (Hex(0, 2), attacker.units[1], BattleSide.ATTACKER),
        (Hex(2, 0), defender.hero, BattleSide.DEFENDER),
        (Hex(2, 1), defender.units[0], BattleSide.DEFENDER),
    )
    assert tuple(
        (position, battle.unit_at(position), battle.side_at(position))
        for position in battle.units
    ) == expected
    assert all(
        battle.battlefield.terrain_at(position) == PLAINS
        for position in battle.units
    )
    assert world.start_battle(camp, vale).units == battle.units


def test_start_battle_does_not_change_world_or_party_composition():
    camp = Region("Camp")
    vale = Region("Vale")
    attacker = Party(Unit(training=1), [Unit(equipment=1)], "north")
    defender = Party(Unit(training=2), [Unit(equipment=2)], "south")
    world = WorldMap(
        [camp, vale], [(camp, vale)], parties={camp: attacker, vale: defender}
    )
    parties_before = dict(world.parties)
    attacker_before = (attacker.hero, attacker.units)
    defender_before = (defender.hero, defender.units)

    world.start_battle(camp, vale)

    assert dict(world.parties) == parties_before
    assert world.party_at(camp) is attacker
    assert world.party_at(vale) is defender
    assert (attacker.hero, attacker.units) == attacker_before
    assert (defender.hero, defender.units) == defender_before


@pytest.mark.parametrize(
    "parties, source_name, destination_name",
    [
        ({"Vale"}, "Camp", "Vale"),
        ({"Camp"}, "Camp", "Vale"),
        ({"Camp", "Vale"}, "Camp", "Camp"),
        ({"Camp", "Wilds"}, "Camp", "Wilds"),
        ({"Camp", "Vale"}, "Camp", "Unknown"),
    ],
    ids=[
        "no-attacker",
        "no-defender",
        "same-region",
        "not-adjacent",
        "outside-map",
    ],
)
def test_start_battle_rejects_invalid_contact(
    parties, source_name, destination_name
):
    camp = Region("Camp")
    vale = Region("Vale")
    wilds = Region("Wilds")
    regions = {region.name: region for region in (camp, vale, wilds)}
    world = WorldMap(
        [camp, vale, wilds],
        [(camp, vale)],
        parties={regions[name]: Party(Unit()) for name in parties},
    )

    with pytest.raises(ValueError):
        destination = (
            Region("Unknown")
            if destination_name == "Unknown"
            else regions[destination_name]
        )
        world.start_battle(
            regions[source_name],
            destination,
        )


@pytest.mark.parametrize(
    "attacker_owner, defender_owner",
    [("north", "north"), (None, "south"), ("north", None)],
    ids=["same-owner", "missing-attacker-owner", "missing-defender-owner"],
)
def test_start_battle_rejects_non_enemy_contact(attacker_owner, defender_owner):
    camp = Region("Camp")
    vale = Region("Vale")
    world = WorldMap(
        [camp, vale],
        [(camp, vale)],
        parties={
            camp: Party(Unit(), owner_id=attacker_owner),
            vale: Party(Unit(), owner_id=defender_owner),
        },
    )

    with pytest.raises(ValueError):
        world.start_battle(camp, vale)


@pytest.mark.parametrize(
    "result, expected_source, expected_destination",
    [
        (BattleResult.ATTACKER_WIN, None, "attacker"),
        (BattleResult.DEFENDER_WIN, None, "defender"),
        (BattleResult.DRAW, None, None),
    ],
)
def test_apply_party_battle_result_updates_occupancy(
    result, expected_source, expected_destination
):
    camp = Region("Camp")
    vale = Region("Vale")
    attacker = Party(Unit(training=1), owner_id="north")
    defender = Party(Unit(training=2), owner_id="south")
    parties = {"attacker": attacker, "defender": defender, None: None}
    world = WorldMap(
        [camp, vale], [(camp, vale)], parties={camp: attacker, vale: defender}
    )

    resolved = world.apply_party_battle_result(camp, vale, result)

    assert resolved.party_at(camp) is parties[expected_source]
    assert resolved.party_at(vale) is parties[expected_destination]
    assert world.party_at(camp) is attacker
    assert world.party_at(vale) is defender
    assert resolved is not world


def test_apply_party_battle_result_preserves_settlements_and_graph():
    camp = Region("Camp")
    vale = Region("Vale")
    settlement = Settlement("Oakrest", 3, garrison=(Unit(),), owner_id="south")
    attacker = Party(Unit(), owner_id="north")
    defender = Party(Unit(), owner_id="south")
    world = WorldMap(
        [camp, vale],
        [(camp, vale)],
        settlements={vale: settlement},
        parties={camp: attacker, vale: defender},
    )

    resolved = world.apply_party_battle_result(
        camp, vale, BattleResult.ATTACKER_WIN
    )

    assert resolved.regions == world.regions
    assert resolved.connections == world.connections
    assert resolved.settlement_at(vale) is settlement
    assert resolved.settlement_at(vale).garrison == settlement.garrison


@pytest.mark.parametrize(
    "result, surviving_side",
    [
        (BattleResult.ATTACKER_WIN, BattleSide.ATTACKER),
        (BattleResult.DEFENDER_WIN, BattleSide.DEFENDER),
    ],
)
def test_apply_party_battle_result_reconstructs_winning_survivors(
    result, surviving_side
):
    camp = Region("Camp")
    vale = Region("Vale")
    attacker = Party(
        Unit(experience=4),
        [Unit(training=2, experience=7, wounds=(BRUISE,)), Unit(equipment=3)],
        owner_id="north",
    )
    defender = Party(
        Unit(experience=5),
        [Unit(training=3), Unit(equipment=4)],
        owner_id="south",
    )
    world = WorldMap(
        [camp, vale], [(camp, vale)], parties={camp: attacker, vale: defender}
    )
    battle = _battle_with_fallen_subordinates(attacker, defender)
    parties_before = dict(world.parties)
    survivors = battle.side_survivors(surviving_side)
    battle_units_before = dict(battle.units)

    resolved = world.apply_party_battle_result(
        camp, vale, result, battle=battle
    )

    reconstructed = resolved.party_at(vale)
    original = attacker if surviving_side is BattleSide.ATTACKER else defender
    assert resolved.party_at(camp) is None
    assert reconstructed.hero is survivors[0]
    assert reconstructed.units == survivors[1:]
    assert all(actual is expected for actual, expected in zip(
        (reconstructed.hero, *reconstructed.units), survivors
    ))
    assert reconstructed.owner_id == original.owner_id
    if surviving_side is BattleSide.ATTACKER:
        assert reconstructed.units[0].wounds == (BRUISE,)
        assert reconstructed.units[0].experience == 7
    assert original.units[1] not in (reconstructed.hero, *reconstructed.units)
    assert dict(world.parties) == parties_before
    assert dict(battle.units) == battle_units_before


def test_apply_party_battle_result_draw_with_battle_removes_both_parties():
    camp = Region("Camp")
    vale = Region("Vale")
    attacker = Party(Unit(), [Unit(), Unit(equipment=1)], "north")
    defender = Party(Unit(training=1), [Unit(), Unit(equipment=2)], "south")
    world = WorldMap(
        [camp, vale], [(camp, vale)], parties={camp: attacker, vale: defender}
    )
    battle = _battle_with_fallen_subordinates(attacker, defender)

    resolved = world.apply_party_battle_result(
        camp, vale, BattleResult.DRAW, battle=battle
    )

    assert resolved.party_at(camp) is None
    assert resolved.party_at(vale) is None


@pytest.mark.parametrize(
    "party_regions, source_name, destination_name",
    [
        ({"Camp", "Vale"}, "Unknown", "Vale"),
        ({"Camp", "Vale"}, "Camp", "Camp"),
        ({"Camp", "Wilds"}, "Camp", "Wilds"),
        ({"Vale"}, "Camp", "Vale"),
        ({"Camp"}, "Camp", "Vale"),
    ],
    ids=["outside-map", "same-region", "not-adjacent", "empty-source", "empty-destination"],
)
def test_apply_party_battle_result_rejects_invalid_contact(
    party_regions, source_name, destination_name
):
    camp = Region("Camp")
    vale = Region("Vale")
    wilds = Region("Wilds")
    regions = {region.name: region for region in (camp, vale, wilds)}
    world = WorldMap(
        [camp, vale, wilds],
        [(camp, vale)],
        parties={
            regions[name]: Party(Unit(), owner_id=name) for name in party_regions
        },
    )
    source = Region("Unknown") if source_name == "Unknown" else regions[source_name]

    with pytest.raises(ValueError):
        world.apply_party_battle_result(
            source, regions[destination_name], BattleResult.DRAW
        )


def test_resolve_party_battle_moves_attacking_survivors_after_win():
    camp = Region("Camp")
    vale = Region("Vale")
    attacker = Party(
        Unit(training=5, equipment=4),
        [Unit(equipment=1), Unit(equipment=4)],
        owner_id="north",
    )
    defender = Party(Unit(equipment=3), [Unit(equipment=3)], owner_id="south")
    world = WorldMap(
        [camp, vale], [(camp, vale)], parties={camp: attacker, vale: defender}
    )

    resolved = world.resolve_party_battle(
        camp, vale, Rng(2), move_points=1, morale=100
    )

    survivors = resolved.party_at(vale)
    assert resolved.party_at(camp) is None
    assert survivors.owner_id == "north"
    assert len((survivors.hero, *survivors.units)) < len(
        (attacker.hero, *attacker.units)
    )
    assert all(
        any(unit is original for original in (attacker.hero, *attacker.units))
        for unit in (survivors.hero, *survivors.units)
    )
    assert all(unit is not attacker.units[0] for unit in survivors.units)


def test_resolve_party_battle_leaves_defending_survivors_after_win():
    camp = Region("Camp")
    vale = Region("Vale")
    attacker = Party(Unit(equipment=1), owner_id="north")
    defender = Party(Unit(training=5, equipment=12), owner_id="south")
    world = WorldMap(
        [camp, vale], [(camp, vale)], parties={camp: attacker, vale: defender}
    )

    resolved = world.resolve_party_battle(camp, vale, Rng(4))

    assert resolved.party_at(camp) is None
    assert resolved.party_at(vale).owner_id == "south"


def test_resolve_party_battle_is_deterministic_and_does_not_mutate_world():
    camp = Region("Camp")
    vale = Region("Vale")
    settlement = Settlement("Oakrest", 3, garrison=(Unit(),), owner_id="south")
    attacker = Party(Unit(equipment=5), [Unit(equipment=2)], "north")
    defender = Party(Unit(equipment=4), [Unit(equipment=3)], "south")
    world = WorldMap(
        [camp, vale],
        [(camp, vale)],
        settlements={vale: settlement},
        parties={camp: attacker, vale: defender},
    )

    first = world.resolve_party_battle(camp, vale, Rng(12))
    second = world.resolve_party_battle(camp, vale, Rng(12))

    assert first == second
    assert world.party_at(camp) is attacker
    assert world.party_at(vale) is defender
    assert world.settlement_at(vale) is settlement
    assert first.settlement_at(vale) is settlement
    assert first.settlement_at(vale).garrison is settlement.garrison


def test_resolve_party_battle_propagates_start_battle_validation():
    camp = Region("Camp")
    vale = Region("Vale")
    world = WorldMap(
        [camp, vale],
        [(camp, vale)],
        parties={
            camp: Party(Unit(), owner_id="north"),
            vale: Party(Unit(), owner_id="north"),
        },
    )

    with pytest.raises(ValueError, match="different owners"):
        world.resolve_party_battle(camp, vale, Rng(1))


def test_start_settlement_battle_deploys_party_and_garrison_in_deterministic_rows():
    camp = Region("Camp")
    vale = Region("Vale")
    attacker = Party(Unit(training=3), [Unit(equipment=1), Unit(experience=2)], "north")
    garrison = (Unit(training=4), Unit(equipment=2), Unit(experience=1))
    settlement = Settlement("Oakrest", population=6, garrison=garrison, owner_id="south")
    world = WorldMap(
        [camp, vale],
        [(camp, vale)],
        settlements={vale: settlement},
        parties={camp: attacker},
    )

    battle = world.start_settlement_battle(camp, vale)

    expected = (
        (Hex(0, 0), attacker.hero, BattleSide.ATTACKER),
        (Hex(0, 1), attacker.units[0], BattleSide.ATTACKER),
        (Hex(0, 2), attacker.units[1], BattleSide.ATTACKER),
        (Hex(2, 0), garrison[0], BattleSide.DEFENDER),
        (Hex(2, 1), garrison[1], BattleSide.DEFENDER),
        (Hex(2, 2), garrison[2], BattleSide.DEFENDER),
    )
    assert tuple(
        (position, battle.unit_at(position), battle.side_at(position))
        for position in battle.units
    ) == expected
    assert all(
        battle.battlefield.terrain_at(position) == PLAINS
        for position in battle.units
    )


def test_start_settlement_battle_does_not_change_world_party_or_settlement():
    camp = Region("Camp")
    vale = Region("Vale")
    attacker = Party(Unit(training=1), [Unit(equipment=1)], "north")
    garrison = (Unit(training=2), Unit(equipment=2))
    settlement = Settlement("Oakrest", population=4, garrison=garrison, owner_id="south")
    world = WorldMap(
        [camp, vale],
        [(camp, vale)],
        settlements={vale: settlement},
        parties={camp: attacker},
    )
    parties_before = dict(world.parties)
    settlements_before = dict(world.settlements)
    party_before = (attacker.hero, attacker.units)
    garrison_before = settlement.garrison

    world.start_settlement_battle(camp, vale)

    assert dict(world.parties) == parties_before
    assert dict(world.settlements) == settlements_before
    assert world.party_at(camp) is attacker
    assert world.settlement_at(vale) is settlement
    assert (attacker.hero, attacker.units) == party_before
    assert settlement.garrison == garrison_before


@pytest.mark.parametrize(
    "party_region, settlement_region, source_name, destination_name",
    [
        (None, "Vale", "Camp", "Vale"),
        ("Camp", None, "Camp", "Vale"),
        ("Camp", "Camp", "Camp", "Camp"),
        ("Camp", "Wilds", "Camp", "Wilds"),
        ("Camp", "Vale", "Camp", "Unknown"),
    ],
    ids=["no-party", "no-settlement", "same-region", "not-adjacent", "outside-map"],
)
def test_start_settlement_battle_rejects_invalid_contact(
    party_region, settlement_region, source_name, destination_name
):
    camp = Region("Camp")
    vale = Region("Vale")
    wilds = Region("Wilds")
    regions = {region.name: region for region in (camp, vale, wilds)}
    parties = (
        {regions[party_region]: Party(Unit())} if party_region is not None else {}
    )
    settlements = (
        {regions[settlement_region]: Settlement("Oakrest", 2, garrison=(Unit(),))}
        if settlement_region is not None
        else {}
    )
    world = WorldMap(
        [camp, vale, wilds],
        [(camp, vale)],
        settlements=settlements,
        parties=parties,
    )
    destination = (
        Region("Unknown")
        if destination_name == "Unknown"
        else regions[destination_name]
    )

    with pytest.raises(ValueError):
        world.start_settlement_battle(regions[source_name], destination)


@pytest.mark.parametrize(
    "party_owner, settlement_owner",
    [("north", "north"), (None, "south"), ("north", None)],
    ids=["same-owner", "missing-party-owner", "missing-settlement-owner"],
)
def test_start_settlement_battle_rejects_non_enemy_contact(
    party_owner, settlement_owner
):
    camp = Region("Camp")
    vale = Region("Vale")
    world = WorldMap(
        [camp, vale],
        [(camp, vale)],
        settlements={
            vale: Settlement(
                "Oakrest", 2, garrison=(Unit(),), owner_id=settlement_owner
            )
        },
        parties={camp: Party(Unit(), owner_id=party_owner)},
    )

    with pytest.raises(ValueError):
        world.start_settlement_battle(camp, vale)


@pytest.mark.parametrize(
    "result, expected_party, expected_owner",
    [
        (BattleResult.ATTACKER_WIN, "attacker", "north"),
        (BattleResult.DEFENDER_WIN, None, "south"),
        (BattleResult.DRAW, None, "south"),
    ],
)
def test_apply_settlement_battle_result_updates_world(
    result, expected_party, expected_owner
):
    camp = Region("Camp")
    vale = Region("Vale")
    attacker = Party(Unit(training=1), owner_id="north")
    garrison = (Unit(training=2),)
    settlement = Settlement(
        "Oakrest", 3, garrison=garrison, owner_id="south"
    )
    world = WorldMap(
        [camp, vale],
        [(camp, vale)],
        settlements={vale: settlement},
        parties={camp: attacker},
    )

    resolved = world.apply_settlement_battle_result(camp, vale, result)

    assert resolved.party_at(camp) is None
    assert resolved.party_at(vale) is (
        attacker if expected_party == "attacker" else None
    )
    assert resolved.settlement_at(vale).owner_id == expected_owner
    assert resolved.settlement_at(vale).garrison == garrison
    if result is not BattleResult.ATTACKER_WIN:
        assert resolved.settlement_at(vale) is settlement

    assert world.party_at(camp) is attacker
    assert world.party_at(vale) is None
    assert world.settlement_at(vale) is settlement
    assert world.settlement_at(vale).owner_id == "south"
    assert resolved is not world


def test_apply_settlement_attacker_win_rejects_occupied_destination():
    camp = Region("Camp")
    vale = Region("Vale")
    world = WorldMap(
        [camp, vale],
        [(camp, vale)],
        settlements={vale: Settlement("Oakrest", 2, owner_id="south")},
        parties={
            camp: Party(Unit(), owner_id="north"),
            vale: Party(Unit(), owner_id="third"),
        },
    )

    with pytest.raises(ValueError):
        world.apply_settlement_battle_result(
            camp, vale, BattleResult.ATTACKER_WIN
        )


@pytest.mark.parametrize(
    "party_region, settlement_region, source_name, destination_name",
    [
        ("Camp", "Vale", "Unknown", "Vale"),
        ("Camp", "Vale", "Camp", "Unknown"),
        ("Camp", "Vale", "Camp", "Camp"),
        ("Camp", "Wilds", "Camp", "Wilds"),
        (None, "Vale", "Camp", "Vale"),
        ("Camp", None, "Camp", "Vale"),
    ],
    ids=[
        "source-outside-map",
        "destination-outside-map",
        "same-region",
        "not-adjacent",
        "no-party",
        "no-settlement",
    ],
)
def test_apply_settlement_battle_result_rejects_invalid_contact(
    party_region, settlement_region, source_name, destination_name
):
    camp = Region("Camp")
    vale = Region("Vale")
    wilds = Region("Wilds")
    regions = {region.name: region for region in (camp, vale, wilds)}
    parties = (
        {regions[party_region]: Party(Unit(), owner_id="north")}
        if party_region is not None
        else {}
    )
    settlements = (
        {
            regions[settlement_region]: Settlement(
                "Oakrest", 2, owner_id="south"
            )
        }
        if settlement_region is not None
        else {}
    )
    world = WorldMap(
        [camp, vale, wilds],
        [(camp, vale)],
        settlements=settlements,
        parties=parties,
    )
    source = Region("Unknown") if source_name == "Unknown" else regions[source_name]
    destination = (
        Region("Unknown")
        if destination_name == "Unknown"
        else regions[destination_name]
    )

    with pytest.raises(ValueError):
        world.apply_settlement_battle_result(
            source, destination, BattleResult.DRAW
        )


def test_apply_settlement_attacker_win_preserves_graph_and_garrison():
    camp = Region("Camp")
    vale = Region("Vale")
    garrison = (Unit(training=2), Unit(equipment=1))
    settlement = Settlement(
        "Oakrest", 4, garrison=garrison, owner_id="south"
    )
    world = WorldMap(
        [camp, vale],
        [(camp, vale)],
        settlements={vale: settlement},
        parties={camp: Party(Unit(), owner_id="north")},
    )

    resolved = world.apply_settlement_battle_result(
        camp, vale, BattleResult.ATTACKER_WIN
    )

    assert resolved.regions == world.regions
    assert resolved.connections == world.connections
    assert resolved.neighbors(camp) == world.neighbors(camp)
    assert resolved.settlement_at(vale).garrison is garrison


def test_apply_settlement_attacker_win_reconstructs_party_survivors():
    camp = Region("Camp")
    vale = Region("Vale")
    attacker = Party(
        Unit(experience=6),
        [Unit(training=2), Unit(equipment=4)],
        owner_id="north",
    )
    garrison = (Unit(training=3), Unit(equipment=2), Unit(experience=1))
    settlement = Settlement(
        "Oakrest", 5, garrison=garrison, owner_id="south"
    )
    world = WorldMap(
        [camp, vale],
        [(camp, vale)],
        settlements={vale: settlement},
        parties={camp: attacker},
    )
    defender = Party(garrison[0], garrison[1:], owner_id="south")
    battle = _battle_with_fallen_subordinates(attacker, defender)
    survivors = battle.side_survivors(BattleSide.ATTACKER)
    battle_units_before = dict(battle.units)

    resolved = world.apply_settlement_battle_result(
        camp, vale, BattleResult.ATTACKER_WIN, battle=battle
    )

    reconstructed = resolved.party_at(vale)
    assert reconstructed.hero is survivors[0]
    assert reconstructed.units == survivors[1:]
    assert reconstructed.owner_id == "north"
    assert attacker.units[1] not in (reconstructed.hero, *reconstructed.units)
    assert resolved.settlement_at(vale).owner_id == "north"
    assert resolved.settlement_at(vale).garrison is garrison
    assert world.party_at(camp) is attacker
    assert world.settlement_at(vale) is settlement
    assert dict(battle.units) == battle_units_before


@pytest.mark.parametrize(
    "result", [BattleResult.DEFENDER_WIN, BattleResult.DRAW]
)
def test_apply_settlement_non_win_with_battle_removes_attacking_party(result):
    camp = Region("Camp")
    vale = Region("Vale")
    attacker = Party(Unit(), [Unit(), Unit(equipment=1)], "north")
    garrison = (Unit(training=1), Unit(), Unit(equipment=2))
    settlement = Settlement("Oakrest", 4, garrison=garrison, owner_id="south")
    world = WorldMap(
        [camp, vale],
        [(camp, vale)],
        settlements={vale: settlement},
        parties={camp: attacker},
    )
    battle = _battle_with_fallen_subordinates(
        attacker, Party(garrison[0], garrison[1:], "south")
    )

    resolved = world.apply_settlement_battle_result(
        camp, vale, result, battle=battle
    )

    assert resolved.party_at(camp) is None
    assert resolved.party_at(vale) is None
    assert resolved.settlement_at(vale) is settlement
    assert resolved.settlement_at(vale).garrison is garrison
