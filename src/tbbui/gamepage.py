"""Deterministic HTML page for one observer party snapshot (map + panels)."""

from __future__ import annotations

from tbb.battle import HexBattle
from tbb.game import GameState
from tbb.turn import Calendar
from tbb.world import WorldMap
from tbbui.battlereport import render_battle_report
from tbbui.battlesvg import render_battle_svg
from tbbui.engagementpreview import render_engagement_preview
from tbbui.herochase import render_hero_chase
from tbbui.herolocator import render_enemy_hero_locator
from tbbui.nextobjective import render_next_objective
from tbbui.ownerlegend import render_owner_legend
from tbbui.partypanel import render_party_panel
from tbbui.playersummary import render_player_summary
from tbbui.settlementpanel import render_settlement_panel
from tbbui.threatalert import render_threat_alert
from tbbui.turnsummary import render_turn_summary
from tbbui.victoryprogress import render_victory_progress
from tbbui.worldsvg import render_world_svg

_OBJECTIVE_TEXT = (
    "Cel: pokonaj księstwo AI — odbierz mu wszystkie osady "
    "i pokonaj jego bohatera"
)


def _result_value(game: GameState) -> str:
    """Map game-over state to the ``data-result`` attribute value."""
    if not game.is_over:
        return "ongoing"
    if game.winner is not None:
        return game.winner.duchy_id
    return "draw"


def _result_text(game: GameState) -> str:
    """Human-readable result banner mirroring ``_result_value``."""
    if not game.is_over:
        return "Gra w toku"
    if game.winner is not None:
        return f"Zwycięstwo: {game.winner.duchy_id}"
    return "Remis"


def _player_result_text(game: GameState, player_duchy_id: str) -> str:
    """Result line from the player's perspective (win / loss / draw / ongoing)."""
    if not game.is_over:
        return "Gra w toku"
    if game.winner is None:
        return "Remis"
    if game.winner.duchy_id == player_duchy_id:
        return "Zwycięstwo Twojego księstwa"
    return "Porażka Twojego księstwa"


def render_game_page(
    world: WorldMap,
    game: GameState,
    calendar: Calendar,
    battle: HexBattle | None = None,
    player_duchy_id: str | None = None,
    previous_game: GameState | None = None,
) -> str:
    """Return a parsable HTML string for one party snapshot.

    Root ``<html>`` has exactly one ``<head>`` with
    ``<title>Total Battle Brothers</title>`` (K32.1a) immediately before
    ``<body>``. First child of ``<body>`` is a visible page title
    ``<h1 data-page-title="">Total Battle Brothers</h1>`` (K32.1b; constant,
    independent of ``player_duchy_id`` / ``battle``), then a fixed win-condition
    line ``<p data-objective="…">…</p>`` (K32.1c; ``_OBJECTIVE_TEXT``, same
    value in attribute and body text; independent of ``player_duchy_id`` /
    ``game`` / ``battle``), then the strategic map SVG from
    ``render_world_svg``, the owner-color legend from
    ``render_owner_legend(world, player_duchy_id)``, a visible settlements
    section header (``<h2 data-panel-section="settlements">Osady</h2>``,
    K27.3a) immediately before the settlement panel from
    ``render_settlement_panel(world, player_duchy_id)``, a visible parties
    section header (``<h2 data-panel-section="parties">Oddziały</h2>``,
    K27.3b) immediately before the party panel from
    ``render_party_panel(world, player_duchy_id)``, a calendar stamp
    (``data-year`` / ``data-month`` plus visible text ``Rok N, miesiąc M``),
    optional ``previous_game`` embeds the canonical string from
    ``render_turn_summary(previous_game, game)`` immediately after the
    calendar (K38.1c, exactly one ``data-turn-summary``; independent of
    ``player_duchy_id``); ``None`` (default) omits it, a visible duchies
    section header
    (``<h2 data-panel-section="duchies">Księstwa</h2>``, K27.3b)
    immediately before one duchy panel row per ``game.duchies`` (machine
    ``data-*`` attributes including ``data-hero`` from ``duchy.has_hero`` and
    ``data-heir`` from ``duchy.heir is not None``, plus human-readable status
    text with ``, bohater tak|nie, dziedzic tak|nie`` after morale), a
    machine-readable result marker (``data-result``), and a human-readable
    result banner (``data-result-text``). When ``battle`` is a ``HexBattle``,
    also embeds the canonical strings from ``render_battle_svg(battle)`` and
    ``render_battle_report(battle)`` in ``<body>``. Optional
    ``player_duchy_id`` marks the matching ``data-duchy`` row with
    ``data-player-duchy=""`` and a visible ``» `` text prefix, and is
    forwarded to the owner legend, settlement panel, and party panel so
    matching legend / ``data-settlement-row`` / ``data-party-row`` entries
    get player markers; when not ``None``, also embeds the canonical string
    from ``render_player_summary(game, player_duchy_id)`` in ``<body>``
    (exactly one ``data-player-summary``), immediately after it the
    canonical string from ``render_victory_progress(game, player_duchy_id)``
    (K33.1c, exactly one ``data-victory-progress``), immediately after that
    the canonical string from ``render_next_objective(game, player_duchy_id)``
    (K34.1b, exactly one ``data-next-objective``), immediately after that
    the canonical string from
    ``render_enemy_hero_locator(world, game, player_duchy_id)`` (K35.1b,
    exactly one ``data-hero-locator``), immediately after that the canonical
    string from ``render_hero_chase(world, game, player_duchy_id)`` (K36.1c,
    exactly one ``data-hero-chase``), immediately after that the canonical
    string from ``render_engagement_preview(world, game, player_duchy_id)``
    (K37.1c, exactly one ``data-engagement-preview``), immediately after that
    the canonical string from
    ``render_threat_alert(world, game, player_duchy_id)`` (K39.1c, exactly one
    ``data-threat-alert``), and a player-perspective result line
    (``<p data-player-result-text>``, K31.2a); ``None`` (default) omits those
    markers, the summary, the victory progress, the next-objective hint, the
    hero locator, the hero chase, the engagement preview, the threat alert, and
    the player result. Pure and deterministic: no RNG/IO; inputs (including
    ``battle``) are not mutated.
    """
    map_svg = render_world_svg(world)
    owner_legend = render_owner_legend(world, player_duchy_id)
    settlement_panel = render_settlement_panel(world, player_duchy_id)
    party_panel = render_party_panel(world, player_duchy_id)
    if player_duchy_id is not None:
        player_summary = render_player_summary(game, player_duchy_id)
        victory_progress = render_victory_progress(game, player_duchy_id)
        next_objective = render_next_objective(game, player_duchy_id)
        hero_locator = render_enemy_hero_locator(world, game, player_duchy_id)
        hero_chase = render_hero_chase(world, game, player_duchy_id)
        engagement_preview = render_engagement_preview(
            world, game, player_duchy_id
        )
        threat_alert = render_threat_alert(world, game, player_duchy_id)
        player_result_text = _player_result_text(game, player_duchy_id)
        player_result_html = (
            f'<p data-player-result-text="{player_result_text}">'
            f"{player_result_text}</p>"
        )
    else:
        player_summary = ""
        victory_progress = ""
        next_objective = ""
        hero_locator = ""
        hero_chase = ""
        engagement_preview = ""
        threat_alert = ""
        player_result_html = ""
    if previous_game is not None:
        turn_summary = render_turn_summary(previous_game, game)
    else:
        turn_summary = ""
    result = _result_value(game)
    result_text = _result_text(game)

    duchy_parts: list[str] = []
    for duchy in game.duchies:
        is_player = player_duchy_id is not None and duchy.duchy_id == player_duchy_id
        hero_label = "tak" if duchy.has_hero else "nie"
        heir_label = "tak" if duchy.heir is not None else "nie"
        status_text = (
            f"{duchy.duchy_id}: osady {len(duchy.settlements)}, "
            f"party {len(duchy.parties)}, morale {duchy.morale}, "
            f"bohater {hero_label}, dziedzic {heir_label}"
        )
        if is_player:
            status_text = f"» {status_text}"
        player_attr = ' data-player-duchy=""' if is_player else ""
        hero_attr = "true" if duchy.has_hero else "false"
        heir_attr = "true" if duchy.heir is not None else "false"
        duchy_parts.append(
            "<div"
            f' data-duchy="{duchy.duchy_id}"'
            f' data-morale="{duchy.morale}"'
            f' data-settlements="{len(duchy.settlements)}"'
            f' data-parties="{len(duchy.parties)}"'
            f' data-hero="{hero_attr}"'
            f' data-heir="{heir_attr}"'
            f"{player_attr}"
            f">{status_text}</div>"
        )

    if battle is not None:
        battle_svg = render_battle_svg(battle)
        battle_report = render_battle_report(battle)
    else:
        battle_svg = ""
        battle_report = ""

    settlements_header = '<h2 data-panel-section="settlements">Osady</h2>'
    parties_header = '<h2 data-panel-section="parties">Oddziały</h2>'
    duchies_header = '<h2 data-panel-section="duchies">Księstwa</h2>'

    page_title = '<h1 data-page-title="">Total Battle Brothers</h1>'
    objective = (
        f'<p data-objective="{_OBJECTIVE_TEXT}">{_OBJECTIVE_TEXT}</p>'
    )

    return (
        "<html>"
        "<head><title>Total Battle Brothers</title></head>"
        "<body>"
        f"{page_title}"
        f"{objective}"
        f"{map_svg}"
        f"{owner_legend}"
        f"{player_summary}"
        f"{victory_progress}"
        f"{next_objective}"
        f"{hero_locator}"
        f"{hero_chase}"
        f"{engagement_preview}"
        f"{threat_alert}"
        f"{battle_svg}"
        f"{battle_report}"
        f"{settlements_header}"
        f"{settlement_panel}"
        f"{parties_header}"
        f"{party_panel}"
        f'<div data-calendar="" data-year="{calendar.year}"'
        f' data-month="{calendar.month}">'
        f"Rok {calendar.year}, miesiąc {calendar.month}</div>"
        f"{turn_summary}"
        f"{duchies_header}"
        f"{''.join(duchy_parts)}"
        f'<div data-result="{result}"></div>'
        f'<p data-result-text="{result_text}">{result_text}</p>'
        f"{player_result_html}"
        "</body></html>"
    )
