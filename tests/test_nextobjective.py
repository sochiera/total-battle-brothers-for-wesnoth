"""Tests for the next-objective presentation primitive (tbbui)."""

from xml.etree import ElementTree as ET

from tbb.duchy import Duchy
from tbb.game import GameState
from tbb.settlement import Settlement
from tbb.unit import Unit
from tbbui.nextobjective import render_next_objective


def _assert_root_attr_matches_body(root: ET.Element) -> str:
    """Contract: root is ``<p>``, attribute and body are identical characters."""
    assert root.tag == "p"
    assert "data-next-objective" in root.attrib
    body = root.text or ""
    attr = root.attrib["data-next-objective"]
    assert attr == body
    assert "".join(root.itertext()) == body
    return body


def test_render_next_objective_empty_root_when_none_or_unknown_duchy():
    """When ``player_duchy_id`` is ``None`` or not in ``game.duchies``, return
    empty root ``<p data-next-objective=""></p>`` — attribute and body both
    empty, same characters.
    """
    game = GameState(
        (
            Duchy(
                "north",
                Unit(),
                settlements=(
                    Settlement("North Keep", population=1, owner_id="north"),
                ),
            ),
            Duchy("south", Unit()),
        )
    )

    for player_duchy_id in (None, "missing"):
        xml = render_next_objective(game, player_duchy_id=player_duchy_id)
        root = ET.fromstring(xml)

        assert root.tag == "p"
        assert root.attrib == {"data-next-objective": ""}
        assert root.text in (None, "")
        assert "".join(root.itertext()) == ""
        # Attribute and body are the same empty string (contract root shape).
        assert root.attrib["data-next-objective"] == (root.text or "")


def test_render_next_objective_all_enemies_defeated():
    """When no undefeated enemy remains (every other duchy is ``is_defeated``),
    text is ``Cel osiągnięty: wszyscy wrogowie pokonani``. Attribute equals body.
    """
    # player: north (alive); only enemy west is defeated (no hero, no settlements)
    game = GameState(
        (
            Duchy(
                "north",
                Unit(),
                settlements=(
                    Settlement("North Keep", population=1, owner_id="north"),
                ),
            ),
            Duchy("west", None),
        )
    )
    expected = "Cel osiągnięty: wszyscy wrogowie pokonani"

    xml = render_next_objective(game, player_duchy_id="north")
    root = ET.fromstring(xml)
    body = _assert_root_attr_matches_body(root)
    assert body == expected


def test_render_next_objective_remaining_enemy_settlements():
    """When an undefeated enemy has settlements, text is
    ``Odbierz wrogie osady (pozostało: S)`` with ``S`` = sum of
    ``len(duchy.settlements)`` over undefeated enemies. Pure: does not mutate
    ``game``.
    """
    # undefeated enemies: south (2 settlements), east (1); west defeated → S = 3
    game = GameState(
        (
            Duchy("north", Unit()),
            Duchy(
                "south",
                Unit(),
                settlements=(
                    Settlement("South Keep", population=1, owner_id="south"),
                    Settlement("South Port", population=1, owner_id="south"),
                ),
            ),
            Duchy(
                "east",
                None,
                settlements=(
                    Settlement("East Keep", population=1, owner_id="east"),
                ),
            ),
            Duchy("west", None),
        )
    )
    duchies_before = game.duchies
    expected_s = 3
    expected = f"Odbierz wrogie osady (pozostało: {expected_s})"

    xml = render_next_objective(game, player_duchy_id="north")
    root = ET.fromstring(xml)
    body = _assert_root_attr_matches_body(root)
    assert body == expected

    assert game.duchies == duchies_before
    assert game.duchies is duchies_before


def test_render_next_objective_finish_enemy_heroes_when_no_settlements():
    """When undefeated enemies remain but their settlement sum is 0, text is
    ``Dobij wrogich bohaterów (pozostało: H)`` with ``H`` = count of undefeated
    enemies that ``has_hero``.
    """
    # undefeated enemies with 0 settlements: south (hero), east (hero);
    # west defeated → H = 2
    game = GameState(
        (
            Duchy("north", Unit()),
            Duchy("south", Unit()),
            Duchy("east", Unit()),
            Duchy("west", None),
        )
    )
    expected_h = 2
    expected = f"Dobij wrogich bohaterów (pozostało: {expected_h})"

    xml = render_next_objective(game, player_duchy_id="north")
    root = ET.fromstring(xml)
    body = _assert_root_attr_matches_body(root)
    assert body == expected
