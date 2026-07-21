"""Tests for the hero-chase presentation primitive (tbbui)."""

from xml.etree import ElementTree as ET

from tbb.duchy import Duchy
from tbb.game import GameState
from tbb.party import Party
from tbb.unit import Unit
from tbb.world import Region, WorldMap
from tbbui.herochase import render_hero_chase


def test_render_hero_chase_empty_root_when_none_or_unknown_duchy():
    """When ``player_duchy_id`` is ``None`` or not in ``game.duchies``, return
    a bare empty root ``<div data-hero-chase=""></div>`` with no
    ``data-player-on-map``, no child rows, and no visible text. Does not
    depend on world parties.
    """
    a = Region("A")
    world = WorldMap(
        [a],
        [],
        parties={a: Party(hero=Unit(), units=(), owner_id="south")},
    )
    game = GameState(
        (
            Duchy("north", Unit()),
            Duchy("south", Unit()),
        )
    )

    for player_duchy_id in (None, "missing"):
        xml = render_hero_chase(
            world, game, player_duchy_id=player_duchy_id
        )
        root = ET.fromstring(xml)

        assert root.tag == "div"
        assert root.attrib == {"data-hero-chase": ""}
        assert "data-player-on-map" not in root.attrib
        assert list(root) == []
        assert "".join(root.itertext()) == ""
