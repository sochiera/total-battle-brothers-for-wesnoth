"""Tests for the situation-report presentation primitive (tbbui)."""

from xml.etree import ElementTree as ET

from tbb.duchy import Duchy
from tbb.game import GameState
from tbb.party import Party
from tbb.settlement import Settlement
from tbb.unit import Unit
from tbb.world import Region, WorldMap
from tbbui.engagementpreview import advantageous_target_count
from tbbui.situationreport import render_situation_report
from tbbui.threatalert import render_threat_alert, threatened_position_count


def test_render_situation_report_empty_root_when_none_or_unknown_duchy():
    """When ``player_duchy_id`` is ``None`` or not in ``game.duchies``
    (``player_duchy(...) is None``), return a bare empty root
    ``<div data-situation-report=""></div>`` with no ``data-threatened-count``,
    no ``data-opportunity-count``, no visible text, and no children. Does not
    depend on world parties or settlements.
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
        xml = render_situation_report(
            world, game, player_duchy_id=player_duchy_id
        )
        root = ET.fromstring(xml)

        assert root.tag == "div"
        assert root.attrib == {"data-situation-report": ""}
        assert "data-threatened-count" not in root.attrib
        assert "data-opportunity-count" not in root.attrib
        assert list(root) == []
        assert "".join(root.itertext()) == ""


def test_render_situation_report_threatened_count_and_label():
    """Known player: root has ``data-threatened-count="N"``,
    ``data-opportunity-count="M"`` and visible text
    ``Sytuacja: zagrożone pozycje N, korzystne cele M``. ``N`` counts own
    positions (player settlement and/or party, separately per region and kind)
    that have ≥1 neighbor with ``party_at(neighbor).owner_id`` set and
    ``!= player_duchy_id`` — same rule as ``render_threat_alert``. ``M`` is
    ``advantageous_target_count``. Pure (no world/game mutation).
    """
    home = Region("Home")
    keep = Region("Keep")
    fort = Region("Fort")
    safe = Region("Safe")
    enemy_camp = Region("EnemyCamp")
    neutral_camp = Region("NeutralCamp")
    ally_camp = Region("AllyCamp")

    # Topology (all of home/keep/fort adj. to enemy_camp; safe only to fort/ally):
    # home party only → 1; keep settlement only → 1; fort party+settlement → 2;
    # safe party (neighbors: player party / same-owner ally) → 0. Total N = 4.
    # neutral (owner_id=None) and same-owner ally do not count as threats.
    world = WorldMap(
        [home, keep, fort, safe, enemy_camp, neutral_camp, ally_camp],
        [
            (home, enemy_camp),
            (keep, enemy_camp),
            (fort, enemy_camp),
            (home, fort),
            (fort, safe),
            (enemy_camp, neutral_camp),
            (safe, ally_camp),
        ],
        parties={
            home: Party(hero=Unit(), units=(), owner_id="player"),
            fort: Party(hero=Unit(), units=(), owner_id="player"),
            safe: Party(hero=Unit(), units=(), owner_id="player"),
            enemy_camp: Party(hero=Unit(), units=(), owner_id="enemy"),
            # unowned / ally neighbors must not create threats for safe
            neutral_camp: Party(hero=Unit(), units=(), owner_id=None),
            ally_camp: Party(hero=Unit(), units=(), owner_id="player"),
        },
        settlements={
            keep: Settlement("KeepS", population=2, owner_id="player"),
            fort: Settlement("FortS", population=2, owner_id="player"),
            # enemy settlement next to home is irrelevant for threat count
            enemy_camp: Settlement(
                "EnemyS", population=2, owner_id="enemy"
            ),
        },
    )
    game = GameState(
        (
            Duchy("player", Unit()),
            Duchy("enemy", Unit()),
        )
    )

    # Threatened: home party, keep settlement, fort party, fort settlement → 4
    # safe party has only ally/unowned-adjacent via ally_camp (same owner) → 0
    expected_n = 4
    expected_m = advantageous_target_count(world, game, "player")

    regions_before = world.regions
    parties_before = {r: world.party_at(r) for r in world.regions}
    settlements_before = {r: world.settlement_at(r) for r in world.regions}
    duchies_before = game.duchies

    xml = render_situation_report(world, game, player_duchy_id="player")
    root = ET.fromstring(xml)

    assert root.tag == "div"
    assert root.attrib.get("data-situation-report") == ""
    assert root.attrib.get("data-threatened-count") == str(expected_n)
    assert root.attrib.get("data-opportunity-count") == str(expected_m)
    assert root.text == (
        f"Sytuacja: zagrożone pozycje {expected_n}, korzystne cele {expected_m}"
    )
    assert list(root) == []

    assert world.regions == regions_before
    assert {r: world.party_at(r) for r in world.regions} == parties_before
    assert {
        r: world.settlement_at(r) for r in world.regions
    } == settlements_before
    assert game.duchies == duchies_before


def test_render_situation_report_count_from_threatened_position_count():
    """``N`` comes from ``threatalert.threatened_position_count`` (shared with
    ``render_threat_alert`` / ``_threatened_rows``), not from parsing alert HTML.
    ``M`` comes from ``advantageous_target_count``. Known player with zero
    threats still yields ``data-threatened-count="0"`` and matching label;
    unknown player: helpers return 0 while report stays empty.
    Pure (no world/game mutation).
    """
    home = Region("Home")
    keep = Region("Keep")
    enemy_camp = Region("EnemyCamp")
    world = WorldMap(
        [home, keep, enemy_camp],
        [(home, enemy_camp), (keep, enemy_camp)],
        parties={
            home: Party(hero=Unit(), units=(), owner_id="player"),
            enemy_camp: Party(hero=Unit(), units=(), owner_id="enemy"),
        },
        settlements={
            keep: Settlement("KeepS", population=2, owner_id="player"),
        },
    )
    game = GameState(
        (
            Duchy("player", Unit()),
            Duchy("enemy", Unit()),
        )
    )

    regions_before = world.regions
    parties_before = {r: world.party_at(r) for r in world.regions}
    settlements_before = {r: world.settlement_at(r) for r in world.regions}
    duchies_before = game.duchies

    n = threatened_position_count(world, game, "player")
    m = advantageous_target_count(world, game, "player")
    assert n == 2  # home party + keep settlement

    xml = render_situation_report(world, game, player_duchy_id="player")
    root = ET.fromstring(xml)
    assert root.attrib.get("data-threatened-count") == str(n)
    assert root.attrib.get("data-opportunity-count") == str(m)
    assert root.text == f"Sytuacja: zagrożone pozycje {n}, korzystne cele {m}"

    # Same N as threat-alert root attribute (shared source, not HTML scrape)
    alert_root = ET.fromstring(
        render_threat_alert(world, game, player_duchy_id="player")
    )
    assert alert_root.attrib.get("data-threats") == str(n)

    # Isolated: count helper alone, without rendering either panel
    assert threatened_position_count(world, game, "player") == n

    # Unknown player: count is 0; situation report remains bare empty root
    assert threatened_position_count(world, game, None) == 0
    assert threatened_position_count(world, game, "missing") == 0
    empty = ET.fromstring(
        render_situation_report(world, game, player_duchy_id=None)
    )
    assert "data-threatened-count" not in empty.attrib
    assert "data-opportunity-count" not in empty.attrib

    # Known player, zero threats
    safe_only = WorldMap(
        [home],
        [],
        parties={home: Party(hero=Unit(), units=(), owner_id="player")},
        settlements={},
    )
    assert threatened_position_count(safe_only, game, "player") == 0
    assert advantageous_target_count(safe_only, game, "player") == 0
    zero = ET.fromstring(
        render_situation_report(safe_only, game, player_duchy_id="player")
    )
    assert zero.attrib.get("data-threatened-count") == "0"
    assert zero.attrib.get("data-opportunity-count") == "0"
    assert zero.text == "Sytuacja: zagrożone pozycje 0, korzystne cele 0"

    assert world.regions == regions_before
    assert {r: world.party_at(r) for r in world.regions} == parties_before
    assert {
        r: world.settlement_at(r) for r in world.regions
    } == settlements_before
    assert game.duchies == duchies_before
