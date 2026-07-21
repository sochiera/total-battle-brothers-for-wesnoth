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


def test_render_enemy_hero_locator_rows_region_unfielded_skip_no_hero_and_on_map_count():
    """With ``player_duchy_id`` in ``game.duchies``, root carries
    ``data-heroes-on-map="K"`` (enemy duchies with ``has_hero`` whose party
    occupies a region via ``world.party_at``), one child row per other duchy
    with ``has_hero`` in ``game.duchies`` order (enemies without hero omitted),
    and region/text from first matching ``world.regions`` entry — or empty
    region + „niewystawiony” when no party. Pure: does not mutate world/game.
    """
    # regions order: West first, then East — west_hero party in West → region West
    west = Region("West")
    east = Region("East")
    world = WorldMap(
        [west, east],
        [],
        parties={
            west: Party(hero=Unit(), units=(), owner_id="west_hero"),
            # player party on map must not create a row or inflate K
            east: Party(hero=Unit(), units=(), owner_id="player"),
        },
    )
    # game.duchies order: player, west_hero (on map), east_unfielded (hero, no
    # party), south_no_hero (skip), north_hero_on_map is not used — keep three
    # enemies: one on map, one unfielded, one without hero
    game = GameState(
        (
            Duchy("player", Unit()),
            Duchy("west_hero", Unit()),
            Duchy("east_unfielded", Unit()),
            Duchy("south_no_hero", None),
        )
    )
    regions_before = world.regions
    parties_before = {r: world.party_at(r) for r in world.regions}
    duchies_before = game.duchies

    xml = render_enemy_hero_locator(world, game, player_duchy_id="player")
    root = ET.fromstring(xml)

    assert root.tag == "div"
    assert root.attrib.get("data-hero-locator") == ""
    # only west_hero has a party on the map among enemies with has_hero
    assert root.attrib["data-heroes-on-map"] == "1"

    rows = list(root)
    assert len(rows) == 2
    assert [r.get("data-enemy-duchy") for r in rows] == [
        "west_hero",
        "east_unfielded",
    ]
    # no row for player or south_no_hero
    assert all(r.get("data-enemy-duchy") != "player" for r in rows)
    assert all(r.get("data-enemy-duchy") != "south_no_hero" for r in rows)

    on_map = rows[0]
    assert on_map.tag == "div"
    assert on_map.get("data-hero-region") == "West"
    assert "".join(on_map.itertext()) == "west_hero: bohater w West"

    unfielded = rows[1]
    assert unfielded.tag == "div"
    assert unfielded.get("data-hero-region") == ""
    assert "".join(unfielded.itertext()) == "east_unfielded: bohater niewystawiony"

    assert world.regions is regions_before
    assert game.duchies is duchies_before
    for r in world.regions:
        assert world.party_at(r) is parties_before[r]
