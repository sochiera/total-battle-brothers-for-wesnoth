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
from tbbui.playersummary import render_player_summary
from tbbui.settlementpanel import render_settlement_panel
from tbbui.engagementpreview import render_engagement_preview
from tbbui.herochase import render_hero_chase
from tbbui.herolocator import render_enemy_hero_locator
from tbbui.nextobjective import render_next_objective
from tbbui.threatalert import render_threat_alert
from tbbui.turnsummary import render_turn_summary
from tbbui.victoryprogress import render_victory_progress
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
        hero_label = "tak" if duchy.has_hero else "nie"
        heir_label = "tak" if duchy.heir is not None else "nie"
        expected_text = (
            f"{duchy.duchy_id}: osady {len(duchy.settlements)}, "
            f"party {len(duchy.parties)}, morale {duchy.morale}, "
            f"bohater {hero_label}, dziedzic {heir_label}"
        )
        assert (el.text or "").strip() == expected_text
        # Machine-readable attributes remain unchanged alongside the new text.
        assert el.get("data-morale") == str(duchy.morale)
        assert el.get("data-settlements") == str(len(duchy.settlements))
        assert el.get("data-parties") == str(len(duchy.parties))
        assert el.get("data-hero") == ("true" if duchy.has_hero else "false")
        assert el.get("data-heir") == (
            "true" if duchy.heir is not None else "false"
        )


def test_render_game_page_duchy_panel_shows_hero_presence():
    """``data-duchy`` gets ``data-hero`` flag and text suffix from ``has_hero``."""
    north_r = Region("north")
    south_r = Region("south")
    n_keep = Settlement("North Keep", 3, owner_id="north")
    s_keep = Settlement("South Keep", 4, owner_id="south")
    world = WorldMap(
        (north_r, south_r),
        ((north_r, south_r),),
        settlements={north_r: n_keep, south_r: s_keep},
    )
    game = GameState(
        (
            Duchy("north", Unit(), morale=7, settlements=(n_keep,)),
            Duchy("south", None, morale=3, settlements=(s_keep,)),
        )
    )
    calendar = Calendar(year=4, month=9)

    html = render_game_page(world, game, calendar)
    root = ET.fromstring(html)

    duchy_els = _find_by_attr(root, "data-duchy")
    by_id = {el.get("data-duchy"): el for el in duchy_els}

    north_el = by_id["north"]
    assert north_el.get("data-hero") == "true"
    assert ", bohater tak" in (north_el.text or "")

    south_el = by_id["south"]
    assert south_el.get("data-hero") == "false"
    assert ", bohater nie" in (south_el.text or "")


def test_render_game_page_duchy_panel_shows_heir_presence():
    """``data-duchy`` gets ``data-heir`` flag and text suffix from ``duchy.heir``."""
    north_r = Region("north")
    south_r = Region("south")
    n_keep = Settlement("North Keep", 3, owner_id="north")
    s_keep = Settlement("South Keep", 4, owner_id="south")
    world = WorldMap(
        (north_r, south_r),
        ((north_r, south_r),),
        settlements={north_r: n_keep, south_r: s_keep},
    )
    game = GameState(
        (
            Duchy("north", Unit(), heir=Unit(), morale=7, settlements=(n_keep,)),
            Duchy("south", Unit(), morale=3, settlements=(s_keep,)),
        )
    )
    calendar = Calendar(year=4, month=9)

    html = render_game_page(world, game, calendar)
    root = ET.fromstring(html)

    duchy_els = _find_by_attr(root, "data-duchy")
    by_id = {el.get("data-duchy"): el for el in duchy_els}

    north_el = by_id["north"]
    assert north_el.get("data-heir") == "true"
    assert ", dziedzic tak" in (north_el.text or "")
    assert (north_el.text or "").index(", bohater tak") < (
        north_el.text or ""
    ).index(", dziedzic tak")

    south_el = by_id["south"]
    assert south_el.get("data-heir") == "false"
    assert ", dziedzic nie" in (south_el.text or "")


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


def test_render_game_page_settlements_header_precedes_settlement_panel():
    """A single settlements ``<h2>`` sits immediately before the settlement panel."""
    world, game, calendar = _ongoing_fixture()
    expected_panel = render_settlement_panel(world)
    header = '<h2 data-panel-section="settlements">Osady</h2>'

    html = render_game_page(world, game, calendar)

    assert html.count(header) == 1
    assert html.index(header) + len(header) == html.index(expected_panel), (
        "header must sit directly before the embedded settlement panel"
    )

    root = ET.fromstring(html)
    headers = _find_by_attr(root, "data-panel-section")
    assert [el.get("data-panel-section") for el in headers] == [
        "settlements",
        "parties",
        "duchies",
    ]
    assert [el.text for el in headers] == ["Osady", "Oddziały", "Księstwa"]


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


def test_render_game_page_parties_header_precedes_party_panel():
    """A single parties ``<h2>`` sits immediately before the embedded party panel."""
    world, game, calendar = _ongoing_fixture()
    expected_panel = render_party_panel(world)
    header = '<h2 data-panel-section="parties">Oddziały</h2>'

    html = render_game_page(world, game, calendar)

    assert html.count(header) == 1
    assert html.index(header) + len(header) == html.index(expected_panel), (
        "header must sit directly before the embedded party panel"
    )

    root = ET.fromstring(html)
    headers = _find_by_attr(root, "data-panel-section")
    assert [el.get("data-panel-section") for el in headers] == [
        "settlements",
        "parties",
        "duchies",
    ]
    assert [el.text for el in headers] == ["Osady", "Oddziały", "Księstwa"]


def test_render_game_page_duchies_header_precedes_first_duchy_row():
    """A single duchies ``<h2>`` sits immediately before the first ``data-duchy`` row."""
    world, game, calendar = _ongoing_fixture()
    header = '<h2 data-panel-section="duchies">Księstwa</h2>'

    html = render_game_page(world, game, calendar)

    assert html.count(header) == 1
    first_duchy_row_start = f'<div data-duchy="{game.duchies[0].duchy_id}"'
    assert html.index(header) + len(header) == html.index(first_duchy_row_start), (
        "header must sit directly before the first data-duchy row"
    )

    root = ET.fromstring(html)
    headers = _find_by_attr(root, "data-panel-section")
    assert [el.get("data-panel-section") for el in headers] == [
        "settlements",
        "parties",
        "duchies",
    ]
    assert [el.text for el in headers] == ["Osady", "Oddziały", "Księstwa"]


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


def test_render_game_page_passes_player_duchy_id_to_owner_legend():
    """``player_duchy_id`` reaches the owner legend: matching row flagged."""
    world, game, calendar = _ongoing_fixture()
    expected_legend = render_owner_legend(world, "north")

    html = render_game_page(world, game, calendar, player_duchy_id="north")
    assert expected_legend in html, (
        "page must embed render_owner_legend(world, player_duchy_id) output"
    )

    root = ET.fromstring(html)
    row_els = _find_by_attr(root, "data-owner-legend-row")
    by_owner = {el.get("data-owner-legend-row"): el for el in row_els}

    for owner_id in owner_palette(world):
        el = by_owner[owner_id]
        if owner_id == "north":
            assert el.get("data-player-owner") == ""
        else:
            assert el.get("data-player-owner") is None


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


def test_render_game_page_embeds_canonical_player_summary_when_player_duchy_id_set():
    """``player_duchy_id`` embeds one canonical ``render_player_summary`` in body."""
    world, game, calendar = _ongoing_fixture()
    expected_summary = render_player_summary(game, "north")

    html = render_game_page(world, game, calendar, player_duchy_id="north")
    assert expected_summary in html, (
        "page must embed render_player_summary(game, player_duchy_id) output"
    )

    root = ET.fromstring(html)
    assert _local(root.tag) == "html"
    body = next(el for el in root if _local(el.tag) == "body")
    summary_els = _find_by_attr(root, "data-player-summary")
    assert len(summary_els) == 1
    assert summary_els[0] in list(body.iter())


def test_render_game_page_embeds_canonical_victory_progress_after_player_summary():
    """``player_duchy_id`` embeds one canonical ``render_victory_progress`` right after summary.

    Exactly one ``data-victory-progress`` in ``<body>``; string equals
    ``render_victory_progress(game, player_duchy_id)`` and sits immediately after
    the embedded ``render_player_summary`` output.
    """
    world, game, calendar = _ongoing_fixture()
    expected_summary = render_player_summary(game, "north")
    expected_progress = render_victory_progress(game, "north")

    html = render_game_page(world, game, calendar, player_duchy_id="north")

    assert expected_progress in html, (
        "page must embed render_victory_progress(game, player_duchy_id) output"
    )
    assert html.count(expected_progress) == 1
    assert html.index(expected_summary) + len(expected_summary) == html.index(
        expected_progress
    ), "victory progress must sit directly after the embedded player summary"

    root = ET.fromstring(html)
    assert _local(root.tag) == "html"
    body = next(el for el in root if _local(el.tag) == "body")
    progress_els = _find_by_attr(root, "data-victory-progress")
    assert len(progress_els) == 1
    assert progress_els[0] in list(body.iter())


def test_render_game_page_embeds_canonical_next_objective_after_victory_progress():
    """``player_duchy_id`` embeds one canonical ``render_next_objective`` right after progress.

    Exactly one ``data-next-objective`` in ``<body>``; string equals
    ``render_next_objective(game, player_duchy_id)`` and sits immediately after
    the embedded ``render_victory_progress`` output.
    """
    world, game, calendar = _ongoing_fixture()
    expected_progress = render_victory_progress(game, "north")
    expected_objective = render_next_objective(game, "north")

    html = render_game_page(world, game, calendar, player_duchy_id="north")

    assert expected_objective in html, (
        "page must embed render_next_objective(game, player_duchy_id) output"
    )
    assert html.count(expected_objective) == 1
    assert html.index(expected_progress) + len(expected_progress) == html.index(
        expected_objective
    ), "next objective must sit directly after the embedded victory progress"

    root = ET.fromstring(html)
    assert _local(root.tag) == "html"
    body = next(el for el in root if _local(el.tag) == "body")
    objective_els = _find_by_attr(root, "data-next-objective")
    assert len(objective_els) == 1
    assert objective_els[0] in list(body.iter())


def test_render_game_page_embeds_canonical_enemy_hero_locator_after_next_objective():
    """``player_duchy_id`` embeds one canonical ``render_enemy_hero_locator`` after objective.

    Exactly one ``data-hero-locator`` in ``<body>``; string equals
    ``render_enemy_hero_locator(world, game, player_duchy_id)`` and sits
    immediately after the embedded ``render_next_objective`` output.
    """
    world, game, calendar = _ongoing_fixture()
    expected_objective = render_next_objective(game, "north")
    expected_locator = render_enemy_hero_locator(world, game, "north")

    html = render_game_page(world, game, calendar, player_duchy_id="north")

    assert expected_locator in html, (
        "page must embed render_enemy_hero_locator(world, game, player_duchy_id) "
        "output"
    )
    assert html.count(expected_locator) == 1
    assert html.index(expected_objective) + len(expected_objective) == html.index(
        expected_locator
    ), "hero locator must sit directly after the embedded next objective"

    root = ET.fromstring(html)
    assert _local(root.tag) == "html"
    body = next(el for el in root if _local(el.tag) == "body")
    locator_els = _find_by_attr(root, "data-hero-locator")
    assert len(locator_els) == 1
    assert locator_els[0] in list(body.iter())


def test_render_game_page_embeds_canonical_hero_chase_after_hero_locator():
    """``player_duchy_id`` embeds one canonical ``render_hero_chase`` after locator.

    Exactly one ``data-hero-chase`` in ``<body>``; string equals
    ``render_hero_chase(world, game, player_duchy_id)`` and sits
    immediately after the embedded ``render_enemy_hero_locator`` output.
    """
    world, game, calendar = _ongoing_fixture()
    expected_locator = render_enemy_hero_locator(world, game, "north")
    expected_chase = render_hero_chase(world, game, "north")

    html = render_game_page(world, game, calendar, player_duchy_id="north")

    assert expected_chase in html, (
        "page must embed render_hero_chase(world, game, player_duchy_id) output"
    )
    assert html.count(expected_chase) == 1
    assert html.index(expected_locator) + len(expected_locator) == html.index(
        expected_chase
    ), "hero chase must sit directly after the embedded hero locator"

    root = ET.fromstring(html)
    assert _local(root.tag) == "html"
    body = next(el for el in root if _local(el.tag) == "body")
    chase_els = _find_by_attr(root, "data-hero-chase")
    assert len(chase_els) == 1
    assert chase_els[0] in list(body.iter())


def test_render_game_page_embeds_canonical_engagement_preview_after_hero_chase():
    """``player_duchy_id`` embeds one canonical ``render_engagement_preview`` after chase.

    Exactly one ``data-engagement-preview`` in ``<body>``; string equals
    ``render_engagement_preview(world, game, player_duchy_id)`` and sits
    immediately after the embedded ``render_hero_chase`` output
    (``data-hero-chase`` before ``data-engagement-preview``).
    """
    world, game, calendar = _ongoing_fixture()
    expected_chase = render_hero_chase(world, game, "north")
    expected_preview = render_engagement_preview(world, game, "north")

    html = render_game_page(world, game, calendar, player_duchy_id="north")

    assert expected_preview in html, (
        "page must embed render_engagement_preview(world, game, player_duchy_id) "
        "output"
    )
    assert html.count(expected_preview) == 1
    assert html.index(expected_chase) + len(expected_chase) == html.index(
        expected_preview
    ), "engagement preview must sit directly after the embedded hero chase"

    root = ET.fromstring(html)
    assert _local(root.tag) == "html"
    body = next(el for el in root if _local(el.tag) == "body")
    preview_els = _find_by_attr(root, "data-engagement-preview")
    assert len(preview_els) == 1
    assert preview_els[0] in list(body.iter())
    chase_els = _find_by_attr(root, "data-hero-chase")
    assert len(chase_els) == 1
    body_order = list(body.iter())
    assert body_order.index(chase_els[0]) < body_order.index(
        preview_els[0]
    ), "data-hero-chase must precede data-engagement-preview in body"


def test_render_game_page_omits_engagement_preview_when_player_duchy_id_none():
    """Default / explicit ``player_duchy_id=None``: no ``data-engagement-preview``.

    Default and explicit None are byte-for-byte identical (no engagement preview).
    """
    world, game, calendar = _ongoing_fixture()
    baseline_html = render_game_page(world, game, calendar)

    assert render_game_page(world, game, calendar, player_duchy_id=None) == baseline_html

    root = ET.fromstring(baseline_html)
    assert _find_by_attr(root, "data-engagement-preview") == []
    assert "data-engagement-preview" not in baseline_html


def test_render_game_page_embeds_canonical_threat_alert_after_engagement_preview():
    """``player_duchy_id`` embeds one canonical ``render_threat_alert`` after preview.

    Exactly one ``data-threat-alert`` in ``<body>``; string equals
    ``render_threat_alert(world, game, player_duchy_id)`` and sits
    immediately after the embedded ``render_engagement_preview`` output
    (``data-engagement-preview`` before ``data-threat-alert``, before
    ``data-duchy`` rows).
    """
    world, game, calendar = _ongoing_fixture()
    expected_preview = render_engagement_preview(world, game, "north")
    expected_alert = render_threat_alert(world, game, "north")

    html = render_game_page(world, game, calendar, player_duchy_id="north")

    assert expected_alert in html, (
        "page must embed render_threat_alert(world, game, player_duchy_id) "
        "output"
    )
    assert html.count(expected_alert) == 1
    assert html.index(expected_preview) + len(expected_preview) == html.index(
        expected_alert
    ), "threat alert must sit directly after the embedded engagement preview"

    root = ET.fromstring(html)
    assert _local(root.tag) == "html"
    body = next(el for el in root if _local(el.tag) == "body")
    alert_els = _find_by_attr(root, "data-threat-alert")
    assert len(alert_els) == 1
    assert alert_els[0] in list(body.iter())
    preview_els = _find_by_attr(root, "data-engagement-preview")
    assert len(preview_els) == 1
    duchy_els = _find_by_attr(root, "data-duchy")
    assert duchy_els, "fixture must include data-duchy rows"
    body_order = list(body.iter())
    assert body_order.index(preview_els[0]) < body_order.index(
        alert_els[0]
    ), "data-engagement-preview must precede data-threat-alert in body"
    assert body_order.index(alert_els[0]) < body_order.index(
        duchy_els[0]
    ), "data-threat-alert must precede data-duchy rows in body"


def test_render_game_page_omits_threat_alert_when_player_duchy_id_none():
    """Default / explicit ``player_duchy_id=None``: no ``data-threat-alert``.

    Default and explicit None are byte-for-byte identical (no threat alert).
    """
    world, game, calendar = _ongoing_fixture()
    baseline_html = render_game_page(world, game, calendar)

    assert render_game_page(world, game, calendar, player_duchy_id=None) == baseline_html

    root = ET.fromstring(baseline_html)
    assert _find_by_attr(root, "data-threat-alert") == []
    assert "data-threat-alert" not in baseline_html


def test_render_game_page_omits_hero_chase_when_player_duchy_id_none():
    """Default / explicit ``player_duchy_id=None``: no ``data-hero-chase``.

    Default and explicit None are byte-for-byte identical (no hero chase).
    """
    world, game, calendar = _ongoing_fixture()
    baseline_html = render_game_page(world, game, calendar)

    assert render_game_page(world, game, calendar, player_duchy_id=None) == baseline_html

    root = ET.fromstring(baseline_html)
    assert _find_by_attr(root, "data-hero-chase") == []
    assert "data-hero-chase" not in baseline_html


def test_render_game_page_omits_victory_progress_when_player_duchy_id_none():
    """Default / explicit ``player_duchy_id=None``: no ``data-victory-progress``.

    Default and explicit None are byte-for-byte identical (no progress panel).
    """
    world, game, calendar = _ongoing_fixture()
    baseline_html = render_game_page(world, game, calendar)

    assert render_game_page(world, game, calendar, player_duchy_id=None) == baseline_html

    root = ET.fromstring(baseline_html)
    assert _find_by_attr(root, "data-victory-progress") == []
    assert "data-victory-progress" not in baseline_html


def test_render_game_page_omits_next_objective_when_player_duchy_id_none():
    """Default / explicit ``player_duchy_id=None``: no ``data-next-objective``.

    Default and explicit None are byte-for-byte identical (no next-objective hint).
    """
    world, game, calendar = _ongoing_fixture()
    baseline_html = render_game_page(world, game, calendar)

    assert render_game_page(world, game, calendar, player_duchy_id=None) == baseline_html

    root = ET.fromstring(baseline_html)
    assert _find_by_attr(root, "data-next-objective") == []
    assert "data-next-objective" not in baseline_html


def test_render_game_page_omits_enemy_hero_locator_when_player_duchy_id_none():
    """Default / explicit ``player_duchy_id=None``: no ``data-hero-locator``.

    Default and explicit None are byte-for-byte identical (no hero locator).
    """
    world, game, calendar = _ongoing_fixture()
    baseline_html = render_game_page(world, game, calendar)

    assert render_game_page(world, game, calendar, player_duchy_id=None) == baseline_html

    root = ET.fromstring(baseline_html)
    assert _find_by_attr(root, "data-hero-locator") == []
    assert "data-hero-locator" not in baseline_html


def test_render_game_page_omits_player_summary_when_player_duchy_id_none():
    """Default / explicit ``player_duchy_id=None``: no ``data-player-summary``."""
    world, game, calendar = _ongoing_fixture()
    baseline_html = render_game_page(world, game, calendar)

    assert render_game_page(world, game, calendar, player_duchy_id=None) == baseline_html

    root = ET.fromstring(baseline_html)
    assert _find_by_attr(root, "data-player-summary") == []
    assert "data-player-summary" not in baseline_html


def test_render_game_page_player_result_text_from_player_perspective():
    """With ``player_duchy_id``, one ``data-player-result-text`` mirrors player outcome.

    Covers ongoing / own win / other duchy win / draw; attribute equals body text.
    """
    world, game, calendar = _ongoing_fixture()
    assert not game.is_over

    html = render_game_page(world, game, calendar, player_duchy_id="north")
    root = ET.fromstring(html)
    player_results = _find_by_attr(root, "data-player-result-text")
    assert len(player_results) == 1
    el = player_results[0]
    assert _local(el.tag) == "p"
    assert el.get("data-player-result-text") == "Gra w toku"
    assert (el.text or "").strip() == "Gra w toku"

    # Player's duchy is the sole winner.
    won_by_player = GameState(
        (
            Duchy(
                "north",
                Unit(),
                morale=7,
                settlements=(Settlement("North Keep", 3, owner_id="north"),),
            ),
            Duchy("south", None, morale=0, settlements=()),
        )
    )
    assert won_by_player.is_over and won_by_player.winner is not None
    assert won_by_player.winner.duchy_id == "north"
    win_html = render_game_page(
        world, won_by_player, calendar, player_duchy_id="north"
    )
    win_els = _find_by_attr(ET.fromstring(win_html), "data-player-result-text")
    assert len(win_els) == 1
    assert win_els[0].get("data-player-result-text") == "Zwycięstwo Twojego księstwa"
    assert (win_els[0].text or "").strip() == "Zwycięstwo Twojego księstwa"

    # Another duchy won — player lost.
    won_by_other = GameState(
        (
            Duchy("north", None, morale=0, settlements=()),
            Duchy(
                "south",
                Unit(),
                morale=3,
                settlements=(Settlement("South Keep", 4, owner_id="south"),),
            ),
        )
    )
    assert won_by_other.is_over and won_by_other.winner is not None
    assert won_by_other.winner.duchy_id == "south"
    loss_html = render_game_page(
        world, won_by_other, calendar, player_duchy_id="north"
    )
    loss_els = _find_by_attr(ET.fromstring(loss_html), "data-player-result-text")
    assert len(loss_els) == 1
    assert loss_els[0].get("data-player-result-text") == "Porażka Twojego księstwa"
    assert (loss_els[0].text or "").strip() == "Porażka Twojego księstwa"

    # Over without a winner — draw.
    draw = GameState(
        (
            Duchy("north", None, morale=0, settlements=()),
            Duchy("south", None, morale=0, settlements=()),
        )
    )
    assert draw.is_over and draw.winner is None
    draw_html = render_game_page(world, draw, calendar, player_duchy_id="north")
    draw_els = _find_by_attr(ET.fromstring(draw_html), "data-player-result-text")
    assert len(draw_els) == 1
    assert draw_els[0].get("data-player-result-text") == "Remis"
    assert (draw_els[0].text or "").strip() == "Remis"


def test_render_game_page_omits_player_result_text_when_player_duchy_id_none():
    """Default / explicit ``player_duchy_id=None``: no ``data-player-result-text``."""
    world, game, calendar = _ongoing_fixture()
    baseline_html = render_game_page(world, game, calendar)

    assert render_game_page(world, game, calendar, player_duchy_id=None) == baseline_html

    root = ET.fromstring(baseline_html)
    assert _find_by_attr(root, "data-player-result-text") == []
    assert "data-player-result-text" not in baseline_html


def test_render_game_page_has_document_title_in_head_before_body():
    """``<html>`` has exactly one ``<head>`` with one ``<title>Total Battle Brothers</title>`` before ``<body>``."""
    world, game, calendar = _ongoing_fixture()

    html = render_game_page(world, game, calendar)
    root = ET.fromstring(html)

    assert _local(root.tag) == "html"
    direct_children = list(root)
    assert [_local(el.tag) for el in direct_children] == ["head", "body"]

    heads = [el for el in root.iter() if _local(el.tag) == "head"]
    assert len(heads) == 1
    head = heads[0]
    assert head in direct_children

    titles = [el for el in head if _local(el.tag) == "title"]
    assert len(titles) == 1
    assert (titles[0].text or "").strip() == "Total Battle Brothers"

    all_titles = [el for el in root.iter() if _local(el.tag) == "title"]
    assert len(all_titles) == 1

    bodies = [el for el in root if _local(el.tag) == "body"]
    assert len(bodies) == 1


def test_render_game_page_emits_visible_page_title_h1_as_first_body_child():
    """Exactly one ``<h1 data-page-title="">Total Battle Brothers</h1>`` is first in ``<body>``, before map SVG."""
    world, game, calendar = _ongoing_fixture()
    expected_svg = render_world_svg(world)
    expected_h1 = '<h1 data-page-title="">Total Battle Brothers</h1>'

    html = render_game_page(world, game, calendar)
    root = ET.fromstring(html)

    body = next(el for el in root if _local(el.tag) == "body")
    body_children = list(body)
    assert len(body_children) >= 1

    first = body_children[0]
    assert _local(first.tag) == "h1"
    assert first.get("data-page-title") == ""
    assert (first.text or "").strip() == "Total Battle Brothers"

    page_titles = _find_by_attr(root, "data-page-title")
    assert len(page_titles) == 1
    assert page_titles[0] is first

    all_h1 = [el for el in root.iter() if _local(el.tag) == "h1"]
    assert len(all_h1) == 1

    assert html.count(expected_h1) == 1
    assert expected_svg in html
    assert html.index(expected_h1) < html.index(expected_svg), (
        "page title h1 must precede the embedded world map SVG in <body>"
    )


def test_render_game_page_emits_objective_line_after_page_title_before_map():
    """Exactly one ``<p data-objective>`` with fixed win text sits after h1, before map SVG.

    Attribute value equals body text; position is immediately after
    ``data-page-title`` and before the embedded ``render_world_svg`` output.
    """
    world, game, calendar = _ongoing_fixture()
    expected_svg = render_world_svg(world)
    expected_text = (
        "Cel: pokonaj księstwo AI — odbierz mu wszystkie osady "
        "i pokonaj jego bohatera"
    )
    expected_h1 = '<h1 data-page-title="">Total Battle Brothers</h1>'
    expected_p = f'<p data-objective="{expected_text}">{expected_text}</p>'

    html = render_game_page(world, game, calendar)
    root = ET.fromstring(html)

    body = next(el for el in root if _local(el.tag) == "body")
    body_children = list(body)
    assert len(body_children) >= 2

    h1 = body_children[0]
    assert _local(h1.tag) == "h1"
    assert h1.get("data-page-title") == ""

    objective = body_children[1]
    assert _local(objective.tag) == "p"
    assert objective.get("data-objective") == expected_text
    assert (objective.text or "").strip() == expected_text

    objectives = _find_by_attr(root, "data-objective")
    assert len(objectives) == 1
    assert objectives[0] is objective

    assert html.count(expected_p) == 1
    assert expected_svg in html
    assert html.index(expected_h1) + len(expected_h1) == html.index(expected_p), (
        "objective line must sit directly after the page title h1"
    )
    assert html.index(expected_p) < html.index(expected_svg), (
        "objective line must precede the embedded world map SVG in <body>"
    )


def test_render_game_page_embeds_canonical_turn_summary_after_calendar_when_previous_game():
    """``previous_game`` embeds one canonical ``render_turn_summary`` right after calendar.

    Exactly one ``data-turn-summary`` in ``<body>``; string equals
    ``render_turn_summary(previous_game, game)`` and sits immediately after
    the ``data-calendar`` element. Independent of ``player_duchy_id`` (works
    in observer mode).
    """
    world, game, calendar = _ongoing_fixture()
    # Distinct previous snapshot: south still has a hero (current fixture: south
    # has hero; use a stripped previous so summary has a real change flag).
    previous_game = GameState(
        (
            Duchy(
                "north",
                Unit(),
                morale=7,
                settlements=(
                    Settlement("North Keep", 3, owner_id="north"),
                ),
                parties=(),
            ),
            Duchy(
                "south",
                Unit(),
                morale=3,
                settlements=(
                    Settlement("South Keep", 4, owner_id="south"),
                ),
                parties=(),
            ),
        )
    )
    expected_summary = render_turn_summary(previous_game, game)
    calendar_snippet = (
        f'<div data-calendar="" data-year="{calendar.year}"'
        f' data-month="{calendar.month}">'
        f"Rok {calendar.year}, miesiąc {calendar.month}</div>"
    )

    html = render_game_page(
        world, game, calendar, previous_game=previous_game
    )

    assert expected_summary in html, (
        "page must embed render_turn_summary(previous_game, game) output"
    )
    assert html.count(expected_summary) == 1
    assert html.index(calendar_snippet) + len(calendar_snippet) == html.index(
        expected_summary
    ), "turn summary must sit directly after the data-calendar element"

    root = ET.fromstring(html)
    assert _local(root.tag) == "html"
    body = next(el for el in root if _local(el.tag) == "body")
    summary_els = _find_by_attr(root, "data-turn-summary")
    assert len(summary_els) == 1
    assert summary_els[0] in list(body.iter())


def test_render_game_page_omits_turn_summary_when_previous_game_none():
    """Default / explicit ``previous_game=None``: no ``data-turn-summary``.

    Default and explicit None are byte-for-byte identical (no turn summary).
    """
    world, game, calendar = _ongoing_fixture()
    baseline_html = render_game_page(world, game, calendar)

    assert render_game_page(world, game, calendar, previous_game=None) == baseline_html

    root = ET.fromstring(baseline_html)
    assert _find_by_attr(root, "data-turn-summary") == []
    assert "data-turn-summary" not in baseline_html

