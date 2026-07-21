"""Tests for the victory progress presentation primitive (tbbui)."""

from xml.etree import ElementTree as ET

from tbb.duchy import Duchy
from tbb.game import GameState
from tbb.settlement import Settlement
from tbb.unit import Unit
from tbbui.victoryprogress import render_victory_progress


def test_render_victory_progress_counts_undefeated_enemies_and_is_pure():
    """When ``player_duchy_id`` matches a duchy in ``game.duchies``, the root is
    ``<div data-victory-progress="">`` with ``data-enemies-remaining="N"`` where
    ``N`` is the number of other duchies that are not ``is_defeated``, and
    visible text ``Wrogów do pokonania: N``. Defeated enemies are excluded.
    Pure: does not mutate ``game``.
    """
    # player: north (has hero + settlement → not defeated, not counted as enemy)
    # undefeated enemies: south (hero), east (settlement only)
    # defeated enemy: west (no hero, no settlements) — must not count
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
    # south + east undefeated; west defeated → N = 2
    expected_n = 2

    xml = render_victory_progress(game, player_duchy_id="north")
    root = ET.fromstring(xml)

    assert root.tag == "div"
    assert root.attrib.get("data-victory-progress") == ""
    assert root.attrib["data-enemies-remaining"] == str(expected_n)
    assert "".join(root.itertext()) == f"Wrogów do pokonania: {expected_n}"

    assert game.duchies == duchies_before
    assert game.duchies is duchies_before


def test_render_victory_progress_empty_root_when_none_or_unknown_duchy():
    """When ``player_duchy_id`` is ``None`` or not in ``game.duchies``, return
    a bare empty root ``<div data-victory-progress=""></div>`` with no
    ``data-enemies-remaining`` and no visible text.
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
        xml = render_victory_progress(game, player_duchy_id=player_duchy_id)
        root = ET.fromstring(xml)

        assert root.tag == "div"
        assert root.attrib == {"data-victory-progress": ""}
        assert "".join(root.itertext()) == ""
        assert "data-enemies-remaining" not in root.attrib
