"""Tests for game-page HTML (observer party view, tbbui presentation layer)."""

from __future__ import annotations

import xml.etree.ElementTree as ET

from tbb.battle import BattleSide, HexBattle
from tbb.battlefield import Battlefield
from tbb.duchy import Duchy
from tbb.game import GameState
from tbb.hex import Hex
from tbb.party import Party
from tbb.settlement import Settlement
from tbb.terrain import PLAINS
from tbb.turn import Calendar
from tbb.unit import Unit
from tbb.world import Region, WorldMap
from tbbui.battlereport import render_battle_report
from tbbui.battlesvg import render_battle_svg
from tbbui.gamepage import render_game_page
from tbbui.ownerlegend import render_owner_legend
from tbbui.palette import owner_palette
from tbbui.partypanel import render_party_panel
from tbbui.settlementpanel import render_settlement_panel
from tbbui.worldsvg import render_world_svg


class ControlledRng:
    def __init__(self, result):
        self.result = result

    def chance(self, probability):
        return self.result


def _finished_battle_fixture() -> HexBattle:
    dead = Unit(training=3)
    dead_position = Hex(1, 0)
    battle = HexBattle(Battlefield()).deploy(
        Unit(), Hex(0, 0), BattleSide.ATTACKER
    ).deploy(dead, dead_position, BattleSide.DEFENDER)
    return battle.damage(dead_position, dead.hp).resolve_defeat(
        dead_position, ControlledRng(True)
    )


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _find_by_attr(root: ET.Element, attr: str) -> list[ET.Element]:
    return [el for el in root.iter() if el.get(attr) is not None]


def _ongoing_fixture() -> tuple[WorldMap, GameState, Calendar]:
    """Two contending duchies with known morale / settlement / party counts."""
    north_r = Region("north")
    south_r = Region("south")
    mid_r = Region("mid")
    n_keep = Settlement("North Keep", 3, owner_id="north")
    n_outpost = Settlement("North Outpost", 2, owner_id="north")
    s_keep = Settlement("South Keep", 4, owner_id="south")
    n_party = Party(Unit(), owner_id="north")
    world = WorldMap(
        (north_r, mid_r, south_r),
        ((north_r, mid_r), (mid_r, south_r)),
        settlements={north_r: n_keep, mid_r: n_outpost, south_r: s_keep},
        parties={mid_r: n_party},
    )
    game = GameState(
        (
            Duchy(
                "north",
                Unit(),
                morale=7,
                settlements=(n_keep, n_outpost),
                parties=(n_party,),
            ),
            Duchy(
                "south",
                Unit(),
                morale=3,
                settlements=(s_keep,),
                parties=(),
            ),
        )
    )
    calendar = Calendar(year=4, month=9)
    return world, game, calendar


def test_render_game_page_html_map_calendar_duchies_result_and_purity():
    """Parsable HTML: embedded map SVG, calendar, duchy panel, result; pure/det.

    Covers ongoing game plus winner and draw result modes from the contract.
    """
    world, game, calendar = _ongoing_fixture()
    regions_before = world.regions
    connections_before = world.connections
    duchies_before = game.duchies
    year_before = calendar.year
    month_before = calendar.month
    expected_svg = render_world_svg(world)

    html = render_game_page(world, game, calendar)

    root = ET.fromstring(html)
    assert _local(root.tag) == "html"

    svgs = [el for el in root.iter() if _local(el.tag) == "svg"]
    assert len(svgs) >= 1, "page must embed at least one map <svg>"
    # Canonical reuse: full string from render_world_svg must appear in the page.
    assert expected_svg in html, "page must embed render_world_svg(world) output"

    calendars = _find_by_attr(root, "data-calendar")
    assert len(calendars) == 1
    cal_el = calendars[0]
    assert cal_el.get("data-year") == str(calendar.year)
    assert cal_el.get("data-month") == str(calendar.month)
    assert (cal_el.text or "").strip() == f"Rok {calendar.year}, miesiąc {calendar.month}"

    duchy_els = _find_by_attr(root, "data-duchy")
    by_id = {el.get("data-duchy"): el for el in duchy_els}
    assert set(by_id) == {d.duchy_id for d in game.duchies}
    assert len(duchy_els) == len(game.duchies)
    for duchy in game.duchies:
        el = by_id[duchy.duchy_id]
        assert el.get("data-morale") == str(duchy.morale)
        assert el.get("data-settlements") == str(len(duchy.settlements))
        assert el.get("data-parties") == str(len(duchy.parties))

    results = _find_by_attr(root, "data-result")
    assert len(results) == 1
    assert results[0].get("data-result") == "ongoing"

    # Winner: sole undefeated duchy.
    won = GameState(
        (
            Duchy("north", Unit(), morale=7, settlements=(
                Settlement("North Keep", 3, owner_id="north"),
            )),
            Duchy("south", None, morale=0, settlements=()),
        )
    )
    assert won.is_over and won.winner is not None
    won_html = render_game_page(world, won, calendar)
    won_root = ET.fromstring(won_html)
    won_results = _find_by_attr(won_root, "data-result")
    assert len(won_results) == 1
    assert won_results[0].get("data-result") == won.winner.duchy_id

    # Draw: over without a winner.
    draw = GameState(
        (
            Duchy("north", None, morale=0, settlements=()),
            Duchy("south", None, morale=0, settlements=()),
        )
    )
    assert draw.is_over and draw.winner is None
    draw_html = render_game_page(world, draw, calendar)
    draw_root = ET.fromstring(draw_html)
    draw_results = _find_by_attr(draw_root, "data-result")
    assert len(draw_results) == 1
    assert draw_results[0].get("data-result") == "draw"

    # Pure and deterministic: same inputs → same string; no mutation.
    again = render_game_page(world, game, calendar)
    assert again == html
    assert world.regions is regions_before
    assert world.connections is connections_before
    assert world.regions == regions_before
    assert world.connections == connections_before
    assert game.duchies is duchies_before
    assert game.duchies == duchies_before
    assert calendar.year == year_before
    assert calendar.month == month_before


def test_render_game_page_embeds_human_readable_result_text_matching_data_result():
    """``data-result-text`` mirrors ``data-result`` with a human-readable string."""
    world, game, calendar = _ongoing_fixture()

    html = render_game_page(world, game, calendar)
    root = ET.fromstring(html)
    texts = _find_by_attr(root, "data-result-text")
    assert len(texts) == 1
    assert texts[0].get("data-result-text") == "Gra w toku"

    won = GameState(
        (
            Duchy("north", Unit(), morale=7, settlements=(
                Settlement("North Keep", 3, owner_id="north"),
            )),
            Duchy("south", None, morale=0, settlements=()),
        )
    )
    won_html = render_game_page(world, won, calendar)
    won_root = ET.fromstring(won_html)
    won_texts = _find_by_attr(won_root, "data-result-text")
    assert len(won_texts) == 1
    assert won_texts[0].get("data-result-text") == f"Zwycięstwo: {won.winner.duchy_id}"

    draw = GameState(
        (
            Duchy("north", None, morale=0, settlements=()),
            Duchy("south", None, morale=0, settlements=()),
        )
    )
    draw_html = render_game_page(world, draw, calendar)
    draw_root = ET.fromstring(draw_html)
    draw_texts = _find_by_attr(draw_root, "data-result-text")
    assert len(draw_texts) == 1
    assert draw_texts[0].get("data-result-text") == "Remis"


def test_render_game_page_duchy_panel_has_human_readable_status_text():
    """Each ``data-duchy`` element contains a human-readable status line."""
    world, game, calendar = _ongoing_fixture()

    html = render_game_page(world, game, calendar)
    root = ET.fromstring(html)

    duchy_els = _find_by_attr(root, "data-duchy")
    by_id = {el.get("data-duchy"): el for el in duchy_els}
    assert len(duchy_els) == len(game.duchies)

    for duchy in game.duchies:
        el = by_id[duchy.duchy_id]
        expected_text = (
            f"{duchy.duchy_id}: osady {len(duchy.settlements)}, "
            f"party {len(duchy.parties)}, morale {duchy.morale}"
        )
        assert (el.text or "").strip() == expected_text
        # Machine-readable attributes remain unchanged alongside the new text.
        assert el.get("data-morale") == str(duchy.morale)
        assert el.get("data-settlements") == str(len(duchy.settlements))
        assert el.get("data-parties") == str(len(duchy.parties))


def test_render_game_page_optional_battle_slot_embeds_svg_and_defaults_unchanged():
    """``battle`` param embeds ``render_battle_svg(battle)``; default output is unchanged."""
    world, game, calendar = _ongoing_fixture()
    baseline_html = render_game_page(world, game, calendar)

    battle_hex = Hex(0, 0)
    battlefield = Battlefield({battle_hex: PLAINS})
    battle = HexBattle(battlefield).deploy(Unit(), battle_hex, BattleSide.ATTACKER)
    expected_battle_svg = render_battle_svg(battle)

    # Default (no battle arg) must be byte-for-byte identical to before.
    assert render_game_page(world, game, calendar) == baseline_html

    html_with_battle = render_game_page(world, game, calendar, battle=battle)
    assert html_with_battle != baseline_html
    assert expected_battle_svg in html_with_battle, (
        "page must embed render_battle_svg(battle) output when battle is given"
    )

    root = ET.fromstring(html_with_battle)
    assert _local(root.tag) == "html"

    # Explicit battle=None must equal the default (byte-for-byte).
    assert render_game_page(world, game, calendar, battle=None) == baseline_html


def test_render_game_page_result_text_present_with_battle_and_battle_not_mutated():
    """``data-result-text`` is emitted regardless of ``battle``; ``battle`` unmutated."""
    world, game, calendar = _ongoing_fixture()
    battle = _finished_battle_fixture()
    battle_before = battle

    html_with_battle = render_game_page(world, game, calendar, battle=battle)

    root = ET.fromstring(html_with_battle)
    texts = _find_by_attr(root, "data-result-text")
    assert len(texts) == 1
    assert texts[0].get("data-result-text") == "Gra w toku"

    assert battle is battle_before
    assert battle == _finished_battle_fixture()


def test_render_game_page_embeds_canonical_settlement_panel_with_matching_rows():
    """Page embeds ``render_settlement_panel(world)`` verbatim; rows match settlements."""
    world, game, calendar = _ongoing_fixture()
    expected_panel = render_settlement_panel(world)

    html = render_game_page(world, game, calendar)
    assert expected_panel in html, (
        "page must embed render_settlement_panel(world) output"
    )

    root = ET.fromstring(html)
    panels = _find_by_attr(root, "data-settlement-panel")
    assert len(panels) == 1

    settlement_regions = [
        region for region in world.regions if world.settlement_at(region) is not None
    ]
    row_els = _find_by_attr(root, "data-settlement-row")
    assert [el.get("data-settlement-row") for el in row_els] == [
        region.name for region in settlement_regions
    ]


def test_render_game_page_embeds_canonical_party_panel_with_matching_rows():
    """Page embeds ``render_party_panel(world)`` verbatim; rows match parties."""
    world, game, calendar = _ongoing_fixture()
    expected_panel = render_party_panel(world)

    html = render_game_page(world, game, calendar)
    assert expected_panel in html, (
        "page must embed render_party_panel(world) output"
    )

    root = ET.fromstring(html)
    panels = _find_by_attr(root, "data-party-panel")
    assert len(panels) == 1

    party_regions = [
        region for region in world.regions if world.party_at(region) is not None
    ]
    row_els = _find_by_attr(root, "data-party-row")
    assert [el.get("data-party-row") for el in row_els] == [
        region.name for region in party_regions
    ]


def test_render_game_page_embeds_canonical_owner_legend_with_matching_rows():
    """Page embeds ``render_owner_legend(world)`` verbatim; rows match owner_palette."""
    world, game, calendar = _ongoing_fixture()
    expected_legend = render_owner_legend(world)

    html = render_game_page(world, game, calendar)
    assert expected_legend in html, (
        "page must embed render_owner_legend(world) output"
    )

    root = ET.fromstring(html)
    legends = _find_by_attr(root, "data-owner-legend")
    assert len(legends) == 1

    row_els = _find_by_attr(root, "data-owner-legend-row")
    assert [el.get("data-owner-legend-row") for el in row_els] == list(
        owner_palette(world)
    )


def test_render_game_page_marks_player_duchy_with_attribute_and_prefix():
    """``player_duchy_id`` flags the matching ``data-duchy`` element only."""
    world, game, calendar = _ongoing_fixture()
    baseline_html = render_game_page(world, game, calendar)

    # Default (no player_duchy_id) and explicit None must be byte-for-byte identical.
    assert render_game_page(world, game, calendar, player_duchy_id=None) == baseline_html

    html = render_game_page(world, game, calendar, player_duchy_id="north")
    root = ET.fromstring(html)

    duchy_els = _find_by_attr(root, "data-duchy")
    by_id = {el.get("data-duchy"): el for el in duchy_els}
    assert len(duchy_els) == len(game.duchies)

    north_el = by_id["north"]
    assert north_el.get("data-player-duchy") == ""
    assert (north_el.text or "").strip().startswith("» ")

    south_el = by_id["south"]
    assert south_el.get("data-player-duchy") is None
    assert not (south_el.text or "").strip().startswith("» ")


def test_render_game_page_passes_player_duchy_id_to_settlement_panel():
    """``player_duchy_id`` reaches the settlement panel: matching rows flagged."""
    world, game, calendar = _ongoing_fixture()
    expected_panel = render_settlement_panel(world, "north")

    html = render_game_page(world, game, calendar, player_duchy_id="north")
    assert expected_panel in html, (
        "page must embed render_settlement_panel(world, player_duchy_id) output"
    )

    root = ET.fromstring(html)
    row_els = _find_by_attr(root, "data-settlement-row")
    by_region = {el.get("data-settlement-row"): el for el in row_els}

    for region in world.regions:
        settlement = world.settlement_at(region)
        if settlement is None:
            continue
        el = by_region[region.name]
        if settlement.owner_id == "north":
            assert el.get("data-player-owned") == ""
        else:
            assert el.get("data-player-owned") is None


def test_render_game_page_passes_player_duchy_id_to_party_panel():
    """``player_duchy_id`` reaches the party panel: matching rows flagged."""
    world, game, calendar = _ongoing_fixture()
    expected_panel = render_party_panel(world, "north")

    html = render_game_page(world, game, calendar, player_duchy_id="north")
    assert expected_panel in html, (
        "page must embed render_party_panel(world, player_duchy_id) output"
    )

    root = ET.fromstring(html)
    row_els = _find_by_attr(root, "data-party-row")
    by_region = {el.get("data-party-row"): el for el in row_els}

    for region in world.regions:
        party = world.party_at(region)
        if party is None:
            continue
        el = by_region[region.name]
        if party.owner_id == "north":
            assert el.get("data-player-owned") == ""
        else:
            assert el.get("data-player-owned") is None


def test_render_game_page_embeds_battle_report_matching_battle_report_counts():
    """``data-battle-report`` is present with battle, absent without; counts match."""
    world, game, calendar = _ongoing_fixture()
    battle = _finished_battle_fixture()
    expected_report_html = render_battle_report(battle)

    html_with_battle = render_game_page(world, game, calendar, battle=battle)
    assert expected_report_html in html_with_battle, (
        "page must embed render_battle_report(battle) output when battle is given"
    )

    root = ET.fromstring(html_with_battle)
    report_els = _find_by_attr(root, "data-battle-report")
    assert len(report_els) == 1

    html_without_battle = render_game_page(world, game, calendar)
    without_root = ET.fromstring(html_without_battle)
    assert _find_by_attr(without_root, "data-battle-report") == []
