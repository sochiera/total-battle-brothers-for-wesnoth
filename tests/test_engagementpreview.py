"""Tests for the engagement-preview presentation primitive (tbbui)."""

from xml.etree import ElementTree as ET

from tbb.duchy import Duchy
from tbb.game import GameState
from tbb.party import Party
from tbb.settlement import Settlement
from tbb.unit import Unit
from tbb.world import Region, WorldMap
from tbbui.engagementpreview import render_engagement_preview
from tbbui.unitstrength import combat_totals


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


def test_render_engagement_preview_player_not_on_map_false_no_rows_no_own():
    """When ``player_duchy_id`` is in ``game.duchies`` but no region has
    ``party_at.owner_id == player_duchy_id``, root carries
    ``data-player-on-map="false"`` with no ``data-own-*`` and no child rows
    (even if enemy settlements exist).
    """
    a = Region("A")
    b = Region("B")
    world = WorldMap(
        [a, b],
        [(a, b)],
        parties={},
        settlements={
            b: Settlement(
                "EnemyKeep",
                population=1,
                owner_id="enemy",
                garrison=(Unit(training=2),),
            ),
        },
    )
    game = GameState(
        (
            Duchy("player", Unit()),
            Duchy("enemy", Unit()),
        )
    )

    xml = render_engagement_preview(world, game, player_duchy_id="player")
    root = ET.fromstring(xml)

    assert root.tag == "div"
    assert root.attrib.get("data-engagement-preview") == ""
    assert root.attrib.get("data-player-on-map") == "false"
    assert "data-own-hp" not in root.attrib
    assert "data-own-attack" not in root.attrib
    assert "data-own-defense" not in root.attrib
    assert list(root) == []
    assert "".join(root.itertext()) == ""


def test_render_engagement_preview_on_map_own_stats_enemy_settlement_and_pure():
    """When player party is on the map: ``data-player-on-map="true"`` and
    ``data-own-*`` from ``combat_totals((hero, *units))``; one settlement row
    per adjacent region (``world.neighbors`` order) with explicit
    ``owner_id != player`` and text/attrs from ``combat_totals(garrison)``;
    skips own/unowned/non-adjacent; pure (no world/game mutation).
    """
    home = Region("Home")
    first_neighbor = Region("First")
    second_neighbor = Region("Second")
    far = Region("Far")

    hero = Unit(training=3)
    companion = Unit(equipment=2)
    party = Party(hero=hero, units=(companion,), owner_id="player")
    own_hp, own_attack, own_defense = combat_totals((hero, companion))

    enemy_garrison = (Unit(training=1), Unit(experience=2))
    enemy_hp, enemy_attack, enemy_defense = combat_totals(enemy_garrison)
    other_garrison = (Unit(equipment=4),)
    other_hp, other_attack, other_defense = combat_totals(other_garrison)

    world = WorldMap(
        [home, first_neighbor, second_neighbor, far],
        [
            (home, first_neighbor),
            (home, second_neighbor),
            (first_neighbor, far),
        ],
        parties={home: party},
        settlements={
            first_neighbor: Settlement(
                "KeepFirst",
                population=2,
                owner_id="enemy",
                garrison=enemy_garrison,
            ),
            second_neighbor: Settlement(
                "KeepSecond",
                population=2,
                owner_id="other",
                garrison=other_garrison,
            ),
            # own adjacent settlement — must not appear
            # (place on a duplicate edge? use far's settlement as non-adjacent enemy)
            far: Settlement(
                "KeepFar",
                population=2,
                owner_id="enemy",
                garrison=(Unit(training=9),),
            ),
            home: Settlement(
                "KeepHome",
                population=2,
                owner_id="player",
                garrison=(Unit(training=5),),
            ),
        },
    )
    # Unowned adjacent settlement on a fifth region would also be skipped;
    # second_neighbor is foreign — included. Order = world.neighbors(home).
    neighbor_order = list(world.neighbors(home))
    assert [r.name for r in neighbor_order] == ["First", "Second"]

    game = GameState(
        (
            Duchy("player", Unit()),
            Duchy("enemy", Unit()),
            Duchy("other", Unit()),
        )
    )

    regions_before = world.regions
    parties_before = {r: world.party_at(r) for r in world.regions}
    settlements_before = {r: world.settlement_at(r) for r in world.regions}
    duchies_before = game.duchies

    xml = render_engagement_preview(world, game, player_duchy_id="player")
    root = ET.fromstring(xml)

    assert root.tag == "div"
    assert root.attrib.get("data-engagement-preview") == ""
    assert root.attrib.get("data-player-on-map") == "true"
    assert root.attrib.get("data-own-hp") == str(own_hp)
    assert root.attrib.get("data-own-attack") == str(own_attack)
    assert root.attrib.get("data-own-defense") == str(own_defense)

    rows = list(root)
    assert [r.get("data-target-region") for r in rows] == ["First", "Second"]
    assert all(r.get("data-target-kind") == "settlement" for r in rows)
    assert all(r.get("data-target-region") != "Far" for r in rows)
    assert all(r.get("data-target-region") != "Home" for r in rows)

    own_sum = own_hp + own_attack + own_defense
    first_advantage = own_sum >= enemy_hp + enemy_attack + enemy_defense
    second_advantage = own_sum >= other_hp + other_attack + other_defense
    first_suffix = " — przewaga" if first_advantage else " — niekorzystnie"
    second_suffix = " — przewaga" if second_advantage else " — niekorzystnie"

    first = rows[0]
    assert first.get("data-target-owner") == "enemy"
    assert first.get("data-enemy-hp") == str(enemy_hp)
    assert first.get("data-enemy-attack") == str(enemy_attack)
    assert first.get("data-enemy-defense") == str(enemy_defense)
    assert first.get("data-advantage") == ("true" if first_advantage else "false")
    assert (
        "".join(first.itertext())
        == (
            f"First (enemy): garnizon HP {enemy_hp},"
            f" atak {enemy_attack}, obrona {enemy_defense}{first_suffix}"
        )
    )

    second = rows[1]
    assert second.get("data-target-owner") == "other"
    assert second.get("data-enemy-hp") == str(other_hp)
    assert second.get("data-enemy-attack") == str(other_attack)
    assert second.get("data-enemy-defense") == str(other_defense)
    assert second.get("data-advantage") == ("true" if second_advantage else "false")
    assert (
        "".join(second.itertext())
        == (
            f"Second (other): garnizon HP {other_hp},"
            f" atak {other_attack}, obrona {other_defense}{second_suffix}"
        )
    )

    assert world.regions is regions_before
    assert game.duchies is duchies_before
    for r in world.regions:
        assert world.party_at(r) is parties_before[r]
        assert world.settlement_at(r) is settlements_before[r]


def test_render_engagement_preview_advantage_flag_and_suffix():
    """Each target row gets ``data-advantage`` after ``data-enemy-defense``:
    ``"true"`` and text suffix `` — przewaga`` when own sum (hp+attack+defense)
    is ``>=`` enemy sum; ``"false"`` and `` — niekorzystnie`` when own sum is
    strictly lower. Equality counts as advantage.
    """
    home = Region("Home")
    equal_region = Region("EqualKeep")
    strong_region = Region("StrongKeep")

    # Own party: single default unit → combat sum 10.
    hero = Unit()
    party = Party(hero=hero, units=(), owner_id="player")
    own_hp, own_attack, own_defense = combat_totals((hero,))
    own_sum = own_hp + own_attack + own_defense

    # Equal enemy garrison (same sum) → advantage true.
    equal_garrison = (Unit(),)
    eq_hp, eq_attack, eq_defense = combat_totals(equal_garrison)
    assert own_sum == eq_hp + eq_attack + eq_defense

    # Stronger enemy garrison → advantage false.
    strong_garrison = (Unit(training=9),)
    st_hp, st_attack, st_defense = combat_totals(strong_garrison)
    assert own_sum < st_hp + st_attack + st_defense

    world = WorldMap(
        [home, equal_region, strong_region],
        [(home, equal_region), (home, strong_region)],
        parties={home: party},
        settlements={
            equal_region: Settlement(
                "KeepEqual",
                population=1,
                owner_id="enemy",
                garrison=equal_garrison,
            ),
            strong_region: Settlement(
                "KeepStrong",
                population=1,
                owner_id="enemy",
                garrison=strong_garrison,
            ),
        },
    )
    assert [r.name for r in world.neighbors(home)] == ["EqualKeep", "StrongKeep"]

    game = GameState(
        (
            Duchy("player", Unit()),
            Duchy("enemy", Unit()),
        )
    )

    xml = render_engagement_preview(world, game, player_duchy_id="player")
    root = ET.fromstring(xml)
    rows = list(root)
    assert len(rows) == 2

    equal_row, strong_row = rows

    # Advantage when own strength >= target strength (including equality).
    assert equal_row.get("data-advantage") == "true"
    assert (
        "".join(equal_row.itertext())
        == (
            f"EqualKeep (enemy): garnizon HP {eq_hp},"
            f" atak {eq_attack}, obrona {eq_defense} — przewaga"
        )
    )

    # Disadvantage when own strength is strictly lower.
    assert strong_row.get("data-advantage") == "false"
    assert (
        "".join(strong_row.itertext())
        == (
            f"StrongKeep (enemy): garnizon HP {st_hp},"
            f" atak {st_attack}, obrona {st_defense} — niekorzystnie"
        )
    )

    # ``data-advantage`` follows ``data-enemy-defense``; other attrs keep order.
    expected_keys = [
        "data-target-region",
        "data-target-owner",
        "data-target-kind",
        "data-enemy-hp",
        "data-enemy-attack",
        "data-enemy-defense",
        "data-advantage",
    ]
    assert list(equal_row.attrib.keys()) == expected_keys
    assert list(strong_row.attrib.keys()) == expected_keys
