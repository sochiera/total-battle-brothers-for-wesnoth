"""Tests for the recommended-action presentation primitive (tbbui)."""

from xml.etree import ElementTree as ET

from tbb.duchy import Duchy
from tbb.game import GameState
from tbb.party import Party
from tbb.settlement import Settlement
from tbb.unit import Unit
from tbb.world import Region, WorldMap
from tbbui.engagementpreview import advantageous_target_count
from tbbui.recommendedaction import render_recommended_action
from tbbui.situationreport import net_posture
from tbbui.threatalert import threatened_position_count


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
    or ``zaatakuj oddział <region>``); defensive → ``Zalecany rozkaz:
    broń się``. Pure and deterministic (no world/game mutation).
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
        "defensive": "Zalecany rozkaz: broń się",
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

    # defensive: N>M — enemy party threatens keep settlement; player has no
    # party so M=0, N=1
    defensive_world = WorldMap(
        [keep, enemy_camp],
        [(keep, enemy_camp)],
        parties={
            enemy_camp: Party(hero=Unit(), units=(), owner_id="enemy"),
        },
        settlements={
            keep: Settlement("KeepS", population=2, owner_id="player"),
        },
    )
    _assert_recommended(defensive_world, "defensive")

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
