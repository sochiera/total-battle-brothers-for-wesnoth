"""Tests for the threat-alert presentation primitive (tbbui)."""

from xml.etree import ElementTree as ET

from tbb.duchy import Duchy
from tbb.game import GameState
from tbb.party import Party
from tbb.settlement import Settlement
from tbb.unit import Unit
from tbb.world import Region, WorldMap
from tbbui.threatalert import render_threat_alert


def test_render_threat_alert_empty_root_when_none_or_unknown_duchy():
    """When ``player_duchy_id`` is ``None`` or not in ``game.duchies``
    (``player_duchy(...) is None``), return a bare empty root
    ``<div data-threat-alert=""></div>`` with no ``data-threats``, no
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
        xml = render_threat_alert(
            world, game, player_duchy_id=player_duchy_id
        )
        root = ET.fromstring(xml)

        assert root.tag == "div"
        assert root.attrib == {"data-threat-alert": ""}
        assert "data-threats" not in root.attrib
        assert list(root) == []
        assert "".join(root.itertext()) == ""


def test_render_threat_alert_data_threats_count_and_label():
    """Known player: root has ``data-threats="N"`` and visible text
    ``Zagrożone pozycje: N``. ``N`` counts own positions (player settlement
    and/or party, separately per region and kind) that have ≥1 neighbor
    with ``party_at(neighbor).owner_id`` set and ``!= player_duchy_id``.
    No child rows at this stage; pure (no world/game mutation).
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

    regions_before = world.regions
    parties_before = {r: world.party_at(r) for r in world.regions}
    settlements_before = {r: world.settlement_at(r) for r in world.regions}
    duchies_before = game.duchies

    xml = render_threat_alert(world, game, player_duchy_id="player")
    root = ET.fromstring(xml)

    assert root.tag == "div"
    assert root.attrib.get("data-threat-alert") == ""
    assert root.attrib.get("data-threats") == str(expected_n)
    assert list(root) == []
    assert "".join(root.itertext()).strip() == f"Zagrożone pozycje: {expected_n}"

    assert world.regions == regions_before
    assert {r: world.party_at(r) for r in world.regions} == parties_before
    assert {
        r: world.settlement_at(r) for r in world.regions
    } == settlements_before
    assert game.duchies == duchies_before
