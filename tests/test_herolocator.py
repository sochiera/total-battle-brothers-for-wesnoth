"""Tests for the enemy-hero locator presentation primitive (tbbui)."""

from xml.etree import ElementTree as ET

from tbb.duchy import Duchy
from tbb.game import GameState
from tbb.party import Party
from tbb.unit import Unit
from tbb.world import Region, WorldMap
from tbbui.herolocator import render_enemy_hero_locator


def test_render_enemy_hero_locator_empty_root_when_none_or_unknown_duchy():
    """When ``player_duchy_id`` is ``None`` or not in ``game.duchies``, return
    a bare empty root ``<div data-hero-locator=""></div>`` with no
    ``data-heroes-on-map``, no child rows, and no visible text. Does not
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
        xml = render_enemy_hero_locator(
            world, game, player_duchy_id=player_duchy_id
        )
        root = ET.fromstring(xml)

        assert root.tag == "div"
        assert root.attrib == {"data-hero-locator": ""}
        assert "data-heroes-on-map" not in root.attrib
        assert list(root) == []
        assert "".join(root.itertext()) == ""
