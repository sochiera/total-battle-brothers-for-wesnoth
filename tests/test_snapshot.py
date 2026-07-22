"""Tests for the tbbbridge settlement snapshot (G63.1a)."""

import copy
import json

from tbb import BARRACKS, FARM, MARKET, Resources, Settlement, Unit
from tbbbridge.snapshot import settlement_state


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
