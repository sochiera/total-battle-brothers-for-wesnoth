"""Tests for the post-turn summary presentation primitive (tbbui)."""

from xml.etree import ElementTree as ET

from tbb.duchy import Duchy
from tbb.game import GameState
from tbb.settlement import Settlement
from tbb.unit import Unit
from tbbui.turnsummary import render_turn_summary


def test_render_turn_summary_empty_root_when_before_is_none():
    """When ``before is None``, return a bare empty root
    ``<div data-turn-summary=""></div>`` with no ``data-changed`` and no
    visible text. ``after`` is still required (current game state after the turn).
    """
    after = GameState(
        (
            Duchy("north", Unit()),
            Duchy("south", Unit()),
        )
    )

    xml = render_turn_summary(None, after)
    root = ET.fromstring(xml)

    assert root.tag == "div"
    assert root.attrib == {"data-turn-summary": ""}
    assert "data-changed" not in root.attrib
    assert root.text in (None, "")
    assert "".join(root.itertext()) == ""
    assert list(root) == []


def test_render_turn_summary_data_changed_from_settlements_or_has_hero():
    """When ``before`` is a ``GameState``, root carries ``data-changed`` and
    visible text matching whether any duchy (matched by ``duchy_id``) differs
    in ``len(settlements)`` or ``has_hero`` between ``before`` and ``after``.
    Pure and deterministic: same inputs → same string; does not mutate
    ``before`` or ``after``.
    """
    north_settlement = Settlement("North Keep", population=1, owner_id="north")
    before = GameState(
        (
            Duchy("north", Unit(), settlements=(north_settlement,)),
            Duchy("south", Unit()),
        )
    )
    before_duchies = before.duchies
    # Identical duchies → no change.
    after_same = GameState(
        (
            Duchy("north", Unit(), settlements=(north_settlement,)),
            Duchy("south", Unit()),
        )
    )
    after_same_duchies = after_same.duchies
    xml_same = render_turn_summary(before, after_same)
    root_same = ET.fromstring(xml_same)
    assert root_same.tag == "div"
    assert root_same.attrib["data-turn-summary"] == ""
    assert root_same.attrib["data-changed"] == "false"
    assert root_same.text == "Zmiany w tej turze: nie"
    assert render_turn_summary(before, after_same) == xml_same
    assert before.duchies is before_duchies
    assert after_same.duchies is after_same_duchies

    # Settlement count differs for north → change.
    after_settlements = GameState(
        (
            Duchy(
                "north",
                Unit(),
                settlements=(
                    north_settlement,
                    Settlement("New Village", population=1, owner_id="north"),
                ),
            ),
            Duchy("south", Unit()),
        )
    )
    after_settlements_duchies = after_settlements.duchies
    xml_settlements = render_turn_summary(before, after_settlements)
    root_settlements = ET.fromstring(xml_settlements)
    assert root_settlements.attrib["data-changed"] == "true"
    assert root_settlements.text == "Zmiany w tej turze: tak"
    assert before.duchies is before_duchies
    assert after_settlements.duchies is after_settlements_duchies

    # has_hero differs for south (hero → None) → change.
    after_hero = GameState(
        (
            Duchy("north", Unit(), settlements=(north_settlement,)),
            Duchy("south", None),
        )
    )
    after_hero_duchies = after_hero.duchies
    xml_hero = render_turn_summary(before, after_hero)
    root_hero = ET.fromstring(xml_hero)
    assert root_hero.attrib["data-changed"] == "true"
    assert root_hero.text == "Zmiany w tej turze: tak"
    assert before.duchies is before_duchies
    assert after_hero.duchies is after_hero_duchies


def test_render_turn_summary_per_duchy_rows_and_change_count():
    """When ``before`` is a ``GameState``, root carries ``data-change-count``
    (number of duchies matched by ``duchy_id`` that differ in
    ``(len(settlements), has_hero)``) and one child per changed duchy in
    ``after.duchies`` order: ``<div data-turn-duchy>`` with settlement and
    hero before/after attributes plus text
    ``<id>: osady A→B, bohater <tak|nie>→<tak|nie>``. Unchanged duchies emit
    no row. ``data-change-count`` equals the number of ``data-turn-duchy``
    children; ``data-changed="true"`` iff count > 0. Pure: does not mutate
    inputs; same inputs → same string.
    """
    north_keep = Settlement("North Keep", population=1, owner_id="north")
    mid_keep = Settlement("Mid Keep", population=1, owner_id="mid")
    before = GameState(
        (
            Duchy("north", Unit(), settlements=(north_keep,)),
            Duchy("mid", Unit(), settlements=(mid_keep,)),
            Duchy("south", Unit()),
        )
    )
    before_duchies = before.duchies

    # No differences → count 0, no children, data-changed false.
    after_same = GameState(
        (
            Duchy("north", Unit(), settlements=(north_keep,)),
            Duchy("mid", Unit(), settlements=(mid_keep,)),
            Duchy("south", Unit()),
        )
    )
    after_same_duchies = after_same.duchies
    xml_same = render_turn_summary(before, after_same)
    root_same = ET.fromstring(xml_same)
    assert root_same.attrib["data-change-count"] == "0"
    assert root_same.attrib["data-changed"] == "false"
    assert root_same.findall("*[@data-turn-duchy]") == []
    assert list(root_same) == []
    assert render_turn_summary(before, after_same) == xml_same
    assert before.duchies is before_duchies
    assert after_same.duchies is after_same_duchies

    # north gains a settlement; south loses hero; mid unchanged.
    # Children follow after.duchies order: north then south (mid skipped).
    after_mixed = GameState(
        (
            Duchy(
                "north",
                Unit(),
                settlements=(
                    north_keep,
                    Settlement("New Village", population=1, owner_id="north"),
                ),
            ),
            Duchy("mid", Unit(), settlements=(mid_keep,)),
            Duchy("south", None),
        )
    )
    after_mixed_duchies = after_mixed.duchies
    xml_mixed = render_turn_summary(before, after_mixed)
    root_mixed = ET.fromstring(xml_mixed)
    rows = root_mixed.findall("*[@data-turn-duchy]")
    assert root_mixed.attrib["data-change-count"] == "2"
    assert root_mixed.attrib["data-changed"] == "true"
    assert len(rows) == 2
    assert int(root_mixed.attrib["data-change-count"]) == len(rows)

    north_row, south_row = rows
    assert north_row.attrib == {
        "data-turn-duchy": "north",
        "data-settlements-before": "1",
        "data-settlements-after": "2",
        "data-hero-before": "true",
        "data-hero-after": "true",
    }
    assert north_row.text == "north: osady 1→2, bohater tak→tak"

    assert south_row.attrib == {
        "data-turn-duchy": "south",
        "data-settlements-before": "0",
        "data-settlements-after": "0",
        "data-hero-before": "true",
        "data-hero-after": "false",
    }
    assert south_row.text == "south: osady 0→0, bohater tak→nie"

    assert [r.attrib["data-turn-duchy"] for r in rows] == ["north", "south"]
    assert before.duchies is before_duchies
    assert after_mixed.duchies is after_mixed_duchies
    assert render_turn_summary(before, after_mixed) == xml_mixed
