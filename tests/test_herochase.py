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


def test_render_hero_chase_player_not_on_map_false_and_no_rows():
    """When ``player_duchy_id`` is in ``game.duchies`` but no party on the
    map has that ``owner_id``, root carries ``data-player-on-map="false"``
    and has no ``data-enemy-duchy`` children (even if enemies are fielded).
    """
    a = Region("A")
    b = Region("B")
    world = WorldMap(
        [a, b],
        [(a, b)],
        parties={
            # only enemy on the map — player has no party
            b: Party(hero=Unit(), units=(), owner_id="enemy"),
        },
    )
    game = GameState(
        (
            Duchy("player", Unit()),
            Duchy("enemy", Unit()),
        )
    )

    xml = render_hero_chase(world, game, player_duchy_id="player")
    root = ET.fromstring(xml)

    assert root.tag == "div"
    assert root.attrib.get("data-hero-chase") == ""
    assert root.attrib.get("data-player-on-map") == "false"
    assert list(root) == []
    assert not any(
        child.get("data-enemy-duchy") is not None for child in root
    )


def test_render_hero_chase_on_map_distances_first_source_skip_and_pure():
    """When player party is on the map: ``data-player-on-map="true"``;
    source region is the first in ``world.regions`` with matching
    ``owner_id``; one row per other duchy with ``has_hero`` and a party on
    the map (``game.duchies`` order) with ``data-distance`` from
    ``ai.region_distance`` and text „id: D pól marszu" or „brak drogi";
    skip no-hero and unfielded enemies; pure (no world/game mutation).
    """
    from tbb import ai

    # Order matters: Far before Near — player parties on both; source = Far.
    far = Region("Far")
    near = Region("Near")
    mid = Region("Mid")
    enemy_here = Region("EnemyHere")
    island = Region("Island")
    world = WorldMap(
        [far, near, mid, enemy_here, island],
        [
            (far, near),
            (near, mid),
            (mid, enemy_here),
            # island disconnected
        ],
        parties={
            far: Party(hero=Unit(), units=(), owner_id="player"),
            near: Party(hero=Unit(), units=(), owner_id="player"),
            enemy_here: Party(hero=Unit(), units=(), owner_id="reachable"),
            island: Party(hero=Unit(), units=(), owner_id="stranded"),
            # unfielded_hero: has hero in game but no party
            # no_hero: party would not matter; no has_hero
        },
    )
    game = GameState(
        (
            Duchy("player", Unit()),
            Duchy("reachable", Unit()),
            Duchy("stranded", Unit()),
            Duchy("unfielded_hero", Unit()),
            Duchy("no_hero", None),
        )
    )
    # Distance from first player region (Far) → EnemyHere is 3 (Far-Near-Mid-EnemyHere),
    # not 2 from Near — proves source is first matching region.
    assert ai.region_distance(world, far, enemy_here) == 3
    assert ai.region_distance(world, near, enemy_here) == 2
    assert ai.region_distance(world, far, island) is None

    regions_before = world.regions
    parties_before = {r: world.party_at(r) for r in world.regions}
    duchies_before = game.duchies

    xml = render_hero_chase(world, game, player_duchy_id="player")
    root = ET.fromstring(xml)

    assert root.tag == "div"
    assert root.attrib.get("data-hero-chase") == ""
    assert root.attrib.get("data-player-on-map") == "true"

    rows = list(root)
    assert [r.get("data-enemy-duchy") for r in rows] == [
        "reachable",
        "stranded",
    ]
    assert all(r.get("data-enemy-duchy") != "player" for r in rows)
    assert all(r.get("data-enemy-duchy") != "unfielded_hero" for r in rows)
    assert all(r.get("data-enemy-duchy") != "no_hero" for r in rows)

    reachable = rows[0]
    assert reachable.tag == "div"
    assert reachable.get("data-distance") == "3"
    assert "".join(reachable.itertext()) == "reachable: 3 pól marszu"

    stranded = rows[1]
    assert stranded.tag == "div"
    assert stranded.get("data-distance") == ""
    assert "".join(stranded.itertext()) == "stranded: brak drogi"

    assert world.regions is regions_before
    assert game.duchies is duchies_before
    for r in world.regions:
        assert world.party_at(r) is parties_before[r]


def test_render_hero_chase_in_reach_only_for_distance_one():
    """Distance 1: ``data-in-reach=""`` + suffix „ — w zasięgu"; other
    distances (including no path) have neither the attribute nor the suffix.
    """
    from tbb import ai

    player_region = Region("Player")
    adjacent = Region("Adjacent")
    far = Region("Far")
    island = Region("Island")
    world = WorldMap(
        [player_region, adjacent, far, island],
        [
            (player_region, adjacent),
            (adjacent, far),
            # island disconnected
        ],
        parties={
            player_region: Party(hero=Unit(), units=(), owner_id="player"),
            adjacent: Party(hero=Unit(), units=(), owner_id="next_door"),
            far: Party(hero=Unit(), units=(), owner_id="distant"),
            island: Party(hero=Unit(), units=(), owner_id="stranded"),
        },
    )
    game = GameState(
        (
            Duchy("player", Unit()),
            Duchy("next_door", Unit()),
            Duchy("distant", Unit()),
            Duchy("stranded", Unit()),
        )
    )
    assert ai.region_distance(world, player_region, adjacent) == 1
    assert ai.region_distance(world, player_region, far) == 2
    assert ai.region_distance(world, player_region, island) is None

    xml = render_hero_chase(world, game, player_duchy_id="player")
    root = ET.fromstring(xml)
    rows = {r.get("data-enemy-duchy"): r for r in root}

    in_reach = rows["next_door"]
    assert in_reach.get("data-distance") == "1"
    assert in_reach.get("data-in-reach") == ""
    assert "".join(in_reach.itertext()) == "next_door: 1 pól marszu — w zasięgu"

    distant = rows["distant"]
    assert distant.get("data-distance") == "2"
    assert "data-in-reach" not in distant.attrib
    assert "".join(distant.itertext()) == "distant: 2 pól marszu"
    assert " — w zasięgu" not in "".join(distant.itertext())

    stranded = rows["stranded"]
    assert stranded.get("data-distance") == ""
    assert "data-in-reach" not in stranded.attrib
    assert "".join(stranded.itertext()) == "stranded: brak drogi"
    assert " — w zasięgu" not in "".join(stranded.itertext())
