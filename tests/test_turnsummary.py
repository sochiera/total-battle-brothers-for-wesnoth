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
