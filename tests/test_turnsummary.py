"""Tests for the post-turn summary presentation primitive (tbbui)."""

from xml.etree import ElementTree as ET

from tbb.duchy import Duchy
from tbb.game import GameState
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
