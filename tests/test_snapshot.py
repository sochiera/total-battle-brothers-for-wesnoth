"""Tests for the tbbbridge state snapshots (G63.1a / G63.1b)."""

import copy
import json

import tbbui.unitstrength
from tbb import BRUISE, BARRACKS, FARM, MARKET, Resources, Settlement, Unit
from tbb.party import Party
from tbb.world import Region, WorldMap
from tbbbridge.snapshot import party_state, settlement_state
from tbbui.layout import layout_world


def _sample_settlement() -> Settlement:
    """A settlement exercising every snapshot field with distinct values."""
    garrison = (Unit(), Unit())
    return Settlement(
        name="Riverford",
        population=10,
        occupied=0,
        active_buildings=(FARM, MARKET, BARRACKS),
        storage=Resources(wheat=7, gold=3),
        capacity=12,
        garrison=garrison,
        owner_id="north",
    )


def test_settlement_state_returns_pure_json_serializable_dict_with_contract_keys_and_values():
    expected_keys = [
        "name",
        "owner",
        "wheat",
        "gold",
        "population",
        "free",
        "garrison",
        "buildings",
        "wheat_production",
        "gold_production",
        "wheat_consumption",
    ]
    settlement = _sample_settlement()
    before = copy.deepcopy(settlement)

    state = settlement_state(settlement)

    # Contract: exact key set in the prescribed order.
    assert list(state.keys()) == expected_keys
    # Contract: value sources from the settlement's public API.
    assert state["name"] == settlement.name
    assert state["owner"] == settlement.owner_id
    assert state["wheat"] == settlement.storage.wheat
    assert state["gold"] == settlement.storage.gold
    assert state["population"] == settlement.population
    assert state["free"] == settlement.free
    assert state["garrison"] == len(settlement.garrison)
    assert state["buildings"] == [b.name for b in settlement.active_buildings]
    assert state["wheat_production"] == settlement.production.wheat
    assert state["gold_production"] == settlement.production.gold
    assert state["wheat_consumption"] == settlement.consumption.wheat
    # Contract: result must be json-serializable.
    assert json.dumps(state, sort_keys=True) is not None
    # Contract: the settlement must not be mutated by the call.
    assert settlement == before


def test_settlement_state_owner_none_is_preserved_and_json_serializable():
    settlement = Settlement("Wild", population=1, owner_id=None)
    state = settlement_state(settlement)
    assert state["owner"] is None
    # None must round-trip through json (as null) without raising.
    json.dumps(state)


def _sample_party() -> Party:
    """A party with a hero, subordinates, a wounded member, and a real owner."""
    hero = Unit(training=2, equipment=1, experience=1)
    healthy = Unit(training=1, equipment=0, experience=1)
    wounded = Unit(training=0, equipment=1, experience=0, wounds=(BRUISE,))
    return Party(hero=hero, units=(healthy, wounded), owner_id="north")


def test_party_state_returns_pure_json_serializable_dict_with_contract_keys_and_values():
    expected_keys = ["owner", "size", "hp", "attack", "defense", "wounded"]
    party = _sample_party()
    before = copy.deepcopy(party)

    state = party_state(party)

    # Contract: exact key set in the prescribed order.
    assert list(state.keys()) == expected_keys
    # Contract: value sources from the party's public API and unitstrength.
    roster = (party.hero, *party.units)
    hp, attack, defense = tbbui.unitstrength.combat_totals(roster)
    assert state["owner"] == party.owner_id
    assert state["size"] == len(party.units)
    assert state["hp"] == hp
    assert state["attack"] == attack
    assert state["defense"] == defense
    assert state["wounded"] == tbbui.unitstrength.wounded_count(roster)
    # Contract: result must be json-serializable.
    json.dumps(state)
    # Contract: the party must not be mutated by the call (byte-for-byte equal).
    assert party == before


def test_party_state_owner_none_is_preserved_and_json_serializable():
    party = Party(Unit(), owner_id=None)
    state = party_state(party)
    assert state["owner"] is None
    # None must round-trip through json (as null) without raising.
    json.dumps(state)


def _map_world() -> WorldMap:
    """A world exercising settlement-only, party-only, empty and contested
    (both settlement + party) regions across a linear graph."""
    north = Region("Northkeep")
    wild = Region("Wilds")
    empty = Region("Empty")
    contested = Region("Contested")
    settlement = Settlement(
        name="Northkeep",
        population=4,
        owner_id="north",
        storage=Resources(wheat=1, gold=1),
        garrison=(Unit(),),
        active_buildings=(FARM,),
    )
    contested_settlement = Settlement(
        name="Contested",
        population=2,
        owner_id="crown",
        storage=Resources(wheat=0, gold=0),
        garrison=(),
        active_buildings=(),
    )
    party = Party(Unit(), owner_id="rebels")
    rebel_party = Party(Unit(training=1), owner_id="rebels")
    return WorldMap(
        regions=(north, wild, empty, contested),
        connections=((north, wild), (wild, empty), (empty, contested)),
        settlements={north: settlement, contested: contested_settlement},
        parties={wild: party, contested: rebel_party},
    )


def test_map_state_returns_pure_json_serializable_dict_with_contract_keys_and_values():
    from tbbbridge.snapshot import map_state

    world = _map_world()
    before = world

    state = map_state(world)

    # Contract: top-level keys exactly in order regions, connections.
    assert list(state.keys()) == ["regions", "connections"]

    positions = layout_world(world)
    north, wild, empty, contested = world.regions

    # Contract: regions list mirrors world.regions order; each entry has the
    # prescribed key order and values sourced from region / layout / snapshots.
    assert [r["name"] for r in state["regions"]] == [r.name for r in world.regions]
    assert list(state["regions"][0].keys()) == [
        "name",
        "col",
        "row",
        "owner",
        "settlement",
        "party",
    ]

    north_entry = state["regions"][0]
    assert north_entry["name"] == north.name
    assert (north_entry["col"], north_entry["row"]) == positions[north]
    # owner falls back to the settlement owner when a settlement is present.
    assert north_entry["owner"] == "north"
    assert north_entry["settlement"] == settlement_state(world.settlement_at(north))
    assert north_entry["party"] is None

    wild_entry = state["regions"][1]
    # No settlement -> owner falls back to the party owner.
    assert wild_entry["owner"] == "rebels"
    assert wild_entry["settlement"] is None
    assert wild_entry["party"] == party_state(world.party_at(wild))

    empty_entry = state["regions"][2]
    # Neither settlement nor party -> owner is None.
    assert empty_entry["owner"] is None
    assert empty_entry["settlement"] is None
    assert empty_entry["party"] is None

    contested_entry = state["regions"][3]
    # Both present -> settlement owner wins over party owner.
    assert contested_entry["owner"] == "crown"
    assert contested_entry["settlement"] == settlement_state(
        world.settlement_at(contested)
    )
    assert contested_entry["party"] == party_state(world.party_at(contested))

    # Contract: connections mirror world.connections order using region names.
    assert state["connections"] == [
        {"from": "Northkeep", "to": "Wilds"},
        {"from": "Wilds", "to": "Empty"},
        {"from": "Empty", "to": "Contested"},
    ]

    # Contract: the whole result is json-serializable and world is not mutated.
    json.dumps(state)
    assert world is before
