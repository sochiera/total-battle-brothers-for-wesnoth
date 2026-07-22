"""Tests for the economy-alert presentation primitive (tbbui)."""

import html
from xml.etree import ElementTree as ET

from tbb.building import FARM
from tbb.duchy import Duchy
from tbb.game import GameState
from tbb.resources import Resources
from tbb.settlement import Settlement
from tbb.unit import Unit
from tbbui.economyalert import render_economy_alert


def test_render_economy_alert_empty_root_when_none_or_unknown_duchy():
    """When ``player_duchy_id`` is ``None`` or not in ``game.duchies``
    (``player_duchy(...) is None``), return a bare empty root
    ``<div data-economy-alert=""></div>`` with no ``data-starving-settlements``,
    no children, and no visible text. Pure: no game mutation. Does not depend
    on whether duchies hold starving settlements.
    """
    starving = Settlement(
        "Starving",
        population=5,
        occupied=1,
        owner_id="north",
        storage=Resources(wheat=0, gold=0),
        active_buildings=(FARM,),
    )
    assert starving.consumption.wheat > starving.production.wheat

    game = GameState(
        (
            Duchy(
                "north",
                Unit(),
                settlements=(starving,),
                parties=(),
            ),
            Duchy("south", Unit(), settlements=(), parties=()),
        )
    )
    duchies_before = game.duchies
    storage_before = tuple(s.storage for s in game.duchies[0].settlements)

    for player_duchy_id in (None, "missing"):
        xml = render_economy_alert(game, player_duchy_id=player_duchy_id)
        root = ET.fromstring(xml)

        assert root.tag == "div"
        assert root.attrib == {"data-economy-alert": ""}
        assert "data-starving-settlements" not in root.attrib
        assert list(root) == []
        assert "".join(root.itertext()) == ""

    assert game.duchies == duchies_before
    assert game.duchies is duchies_before
    assert (
        tuple(s.storage for s in game.duchies[0].settlements) == storage_before
    )


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


def test_render_economy_alert_visible_text_matches_starving_count():
    """When ``player_duchy_id`` matches a duchy, the root carries visible text
    ``Osady na deficycie pszenicy: N`` where ``N`` equals
    ``data-starving-settlements`` (count of settlements with
    ``consumption.wheat > production.wheat``). Pure: no game mutation.
    """
    starving = Settlement(
        "Starving Farm",
        population=5,
        occupied=1,
        owner_id="north",
        storage=Resources(wheat=1, gold=0),
        active_buildings=(FARM,),
    )
    surplus = Settlement(
        "Surplus Keep",
        population=1,
        occupied=1,
        owner_id="north",
        storage=Resources(wheat=10, gold=0),
        active_buildings=(FARM,),
    )
    no_farm = Settlement(
        "Hungry Hamlet",
        population=2,
        owner_id="north",
        storage=Resources(wheat=0, gold=0),
    )
    assert starving.consumption.wheat > starving.production.wheat
    assert not (surplus.consumption.wheat > surplus.production.wheat)
    assert no_farm.consumption.wheat > no_farm.production.wheat

    game = GameState(
        (
            Duchy(
                "north",
                Unit(),
                settlements=(starving, surplus, no_farm),
                parties=(),
            ),
        )
    )
    duchies_before = game.duchies
    storage_before = tuple(s.storage for s in game.duchies[0].settlements)

    expected_n = 2  # starving + no_farm

    xml = render_economy_alert(game, player_duchy_id="north")
    root = ET.fromstring(xml)

    assert root.attrib.get("data-starving-settlements") == str(expected_n)
    # Header text only (direct root text); row bodies are covered by K61.1b.
    assert root.text == f"Osady na deficycie pszenicy: {expected_n}"

    assert game.duchies == duchies_before
    assert game.duchies is duchies_before
    assert (
        tuple(s.storage for s in game.duchies[0].settlements) == storage_before
    )


def test_render_economy_alert_starving_settlement_rows_with_deficit():
    """When ``player_duchy_id`` matches a duchy, the root has one child
    ``<div data-starving-settlement="<name>" data-wheat-deficit="D"></div>``
    per settlement with ``consumption.wheat > production.wheat``, in
    ``duchy.settlements`` order, where ``D = consumption.wheat -
    production.wheat`` (positive). Settlements with
    ``consumption.wheat <= production.wheat`` produce no row. Other duchies
    ignored. Pure: no game mutation.
    """
    # starving: cons 5 > prod 3 → D=2
    starving_farm = Settlement(
        "Starving Farm",
        population=5,
        occupied=1,
        owner_id="north",
        storage=Resources(wheat=1, gold=0),
        active_buildings=(FARM,),
    )
    # surplus: cons 1 < prod 3 — no row
    surplus = Settlement(
        "Surplus Keep",
        population=1,
        occupied=1,
        owner_id="north",
        storage=Resources(wheat=10, gold=0),
        active_buildings=(FARM,),
    )
    # balanced: cons 3 == prod 3 — no row (strict >)
    balanced = Settlement(
        "Balanced",
        population=3,
        occupied=1,
        owner_id="north",
        storage=Resources(wheat=1, gold=0),
        active_buildings=(FARM,),
    )
    # starving no farm: cons 2 > prod 0 → D=2
    no_farm = Settlement(
        "Hungry Hamlet",
        population=2,
        owner_id="north",
        storage=Resources(wheat=0, gold=0),
    )
    # other duchy starving — must not appear
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

    d_farm = (
        starving_farm.consumption.wheat - starving_farm.production.wheat
    )
    d_no_farm = no_farm.consumption.wheat - no_farm.production.wheat
    assert d_farm > 0
    assert d_no_farm > 0

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

    xml = render_economy_alert(game, player_duchy_id="north")
    root = ET.fromstring(xml)

    children = list(root)
    assert len(children) == 2
    expected_rows = (
        ("Starving Farm", str(d_farm)),
        ("Hungry Hamlet", str(d_no_farm)),
    )
    for child, (name, deficit) in zip(children, expected_rows, strict=True):
        assert child.tag == "div"
        assert child.attrib == {
            "data-starving-settlement": name,
            "data-wheat-deficit": deficit,
        }
        assert list(child) == []
        # Visible row body is specified by K61.1b
        # (test_render_economy_alert_starving_row_visible_text_matches_attrs).

    assert game.duchies == duchies_before
    assert game.duchies is duchies_before
    assert (
        tuple(s.storage for s in game.duchies[0].settlements) == storage_before
    )


def test_render_economy_alert_starving_row_visible_text_matches_attrs():
    """Each ``data-starving-settlement`` child carries visible body text
    ``<name>: deficyt D pszenicy/mies.`` consistent with attributes
    ``data-starving-settlement`` (name) and ``data-wheat-deficit`` (D). Pure:
    no game mutation.
    """
    # starving: cons 5 > prod 3 → D=2
    starving_farm = Settlement(
        "Starving Farm",
        population=5,
        occupied=1,
        owner_id="north",
        storage=Resources(wheat=1, gold=0),
        active_buildings=(FARM,),
    )
    # surplus: no row
    surplus = Settlement(
        "Surplus Keep",
        population=1,
        occupied=1,
        owner_id="north",
        storage=Resources(wheat=10, gold=0),
        active_buildings=(FARM,),
    )
    # starving no farm: cons 2 > prod 0 → D=2
    no_farm = Settlement(
        "Hungry Hamlet",
        population=2,
        owner_id="north",
        storage=Resources(wheat=0, gold=0),
    )

    assert starving_farm.consumption.wheat > starving_farm.production.wheat
    assert not (surplus.consumption.wheat > surplus.production.wheat)
    assert no_farm.consumption.wheat > no_farm.production.wheat

    d_farm = (
        starving_farm.consumption.wheat - starving_farm.production.wheat
    )
    d_no_farm = no_farm.consumption.wheat - no_farm.production.wheat
    assert d_farm > 0
    assert d_no_farm > 0

    game = GameState(
        (
            Duchy(
                "north",
                Unit(),
                settlements=(starving_farm, surplus, no_farm),
                parties=(),
            ),
        )
    )
    duchies_before = game.duchies
    storage_before = tuple(s.storage for s in game.duchies[0].settlements)

    xml = render_economy_alert(game, player_duchy_id="north")
    root = ET.fromstring(xml)

    children = list(root)
    assert len(children) == 2
    expected_rows = (
        ("Starving Farm", str(d_farm)),
        ("Hungry Hamlet", str(d_no_farm)),
    )
    for child, (name, deficit) in zip(children, expected_rows, strict=True):
        assert child.attrib.get("data-starving-settlement") == name
        assert child.attrib.get("data-wheat-deficit") == deficit
        assert "".join(child.itertext()) == (
            f"{name}: deficyt {deficit} pszenicy/mies."
        )

    assert game.duchies == duchies_before
    assert game.duchies is duchies_before
    assert (
        tuple(s.storage for s in game.duchies[0].settlements) == storage_before
    )


def test_render_economy_alert_escapes_settlement_name_in_attribute():
    """``data-starving-settlement`` uses ``html.escape(name, quote=True)`` so
    names with XML-special characters (``"``, ``&``, ``<``) keep the fragment
    parsable. ElementTree attribute value equals the original name; raw
    fragment contains the escaped form. Pure: no game mutation.
    """
    special_name = 'Hamlet "A" & B <C>'
    starving = Settlement(
        special_name,
        population=2,
        owner_id="north",
        storage=Resources(wheat=0, gold=0),
    )
    assert starving.consumption.wheat > starving.production.wheat
    deficit = starving.consumption.wheat - starving.production.wheat
    assert deficit > 0

    game = GameState(
        (
            Duchy(
                "north",
                Unit(),
                settlements=(starving,),
                parties=(),
            ),
        )
    )
    duchies_before = game.duchies
    storage_before = tuple(s.storage for s in game.duchies[0].settlements)

    escaped = html.escape(special_name, quote=True)
    xml = render_economy_alert(game, player_duchy_id="north")
    assert f'data-starving-settlement="{escaped}"' in xml

    root = ET.fromstring(xml)
    children = list(root)
    assert len(children) == 1
    assert children[0].attrib == {
        "data-starving-settlement": special_name,
        "data-wheat-deficit": str(deficit),
    }

    assert game.duchies == duchies_before
    assert game.duchies is duchies_before
    assert (
        tuple(s.storage for s in game.duchies[0].settlements) == storage_before
    )


def test_render_economy_alert_total_wheat_deficit_on_root():
    """When ``player_duchy_id`` matches a duchy, root carries
    ``data-total-wheat-deficit="D"`` immediately after
    ``data-starving-settlements``, where ``D`` is the sum of
    ``(consumption.wheat - production.wheat)`` over settlements with
    ``consumption.wheat > production.wheat`` (``0`` when none starve).
    Attribute order on the root: ``data-economy-alert``,
    ``data-starving-settlements``, ``data-total-wheat-deficit``. Pure: no
    game mutation.
    """
    # starving: cons 5 > prod 3 → d=2
    starving_farm = Settlement(
        "Starving Farm",
        population=5,
        occupied=1,
        owner_id="north",
        storage=Resources(wheat=1, gold=0),
        active_buildings=(FARM,),
    )
    # surplus: not counted
    surplus = Settlement(
        "Surplus Keep",
        population=1,
        occupied=1,
        owner_id="north",
        storage=Resources(wheat=10, gold=0),
        active_buildings=(FARM,),
    )
    # balanced: not counted (strict >)
    balanced = Settlement(
        "Balanced",
        population=3,
        occupied=1,
        owner_id="north",
        storage=Resources(wheat=1, gold=0),
        active_buildings=(FARM,),
    )
    # starving no farm: cons 2 > prod 0 → d=2
    no_farm = Settlement(
        "Hungry Hamlet",
        population=2,
        owner_id="north",
        storage=Resources(wheat=0, gold=0),
    )
    # other duchy starving — must not contribute
    other = Settlement(
        "South Keep",
        population=99,
        owner_id="south",
        storage=Resources(wheat=0, gold=0),
    )

    d_farm = (
        starving_farm.consumption.wheat - starving_farm.production.wheat
    )
    d_no_farm = no_farm.consumption.wheat - no_farm.production.wheat
    assert d_farm > 0
    assert d_no_farm > 0
    expected_total = d_farm + d_no_farm
    expected_n = 2

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

    xml = render_economy_alert(game, player_duchy_id="north")
    root = ET.fromstring(xml)

    assert root.tag == "div"
    assert list(root.attrib.keys()) == [
        "data-economy-alert",
        "data-starving-settlements",
        "data-total-wheat-deficit",
    ]
    assert root.attrib["data-economy-alert"] == ""
    assert root.attrib["data-starving-settlements"] == str(expected_n)
    assert root.attrib["data-total-wheat-deficit"] == str(expected_total)

    # Zero-deficit case: known player, no starving settlements → D=0
    full_only = GameState(
        (
            Duchy(
                "north",
                Unit(),
                settlements=(surplus, balanced),
                parties=(),
            ),
        )
    )
    xml_zero = render_economy_alert(full_only, player_duchy_id="north")
    root_zero = ET.fromstring(xml_zero)
    assert list(root_zero.attrib.keys()) == [
        "data-economy-alert",
        "data-starving-settlements",
        "data-total-wheat-deficit",
    ]
    assert root_zero.attrib["data-starving-settlements"] == "0"
    assert root_zero.attrib["data-total-wheat-deficit"] == "0"

    assert game.duchies == duchies_before
    assert game.duchies is duchies_before
    assert (
        tuple(s.storage for s in game.duchies[0].settlements) == storage_before
    )
