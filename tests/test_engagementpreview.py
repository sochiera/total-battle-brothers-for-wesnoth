"""Tests for the engagement-preview presentation primitive (tbbui)."""

from xml.etree import ElementTree as ET

from tbb.duchy import Duchy
from tbb.game import GameState
from tbb.party import Party
from tbb.unit import Unit
from tbb.world import Region, WorldMap
from tbbui.engagementpreview import render_engagement_preview


def test_render_engagement_preview_empty_root_when_none_or_unknown_duchy():
    """When ``player_duchy_id`` is ``None`` or not in ``game.duchies``, return
    a bare empty root ``<div data-engagement-preview=""></div>`` with no
    ``data-player-on-map``, no ``data-own-*``, no child rows, and no visible
    text. Does not depend on world parties or settlements.
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
        xml = render_engagement_preview(
            world, game, player_duchy_id=player_duchy_id
        )
        root = ET.fromstring(xml)

        assert root.tag == "div"
        assert root.attrib == {"data-engagement-preview": ""}
        assert "data-player-on-map" not in root.attrib
        assert "data-own-hp" not in root.attrib
        assert "data-own-attack" not in root.attrib
        assert "data-own-defense" not in root.attrib
        assert list(root) == []
        assert "".join(root.itertext()) == ""
