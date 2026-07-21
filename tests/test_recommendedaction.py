"""Tests for the recommended-action presentation primitive (tbbui)."""

from xml.etree import ElementTree as ET

from tbb.duchy import Duchy
from tbb.game import GameState
from tbb.party import Party
from tbb.unit import Unit
from tbb.world import Region, WorldMap
from tbbui.recommendedaction import render_recommended_action


def test_render_recommended_action_empty_root_when_none_or_unknown_duchy():
    """When ``player_duchy_id`` is ``None`` or not in ``game.duchies``
    (``player_duchy(...) is None``), return a bare empty root
    ``<div data-recommended-action=""></div>`` with no ``data-posture``, no
    visible text, and no children. Does not depend on world parties or
    settlements.
    """
    a = Region("A")
    b = Region("B")
    world = WorldMap(
        [a, b],
        [(a, b)],
        parties={
            a: Party(hero=Unit(), units=(), owner_id="south"),
        },
        settlements={},
    )
    game = GameState(
        (
            Duchy("north", Unit()),
            Duchy("south", Unit()),
        )
    )

    for player_duchy_id in (None, "missing"):
        xml = render_recommended_action(
            world, game, player_duchy_id=player_duchy_id
        )
        root = ET.fromstring(xml)

        assert root.tag == "div"
        assert root.attrib == {"data-recommended-action": ""}
        assert "data-posture" not in root.attrib
        assert list(root) == []
        assert "".join(root.itertext()) == ""
