"""Tests for the recommended-action presentation primitive (tbbui)."""

from xml.etree import ElementTree as ET

from tbb import ai
from tbb.duchy import Duchy
from tbb.game import GameState
from tbb.party import Party
from tbb.settlement import Settlement
from tbb.unit import Unit
from tbb.world import Region, WorldMap
from tbbui.engagementpreview import (
    advantageous_target_count,
    first_advantageous_target,
)
from tbbui.gamelookup import player_duchy
from tbbui.maplookup import first_party_region
from tbbui import recommendedaction
from tbbui.recommendedaction import recommended_order, render_recommended_action
from tbbui.situationreport import net_posture
from tbbui.threatalert import first_threatened_region, threatened_position_count


def test_player_march_target_none_without_duchy_or_party_name_when_distance_ge_two():
    """``player_march_target(world, game, player_duchy_id)`` → ``None`` when
    ``player_duchy(game, player_duchy_id) is None`` or
    ``first_party_region(world, player_duchy_id) is None``; when the player has
    a party in region R and ``ai.nearest_enemy_settlement(world, R, id)`` exists
    with ``ai.region_distance(world, R, target) >= 2``, returns ``target.name``;
    when the nearest enemy settlement is ``None`` or has distance ``< 2``,
    returns ``None``. Pure and deterministic: no RNG/IO; does not mutate
    ``world`` or ``game`` — K49.1a.

    Contract: reuses ``gamelookup.player_duchy``, ``maplookup.first_party_region``,
    ``ai.nearest_enemy_settlement`` and ``ai.region_distance``.
    """
    player_march_target = recommendedaction.player_march_target
    home = Region("Home")
    road = Region("Road")
    far_enemy = Region("FarEnemy")
    near_enemy = Region("NearEnemy")
    only_home = Region("OnlyHome")
    game = GameState(
        (
            Duchy("player", Unit()),
            Duchy("enemy", Unit()),
        )
    )

    # Distance >= 2: Home — Road — FarEnemy (enemy settlement at FarEnemy)
    far_world = WorldMap(
        [home, road, far_enemy],
        [(home, road), (road, far_enemy)],
        parties={home: Party(hero=Unit(), units=(), owner_id="player")},
        settlements={
            far_enemy: Settlement("FarS", population=2, owner_id="enemy"),
        },
    )
    r = first_party_region(far_world, "player")
    assert r is home
    target = ai.nearest_enemy_settlement(far_world, r, "player")
    assert target is far_enemy
    assert ai.region_distance(far_world, r, target) >= 2

    regions_before = far_world.regions
    parties_before = {reg: far_world.party_at(reg) for reg in far_world.regions}
    settlements_before = {
        reg: far_world.settlement_at(reg) for reg in far_world.regions
    }
    duchies_before = game.duchies

    assert player_march_target(far_world, game, "player") == target.name

    assert far_world.regions == regions_before
    assert {
        reg: far_world.party_at(reg) for reg in far_world.regions
    } == parties_before
    assert {
        reg: far_world.settlement_at(reg) for reg in far_world.regions
    } == settlements_before
    assert game.duchies == duchies_before

    # player_duchy is None → None
    for player_duchy_id in (None, "missing"):
        assert player_duchy(game, player_duchy_id) is None
        assert player_march_target(far_world, game, player_duchy_id) is None

    # known duchy but no party on the map → None
    no_party_world = WorldMap(
        [home, road, far_enemy],
        [(home, road), (road, far_enemy)],
        parties={},
        settlements={
            far_enemy: Settlement("FarS", population=2, owner_id="enemy"),
        },
    )
    assert player_duchy(game, "player") is not None
    assert first_party_region(no_party_world, "player") is None
    assert player_march_target(no_party_world, game, "player") is None

    # nearest enemy settlement is adjacent (distance < 2) → None
    near_world = WorldMap(
        [home, near_enemy],
        [(home, near_enemy)],
        parties={home: Party(hero=Unit(), units=(), owner_id="player")},
        settlements={
            near_enemy: Settlement("NearS", population=2, owner_id="enemy"),
        },
    )
    r_near = first_party_region(near_world, "player")
    assert r_near is home
    near_target = ai.nearest_enemy_settlement(near_world, r_near, "player")
    assert near_target is near_enemy
    assert ai.region_distance(near_world, r_near, near_target) == 1
    assert ai.region_distance(near_world, r_near, near_target) < 2
    assert player_march_target(near_world, game, "player") is None

    # no enemy settlement at all → None
    alone_world = WorldMap(
        [only_home],
        [],
        parties={only_home: Party(hero=Unit(), units=(), owner_id="player")},
        settlements={
            only_home: Settlement("HomeS", population=2, owner_id="player"),
        },
    )
    r_alone = first_party_region(alone_world, "player")
    assert r_alone is only_home
    assert ai.nearest_enemy_settlement(alone_world, r_alone, "player") is None
    assert player_march_target(alone_world, game, "player") is None


def test_player_can_muster_true_iff_hero_no_party_and_free_own_settlement():
    """``player_can_muster(world, game, player_duchy_id)`` is True iff the
    player duchy is known, has a hero, has no party on the map, and owns a
    settlement in a party-free region (``world.regions`` order) — K48.1a.

    Contract: reuses ``player_duchy`` and ``first_party_region``; free-settlement
    predicate matches ``ai.muster_duchy_party`` success
    (``settlement.owner_id == player_duchy_id and region not in world.parties``).
    Pure and deterministic: no world/game mutation. False for ``None``/unknown
    id, no hero, party already fielded, or no free own settlement.
    """
    player_can_muster = recommendedaction.player_can_muster
    home = Region("Home")
    other = Region("Other")
    occupied = Region("Occupied")
    hero = Unit(training=2)
    own_settlement = Settlement("HomeS", population=2, owner_id="player")
    foreign_settlement = Settlement("OtherS", population=1, owner_id="enemy")

    ready_world = WorldMap(
        [home, other],
        [(home, other)],
        parties={},
        settlements={
            home: own_settlement,
            other: foreign_settlement,
        },
    )
    game = GameState(
        (
            Duchy("player", hero),
            Duchy("enemy", Unit()),
        )
    )
    no_hero_game = GameState(
        (
            Duchy("player", None),
            Duchy("enemy", Unit()),
        )
    )

    # Preconditions of the True path align with lookup helpers / muster rules.
    assert player_duchy(game, "player") is not None
    assert player_duchy(game, "player").has_hero
    assert first_party_region(ready_world, "player") is None
    assert home not in ready_world.parties
    assert ready_world.settlement_at(home).owner_id == "player"

    regions_before = ready_world.regions
    parties_before = {r: ready_world.party_at(r) for r in ready_world.regions}
    settlements_before = {
        r: ready_world.settlement_at(r) for r in ready_world.regions
    }
    duchies_before = game.duchies

    assert player_can_muster(ready_world, game, "player") is True

    assert ready_world.regions == regions_before
    assert {
        r: ready_world.party_at(r) for r in ready_world.regions
    } == parties_before
    assert {
        r: ready_world.settlement_at(r) for r in ready_world.regions
    } == settlements_before
    assert game.duchies == duchies_before

    # player_duchy_id is None or not in game.duchies → False
    for player_duchy_id in (None, "missing"):
        assert player_duchy(game, player_duchy_id) is None
        assert player_can_muster(ready_world, game, player_duchy_id) is False

    # no hero → False
    assert player_duchy(no_hero_game, "player") is not None
    assert not player_duchy(no_hero_game, "player").has_hero
    assert player_can_muster(ready_world, no_hero_game, "player") is False

    # player party already on map → False
    fielded_world = WorldMap(
        [home, other],
        [(home, other)],
        parties={other: Party(hero=Unit(), units=(), owner_id="player")},
        settlements={home: own_settlement},
    )
    assert first_party_region(fielded_world, "player") is not None
    assert player_can_muster(fielded_world, game, "player") is False

    # own settlement exists but its region is occupied by another party → False
    blocked_world = WorldMap(
        [occupied],
        [],
        parties={occupied: Party(hero=Unit(), units=(), owner_id="enemy")},
        settlements={
            occupied: Settlement("BlockedS", population=2, owner_id="player"),
        },
    )
    assert first_party_region(blocked_world, "player") is None
    assert player_can_muster(blocked_world, game, "player") is False

    # no own settlement at all → False
    no_own_world = WorldMap(
        [other],
        [],
        parties={},
        settlements={other: foreign_settlement},
    )
    assert player_can_muster(no_own_world, game, "player") is False


def test_recommended_order_text_maps_action_and_target_to_description():
    """``recommended_order_text(action, target_name)`` returns the descriptive
    half of the advice line only (no ``Zalecany rozkaz: `` prefix) — K42.2a.

    Contract (task-206): ``("assault", R)`` → ``szturmuj osadę <R>``;
    ``("engage", R)`` → ``zaatakuj oddział <R>``; ``("defend", R)`` →
    ``broń pozycji <R>``; ``("develop", None)`` → ``rozwijaj księstwo``.
    Pure and deterministic.
    """
    recommended_order_text = recommendedaction.recommended_order_text
    assert recommended_order_text("assault", "EnemyCamp") == (
        "szturmuj osadę EnemyCamp"
    )
    assert recommended_order_text("engage", "WeakA") == "zaatakuj oddział WeakA"
    assert recommended_order_text("defend", "Keep") == "broń pozycji Keep"
    assert recommended_order_text("develop", None) == "rozwijaj księstwo"


def test_recommended_order_text_muster_returns_zbierz_oddzial():
    """``recommended_order_text("muster", None)`` → ``"zbierz oddział"`` — K48.1b.

    Contract (task-228): new ``muster`` branch with target ``None``; descriptive
    half only (no ``Zalecany rozkaz: `` prefix). Other actions stay covered by
    ``test_recommended_order_text_maps_action_and_target_to_description``.
    Pure and deterministic.
    """
    recommended_order_text = recommendedaction.recommended_order_text
    assert recommended_order_text("muster", None) == "zbierz oddział"


def test_recommended_order_text_march_returns_maszeruj_ku_osadzie():
    """``recommended_order_text("march", "Północ")`` →
    ``"maszeruj ku osadzie Północ"`` — K49.1b.

    Contract (task-232): new ``march`` branch
    ``f"maszeruj ku osadzie {target_name}"``; descriptive half only (no
    ``Zalecany rozkaz: `` prefix). Remaining actions unchanged:
    ``("assault", R)`` → ``"szturmuj osadę R"``, ``("engage", R)`` →
    ``"zaatakuj oddział R"``, ``("defend", R)`` → ``"broń pozycji R"``,
    ``("muster", None)`` → ``"zbierz oddział"``, ``("develop", None)`` →
    ``"rozwijaj księstwo"``. Pure and deterministic.
    """
    recommended_order_text = recommendedaction.recommended_order_text
    assert recommended_order_text("march", "Północ") == (
        "maszeruj ku osadzie Północ"
    )
    assert recommended_order_text("assault", "R") == "szturmuj osadę R"
    assert recommended_order_text("engage", "R") == "zaatakuj oddział R"
    assert recommended_order_text("defend", "R") == "broń pozycji R"
    assert recommended_order_text("muster", None) == "zbierz oddział"
    assert recommended_order_text("develop", None) == "rozwijaj księstwo"


def test_recommended_order_muster_before_posture_when_player_can_muster():
    """``recommended_order`` returns ``("muster", None)`` when
    ``player_can_muster`` is True — priority BEFORE posture (K48.1c).

    Even if net posture would be defensive (N>M → defend), muster wins.
    Pure: no world/game mutation.
    """
    player_can_muster = recommendedaction.player_can_muster
    keep = Region("Keep")
    enemy_camp = Region("EnemyCamp")
    game = GameState(
        (
            Duchy("player", Unit()),
            Duchy("enemy", Unit()),
        )
    )
    # Defensive world: no player party, free own settlement → can muster;
    # enemy party threatens keep → N>M → posture would be defensive/defend.
    world = WorldMap(
        [keep, enemy_camp],
        [(keep, enemy_camp)],
        parties={
            enemy_camp: Party(hero=Unit(), units=(), owner_id="enemy"),
        },
        settlements={
            keep: Settlement("KeepS", population=2, owner_id="player"),
        },
    )
    assert player_can_muster(world, game, "player") is True
    m = advantageous_target_count(world, game, "player")
    n = threatened_position_count(world, game, "player")
    assert net_posture(m, n) == "defensive"
    assert first_threatened_region(world, game, "player") is not None

    regions_before = world.regions
    parties_before = {r: world.party_at(r) for r in world.regions}
    settlements_before = {
        r: world.settlement_at(r) for r in world.regions
    }
    duchies_before = game.duchies

    assert recommended_order(world, game, "player") == ("muster", None)

    assert world.regions == regions_before
    assert {
        r: world.party_at(r) for r in world.regions
    } == parties_before
    assert {
        r: world.settlement_at(r) for r in world.regions
    } == settlements_before
    assert game.duchies == duchies_before


def test_render_recommended_action_muster_data_action_and_text_keeps_posture():
    """``render_recommended_action`` when ``recommended_order`` is
    ``("muster", None)``: root has ``data-action="muster"`` and text
    ``Zalecany rozkaz: zbierz oddział``; ``data-posture`` still equals
    ``net_posture(M, N)`` (M/N counts unchanged) — K48.1c.

    Scenario: can muster True and defensive M/N so posture would be defend
    if muster did not win the order. Pure: no world/game mutation.
    """
    player_can_muster = recommendedaction.player_can_muster
    keep = Region("Keep")
    enemy_camp = Region("EnemyCamp")
    game = GameState(
        (
            Duchy("player", Unit()),
            Duchy("enemy", Unit()),
        )
    )
    world = WorldMap(
        [keep, enemy_camp],
        [(keep, enemy_camp)],
        parties={
            enemy_camp: Party(hero=Unit(), units=(), owner_id="enemy"),
        },
        settlements={
            keep: Settlement("KeepS", population=2, owner_id="player"),
        },
    )
    assert player_can_muster(world, game, "player") is True
    assert recommended_order(world, game, "player") == ("muster", None)
    m = advantageous_target_count(world, game, "player")
    n = threatened_position_count(world, game, "player")
    expected_posture = net_posture(m, n)
    assert expected_posture == "defensive"

    regions_before = world.regions
    parties_before = {r: world.party_at(r) for r in world.regions}
    settlements_before = {
        r: world.settlement_at(r) for r in world.regions
    }
    duchies_before = game.duchies

    root = ET.fromstring(
        render_recommended_action(world, game, player_duchy_id="player")
    )
    assert root.tag == "div"
    assert root.attrib.get("data-recommended-action") == ""
    assert root.attrib.get("data-posture") == expected_posture
    assert root.attrib.get("data-posture") == net_posture(m, n)
    assert root.attrib.get("data-action") == "muster"
    assert root.text == "Zalecany rozkaz: zbierz oddział"
    assert list(root) == []

    assert world.regions == regions_before
    assert {
        r: world.party_at(r) for r in world.regions
    } == parties_before
    assert {
        r: world.settlement_at(r) for r in world.regions
    } == settlements_before
    assert game.duchies == duchies_before


def test_recommended_order_returns_none_when_player_duchy_missing():
    """``recommended_order(world, game, player_duchy_id)`` returns ``None``
    when ``player_duchy(game, player_duchy_id) is None`` — i.e. no player
    (``player_duchy_id is None``) or id not in ``game.duchies``. Pure: does
    not mutate ``world`` or ``game``.
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
    regions_before = world.regions
    parties_before = {r: world.party_at(r) for r in world.regions}
    settlements_before = {
        r: world.settlement_at(r) for r in world.regions
    }
    duchies_before = game.duchies

    for player_duchy_id in (None, "missing"):
        assert player_duchy(game, player_duchy_id) is None
        assert recommended_order(world, game, player_duchy_id) is None

    assert world.regions == regions_before
    assert {
        r: world.party_at(r) for r in world.regions
    } == parties_before
    assert {
        r: world.settlement_at(r) for r in world.regions
    } == settlements_before
    assert game.duchies == duchies_before


def test_recommended_order_offensive_assault_and_engage_from_first_advantageous_target():
    """Offensive posture: ``recommended_order`` returns
    ``("assault", <region>)`` when ``first_advantageous_target`` has
    ``kind=="settlement"``, and ``("engage", <region>)`` when
    ``kind=="party"`` — same target selection / order as
    ``render_recommended_action``. Pure: no world/game mutation.
    """
    home = Region("Home")
    enemy_camp = Region("EnemyCamp")
    weak_a = Region("WeakA")
    weak_b = Region("WeakB")
    game = GameState(
        (
            Duchy("player", Unit()),
            Duchy("enemy", Unit()),
        )
    )

    # offensive + settlement kind → assault (M>N; settlement only, no N from
    # hostile party)
    assault_world = WorldMap(
        [home, enemy_camp],
        [(home, enemy_camp)],
        parties={home: Party(hero=Unit(), units=(), owner_id="player")},
        settlements={
            enemy_camp: Settlement(
                "EnemyS", population=2, owner_id="enemy"
            ),
        },
    )
    m = advantageous_target_count(assault_world, game, "player")
    n = threatened_position_count(assault_world, game, "player")
    assert net_posture(m, n) == "offensive"
    target = first_advantageous_target(assault_world, game, "player")
    assert target is not None
    region, kind = target
    assert kind == "settlement"
    regions_before = assault_world.regions
    parties_before = {r: assault_world.party_at(r) for r in assault_world.regions}
    settlements_before = {
        r: assault_world.settlement_at(r) for r in assault_world.regions
    }
    duchies_before = game.duchies
    assert recommended_order(assault_world, game, "player") == (
        "assault",
        region,
    )
    assert assault_world.regions == regions_before
    assert {
        r: assault_world.party_at(r) for r in assault_world.regions
    } == parties_before
    assert {
        r: assault_world.settlement_at(r) for r in assault_world.regions
    } == settlements_before
    assert game.duchies == duchies_before

    # offensive + party kind → engage (two weak hostile parties: M=2 > N=1)
    engage_world = WorldMap(
        [home, weak_a, weak_b],
        [(home, weak_a), (home, weak_b)],
        parties={
            home: Party(hero=Unit(), units=(), owner_id="player"),
            weak_a: Party(hero=Unit(), units=(), owner_id="enemy"),
            weak_b: Party(hero=Unit(), units=(), owner_id="enemy"),
        },
        settlements={},
    )
    m = advantageous_target_count(engage_world, game, "player")
    n = threatened_position_count(engage_world, game, "player")
    assert net_posture(m, n) == "offensive"
    target = first_advantageous_target(engage_world, game, "player")
    assert target is not None
    region, kind = target
    assert kind == "party"
    assert recommended_order(engage_world, game, "player") == (
        "engage",
        region,
    )


def test_recommended_order_defensive_defend_and_balanced_develop():
    """Defensive posture: ``recommended_order`` returns
    ``("defend", <region>)`` from ``first_threatened_region``. Balanced
    posture: ``("develop", None)``. Pure: no world/game mutation.
    """
    home = Region("Home")
    keep = Region("Keep")
    enemy_camp = Region("EnemyCamp")
    game = GameState(
        (
            Duchy("player", Unit()),
            Duchy("enemy", Unit()),
        )
    )

    # defensive: N>M — enemy party threatens keep; player party already
    # fielded so player_can_muster is False (posture path, not K48.1c muster)
    defensive_world = WorldMap(
        [keep, enemy_camp],
        [(keep, enemy_camp)],
        parties={
            keep: Party(hero=Unit(), units=(), owner_id="player"),
            enemy_camp: Party(hero=Unit(), units=(), owner_id="enemy"),
        },
        settlements={
            keep: Settlement("KeepS", population=2, owner_id="player"),
        },
    )
    m = advantageous_target_count(defensive_world, game, "player")
    n = threatened_position_count(defensive_world, game, "player")
    assert net_posture(m, n) == "defensive"
    threatened = first_threatened_region(defensive_world, game, "player")
    assert threatened is not None
    regions_before = defensive_world.regions
    parties_before = {
        r: defensive_world.party_at(r) for r in defensive_world.regions
    }
    settlements_before = {
        r: defensive_world.settlement_at(r) for r in defensive_world.regions
    }
    duchies_before = game.duchies
    assert recommended_order(defensive_world, game, "player") == (
        "defend",
        threatened,
    )
    assert defensive_world.regions == regions_before
    assert {
        r: defensive_world.party_at(r) for r in defensive_world.regions
    } == parties_before
    assert {
        r: defensive_world.settlement_at(r) for r in defensive_world.regions
    } == settlements_before
    assert game.duchies == duchies_before

    # balanced: M==N==0
    balanced_world = WorldMap(
        [home],
        [],
        parties={home: Party(hero=Unit(), units=(), owner_id="player")},
        settlements={},
    )
    m = advantageous_target_count(balanced_world, game, "player")
    n = threatened_position_count(balanced_world, game, "player")
    assert net_posture(m, n) == "balanced"
    assert recommended_order(balanced_world, game, "player") == (
        "develop",
        None,
    )


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


def test_render_recommended_action_data_posture_and_order_text_from_m_vs_n():
    """Known player: root has ``data-posture`` = ``net_posture(M, N)``
    (M=``advantageous_target_count``, N=``threatened_position_count``):
    ``"offensive"`` when M>N, ``"defensive"`` when N>M, ``"balanced"`` when
    M==N. Visible text: balanced → ``Zalecany rozkaz: rozwijaj księstwo``;
    offensive → first advantageous target named (``szturmuj osadę <region>``
    or ``zaatakuj oddział <region>``); defensive → first threatened region
    (``broń pozycji <region>`` via ``first_threatened_region``). Pure and
    deterministic (no world/game mutation).
    """
    home = Region("Home")
    keep = Region("Keep")
    enemy_camp = Region("EnemyCamp")
    game = GameState(
        (
            Duchy("player", Unit()),
            Duchy("enemy", Unit()),
        )
    )

    order_text = {
        "balanced": "Zalecany rozkaz: rozwijaj księstwo",
    }

    def _assert_recommended(
        world: WorldMap, expected: str, *, text: str | None = None
    ) -> None:
        n = threatened_position_count(world, game, "player")
        m = advantageous_target_count(world, game, "player")
        if expected == "offensive":
            assert m > n, f"{expected}: need M>N, got M={m} N={n}"
        elif expected == "defensive":
            assert n > m, f"{expected}: need N>M, got M={m} N={n}"
        else:
            assert m == n, f"{expected}: need M==N, got M={m} N={n}"
        assert net_posture(m, n) == expected

        regions_before = world.regions
        parties_before = {r: world.party_at(r) for r in world.regions}
        settlements_before = {
            r: world.settlement_at(r) for r in world.regions
        }
        duchies_before = game.duchies

        root = ET.fromstring(
            render_recommended_action(world, game, player_duchy_id="player")
        )
        assert root.tag == "div"
        assert root.attrib.get("data-recommended-action") == ""
        assert root.attrib.get("data-posture") == expected
        assert root.attrib.get("data-posture") == net_posture(m, n)
        expected_text = text if text is not None else order_text[expected]
        assert root.text == expected_text
        assert list(root) == []

        assert world.regions == regions_before
        assert {
            r: world.party_at(r) for r in world.regions
        } == parties_before
        assert {
            r: world.settlement_at(r) for r in world.regions
        } == settlements_before
        assert game.duchies == duchies_before

    # balanced: M==N==0 (isolated player party, no hostiles)
    balanced_world = WorldMap(
        [home],
        [],
        parties={home: Party(hero=Unit(), units=(), owner_id="player")},
        settlements={},
    )
    _assert_recommended(balanced_world, "balanced")

    # defensive: N>M — enemy party threatens keep; player party fielded so
    # player_can_muster is False (posture path, not K48.1c muster)
    defensive_world = WorldMap(
        [keep, enemy_camp],
        [(keep, enemy_camp)],
        parties={
            keep: Party(hero=Unit(), units=(), owner_id="player"),
            enemy_camp: Party(hero=Unit(), units=(), owner_id="enemy"),
        },
        settlements={
            keep: Settlement("KeepS", population=2, owner_id="player"),
        },
    )
    _assert_recommended(
        defensive_world,
        "defensive",
        text="Zalecany rozkaz: broń pozycji Keep",
    )

    # offensive: M>N — player party next to weak enemy settlement only
    # (hostile party required for N; settlement alone is an opportunity for M)
    offensive_world = WorldMap(
        [home, enemy_camp],
        [(home, enemy_camp)],
        parties={home: Party(hero=Unit(), units=(), owner_id="player")},
        settlements={
            enemy_camp: Settlement(
                "EnemyS", population=2, owner_id="enemy"
            ),
        },
    )
    _assert_recommended(
        offensive_world,
        "offensive",
        text="Zalecany rozkaz: szturmuj osadę EnemyCamp",
    )


def test_render_recommended_action_data_action_after_posture_from_kind():
    """Known player: root carries ``data-action`` immediately after
    ``data-posture``. Mapping: balanced → ``"develop"``; defensive →
    ``"defend"``; offensive with ``first_advantageous_target`` kind
    ``"settlement"`` → ``"assault"``, kind ``"party"`` → ``"engage"``.
    """
    home = Region("Home")
    keep = Region("Keep")
    enemy_camp = Region("EnemyCamp")
    weak_a = Region("WeakA")
    weak_b = Region("WeakB")
    game = GameState(
        (
            Duchy("player", Unit()),
            Duchy("enemy", Unit()),
        )
    )

    def _assert_action(
        world: WorldMap,
        expected_posture: str,
        expected_action: str,
        *,
        target_kind: str | None = None,
    ) -> None:
        m = advantageous_target_count(world, game, "player")
        n = threatened_position_count(world, game, "player")
        assert net_posture(m, n) == expected_posture
        if expected_posture == "offensive":
            target = first_advantageous_target(world, game, "player")
            assert target is not None
            assert target[1] == target_kind

        root = ET.fromstring(
            render_recommended_action(world, game, player_duchy_id="player")
        )
        keys = list(root.attrib.keys())
        posture_i = keys.index("data-posture")
        action_i = keys.index("data-action")
        assert action_i == posture_i + 1
        assert root.attrib["data-posture"] == expected_posture
        assert root.attrib["data-action"] == expected_action

    # balanced → develop
    balanced_world = WorldMap(
        [home],
        [],
        parties={home: Party(hero=Unit(), units=(), owner_id="player")},
        settlements={},
    )
    _assert_action(balanced_world, "balanced", "develop")

    # defensive → defend (player party fielded → can_muster False)
    defensive_world = WorldMap(
        [keep, enemy_camp],
        [(keep, enemy_camp)],
        parties={
            keep: Party(hero=Unit(), units=(), owner_id="player"),
            enemy_camp: Party(hero=Unit(), units=(), owner_id="enemy"),
        },
        settlements={
            keep: Settlement("KeepS", population=2, owner_id="player"),
        },
    )
    _assert_action(defensive_world, "defensive", "defend")

    # offensive + settlement kind → assault
    assault_world = WorldMap(
        [home, enemy_camp],
        [(home, enemy_camp)],
        parties={home: Party(hero=Unit(), units=(), owner_id="player")},
        settlements={
            enemy_camp: Settlement(
                "EnemyS", population=2, owner_id="enemy"
            ),
        },
    )
    _assert_action(
        assault_world, "offensive", "assault", target_kind="settlement"
    )

    # offensive + party kind → engage (two weak hostile parties: M=2 > N=1)
    engage_world = WorldMap(
        [home, weak_a, weak_b],
        [(home, weak_a), (home, weak_b)],
        parties={
            home: Party(hero=Unit(), units=(), owner_id="player"),
            weak_a: Party(hero=Unit(), units=(), owner_id="enemy"),
            weak_b: Party(hero=Unit(), units=(), owner_id="enemy"),
        },
        settlements={},
    )
    _assert_action(
        engage_world, "offensive", "engage", target_kind="party"
    )
