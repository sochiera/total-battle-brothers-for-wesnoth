"""Tests for the economy-alert presentation primitive (tbbui)."""

from xml.etree import ElementTree as ET

from tbb.building import FARM
from tbb.duchy import Duchy
from tbb.game import GameState
from tbb.resources import Resources
from tbb.settlement import Settlement
from tbb.unit import Unit
from tbbui.economyalert import render_economy_alert


def test_render_economy_alert_counts_starving_settlements_for_known_player():
    """When ``player_duchy_id`` matches a duchy, root is
    ``<div data-economy-alert="">`` with ``data-starving-settlements="N"``
    where ``N`` is the number of ``duchy.settlements`` with
    ``consumption.wheat > production.wheat``. Other duchies ignored. Strict
    greater-than (equal wheat balance does not count). Pure: no game mutation.
    """
    # starving: cons 5 > prod 3
    starving_farm = Settlement(
        "Starving Farm",
        population=5,
        occupied=1,
        owner_id="north",
        storage=Resources(wheat=1, gold=0),
        active_buildings=(FARM,),
    )
    # surplus: cons 1 < prod 3 — not starving
    surplus = Settlement(
        "Surplus Keep",
        population=1,
        occupied=1,
        owner_id="north",
        storage=Resources(wheat=10, gold=0),
        active_buildings=(FARM,),
    )
    # balanced: cons 3 == prod 3 — not starving (strict >)
    balanced = Settlement(
        "Balanced",
        population=3,
        occupied=1,
        owner_id="north",
        storage=Resources(wheat=1, gold=0),
        active_buildings=(FARM,),
    )
    # starving no farm: cons 2 > prod 0
    no_farm = Settlement(
        "Hungry Hamlet",
        population=2,
        owner_id="north",
        storage=Resources(wheat=0, gold=0),
    )
    # other duchy starving — must not count
    other = Settlement(
        "South Keep",
        population=99,
        owner_id="south",
        storage=Resources(wheat=0, gold=0),
    )

    assert starving_farm.consumption.wheat > starving_farm.production.wheat
    assert not (surplus.consumption.wheat > surplus.production.wheat)
    assert not (balanced.consumption.wheat > balanced.production.wheat)
    assert no_farm.consumption.wheat > no_farm.production.wheat
    assert other.consumption.wheat > other.production.wheat

    game = GameState(
        (
            Duchy(
                "north",
                Unit(),
                settlements=(starving_farm, surplus, balanced, no_farm),
                parties=(),
            ),
            Duchy(
                "south",
                Unit(),
                settlements=(other,),
                parties=(),
            ),
        )
    )
    duchies_before = game.duchies
    storage_before = tuple(s.storage for s in game.duchies[0].settlements)

    expected_n = 2  # starving_farm + no_farm

    xml = render_economy_alert(game, player_duchy_id="north")
    root = ET.fromstring(xml)

    assert root.tag == "div"
    assert root.attrib.get("data-economy-alert") == ""
    assert root.attrib.get("data-starving-settlements") == str(expected_n)

    assert game.duchies == duchies_before
    assert game.duchies is duchies_before
    assert (
        tuple(s.storage for s in game.duchies[0].settlements) == storage_before
    )
