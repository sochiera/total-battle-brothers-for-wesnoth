"""Tests for the next-objective presentation primitive (tbbui)."""

from xml.etree import ElementTree as ET

from tbb.duchy import Duchy
from tbb.game import GameState
from tbb.settlement import Settlement
from tbb.unit import Unit
from tbbui.nextobjective import render_next_objective


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
