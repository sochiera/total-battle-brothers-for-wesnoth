"""Tests for the engagement-preview presentation primitive (tbbui)."""

from xml.etree import ElementTree as ET

from tbb.duchy import Duchy
from tbb.game import GameState
from tbb.party import Party
from tbb.settlement import Settlement
from tbb.unit import Unit
from tbb.world import Region, WorldMap
from tbbui.engagementpreview import (
    advantageous_target_count,
    render_engagement_preview,
)
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


def test_render_engagement_preview_adjacent_enemy_party_and_settlement_before_party():
    """Adjacent enemy parties yield ``data-target-kind="party"`` rows with
    strength from ``combat_totals((hero, *units))`` and visible text
    ``…: oddział HP H, atak A, obrona D`` (plus advantage suffix). When the
    same neighbouring region has both a hostile settlement and a hostile party,
    the settlement row precedes the party row; inter-region order follows
    ``world.neighbors``. Party rows use the same ``data-advantage`` rule as
    settlements (own sum ≥ target sum → ``"true"`` / „ — przewaga").
    """
    home = Region("Home")
    party_only = Region("PartyOnly")
    both = Region("Both")
    far = Region("Far")

    hero = Unit()
    player_party = Party(hero=hero, units=(), owner_id="player")
    own_hp, own_attack, own_defense = combat_totals((hero,))
    own_sum = own_hp + own_attack + own_defense

    # Weaker enemy party on PartyOnly → advantage true.
    enemy_party_hero = Unit()
    enemy_party = Party(
        hero=enemy_party_hero, units=(), owner_id="enemy"
    )
    party_hp, party_attack, party_defense = combat_totals((enemy_party_hero,))
    assert own_sum >= party_hp + party_attack + party_defense

    # Hostile settlement + stronger hostile party on Both.
    both_garrison = (Unit(),)
    set_hp, set_attack, set_defense = combat_totals(both_garrison)
    both_party_hero = Unit(training=9)
    both_party = Party(
        hero=both_party_hero, units=(), owner_id="enemy"
    )
    both_party_hp, both_party_attack, both_party_defense = combat_totals(
        (both_party_hero,)
    )
    assert own_sum < both_party_hp + both_party_attack + both_party_defense

    # Non-adjacent enemy party/settlement on Far must not appear as targets.
    far_party = Party(hero=Unit(training=4), units=(), owner_id="enemy")

    world = WorldMap(
        [home, party_only, both, far],
        [
            (home, party_only),
            (home, both),
            (both, far),
        ],
        parties={
            home: player_party,
            party_only: enemy_party,
            both: both_party,
            far: far_party,
        },
        settlements={
            both: Settlement(
                "KeepBoth",
                population=1,
                owner_id="enemy",
                garrison=both_garrison,
            ),
            # non-adjacent enemy settlement — must not appear
            far: Settlement(
                "KeepFar",
                population=1,
                owner_id="enemy",
                garrison=(Unit(training=2),),
            ),
        },
    )
    assert [r.name for r in world.neighbors(home)] == ["PartyOnly", "Both"]

    game = GameState(
        (
            Duchy("player", Unit()),
            Duchy("enemy", Unit()),
        )
    )

    xml = render_engagement_preview(world, game, player_duchy_id="player")
    root = ET.fromstring(xml)

    assert root.attrib.get("data-player-on-map") == "true"
    assert root.attrib.get("data-own-hp") == str(own_hp)

    rows = list(root)
    # neighbors order: PartyOnly (party only) → Both (settlement then party)
    assert [
        (r.get("data-target-region"), r.get("data-target-kind")) for r in rows
    ] == [
        ("PartyOnly", "party"),
        ("Both", "settlement"),
        ("Both", "party"),
    ]
    assert all(r.get("data-target-region") != "Far" for r in rows)
    assert all(r.get("data-target-region") != "Home" for r in rows)

    party_only_row = rows[0]
    assert party_only_row.get("data-target-owner") == "enemy"
    assert party_only_row.get("data-enemy-hp") == str(party_hp)
    assert party_only_row.get("data-enemy-attack") == str(party_attack)
    assert party_only_row.get("data-enemy-defense") == str(party_defense)
    assert party_only_row.get("data-advantage") == "true"
    assert (
        "".join(party_only_row.itertext())
        == (
            f"PartyOnly (enemy): oddział HP {party_hp},"
            f" atak {party_attack}, obrona {party_defense} — przewaga"
        )
    )

    both_settlement = rows[1]
    assert both_settlement.get("data-target-kind") == "settlement"
    assert both_settlement.get("data-enemy-hp") == str(set_hp)
    assert both_settlement.get("data-advantage") == (
        "true" if own_sum >= set_hp + set_attack + set_defense else "false"
    )
    set_suffix = (
        " — przewaga"
        if own_sum >= set_hp + set_attack + set_defense
        else " — niekorzystnie"
    )
    assert (
        "".join(both_settlement.itertext())
        == (
            f"Both (enemy): garnizon HP {set_hp},"
            f" atak {set_attack}, obrona {set_defense}{set_suffix}"
        )
    )

    both_party_row = rows[2]
    assert both_party_row.get("data-target-owner") == "enemy"
    assert both_party_row.get("data-enemy-hp") == str(both_party_hp)
    assert both_party_row.get("data-enemy-attack") == str(both_party_attack)
    assert both_party_row.get("data-enemy-defense") == str(both_party_defense)
    assert both_party_row.get("data-advantage") == "false"
    assert (
        "".join(both_party_row.itertext())
        == (
            f"Both (enemy): oddział HP {both_party_hp},"
            f" atak {both_party_attack}, obrona {both_party_defense}"
            f" — niekorzystnie"
        )
    )


def test_advantageous_target_count_adjacent_with_advantage_and_zero_when_absent():
    """``advantageous_target_count(world, game, player_duchy_id) -> int`` is the
    number of adjacent hostile targets (settlement and/or party, same targets as
    ``render_engagement_preview`` rows) where the player's party has advantage
    (``own_sum >= enemy_sum``, same rule as ``data-advantage="true"``). Equality
    counts; strictly weaker targets do not. Unknown player
    (``player_duchy(...) is None``) or known player with no party on the map
    → ``0``. Pure (no world/game mutation).
    """
    home = Region("Home")
    equal_region = Region("EqualKeep")
    strong_region = Region("StrongKeep")
    weak_party_region = Region("WeakParty")
    far = Region("Far")

    hero = Unit()
    player_party = Party(hero=hero, units=(), owner_id="player")
    own_hp, own_attack, own_defense = combat_totals((hero,))
    own_sum = own_hp + own_attack + own_defense

    # Equal enemy garrison → advantage (counts).
    equal_garrison = (Unit(),)
    eq_hp, eq_attack, eq_defense = combat_totals(equal_garrison)
    assert own_sum == eq_hp + eq_attack + eq_defense

    # Stronger enemy garrison → no advantage (does not count).
    strong_garrison = (Unit(training=9),)
    st_hp, st_attack, st_defense = combat_totals(strong_garrison)
    assert own_sum < st_hp + st_attack + st_defense

    # Weaker adjacent enemy party → advantage (counts).
    weak_hero = Unit()
    weak_party = Party(hero=weak_hero, units=(), owner_id="enemy")
    w_hp, w_attack, w_defense = combat_totals((weak_hero,))
    assert own_sum >= w_hp + w_attack + w_defense

    # Non-adjacent equal enemy settlement must not count.
    far_garrison = (Unit(),)

    world = WorldMap(
        [home, equal_region, strong_region, weak_party_region, far],
        [
            (home, equal_region),
            (home, strong_region),
            (home, weak_party_region),
            (strong_region, far),
        ],
        parties={
            home: player_party,
            weak_party_region: weak_party,
        },
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
            far: Settlement(
                "KeepFar",
                population=1,
                owner_id="enemy",
                garrison=far_garrison,
            ),
        },
    )
    game = GameState(
        (
            Duchy("player", Unit()),
            Duchy("enemy", Unit()),
        )
    )

    # Preview rows: Equal (adv), Strong (no), WeakParty (adv) → M = 2
    preview = ET.fromstring(
        render_engagement_preview(world, game, player_duchy_id="player")
    )
    advantage_true = [
        r for r in list(preview) if r.get("data-advantage") == "true"
    ]
    assert len(advantage_true) == 2

    regions_before = world.regions
    parties_before = {r: world.party_at(r) for r in world.regions}
    settlements_before = {r: world.settlement_at(r) for r in world.regions}
    duchies_before = game.duchies

    m = advantageous_target_count(world, game, "player")
    assert m == 2
    assert m == len(advantage_true)

    # Unknown / missing player → 0
    assert advantageous_target_count(world, game, None) == 0
    assert advantageous_target_count(world, game, "missing") == 0

    # Known player, no party on map → 0
    empty_map = WorldMap(
        [home, equal_region],
        [(home, equal_region)],
        parties={},
        settlements={
            equal_region: Settlement(
                "KeepEqual",
                population=1,
                owner_id="enemy",
                garrison=equal_garrison,
            ),
        },
    )
    assert advantageous_target_count(empty_map, game, "player") == 0

    assert world.regions is regions_before
    assert game.duchies is duchies_before
    for r in world.regions:
        assert world.party_at(r) is parties_before[r]
        assert world.settlement_at(r) is settlements_before[r]

