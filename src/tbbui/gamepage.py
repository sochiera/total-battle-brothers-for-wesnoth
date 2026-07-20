"""Deterministic HTML page for one observer party snapshot (map + panels)."""

from __future__ import annotations

from tbb.battle import HexBattle
from tbb.game import GameState
from tbb.turn import Calendar
from tbb.world import WorldMap
from tbbui.battlereport import render_battle_report
from tbbui.battlesvg import render_battle_svg
from tbbui.ownerlegend import render_owner_legend
from tbbui.partypanel import render_party_panel
from tbbui.settlementpanel import render_settlement_panel
from tbbui.worldsvg import render_world_svg


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


def render_game_page(
    world: WorldMap,
    game: GameState,
    calendar: Calendar,
    battle: HexBattle | None = None,
    player_duchy_id: str | None = None,
) -> str:
    """Return a parsable HTML string for one party snapshot.

    Embeds the strategic map SVG from ``render_world_svg``, the owner-color
    legend from ``render_owner_legend(world)``, the settlement panel from
    ``render_settlement_panel(world, player_duchy_id)``, the party panel from
    ``render_party_panel(world)``, a calendar stamp (``data-year`` /
    ``data-month`` plus visible text ``Rok N, miesiąc M``), one duchy panel
    row per ``game.duchies`` (machine ``data-*`` attributes plus
    human-readable status text), a machine-readable result marker
    (``data-result``), and a human-readable result banner
    (``data-result-text``). When ``battle`` is a ``HexBattle``, also embeds the
    canonical strings from ``render_battle_svg(battle)`` and
    ``render_battle_report(battle)`` in ``<body>``. Optional
    ``player_duchy_id`` marks the matching ``data-duchy`` row with
    ``data-player-duchy=""`` and a visible ``» `` text prefix, and is
    forwarded to the settlement panel so matching ``data-settlement-row``
    entries get ``data-player-owned=""``; ``None`` (default) leaves the page
    byte-for-byte unchanged. Pure and deterministic: no RNG/IO; inputs
    (including ``battle``) are not mutated.
    """
    map_svg = render_world_svg(world)
    owner_legend = render_owner_legend(world)
    settlement_panel = render_settlement_panel(world, player_duchy_id)
    party_panel = render_party_panel(world)
    result = _result_value(game)
    result_text = _result_text(game)

    duchy_parts: list[str] = []
    for duchy in game.duchies:
        is_player = player_duchy_id is not None and duchy.duchy_id == player_duchy_id
        status_text = (
            f"{duchy.duchy_id}: osady {len(duchy.settlements)}, "
            f"party {len(duchy.parties)}, morale {duchy.morale}"
        )
        if is_player:
            status_text = f"» {status_text}"
        player_attr = ' data-player-duchy=""' if is_player else ""
        duchy_parts.append(
            "<div"
            f' data-duchy="{duchy.duchy_id}"'
            f' data-morale="{duchy.morale}"'
            f' data-settlements="{len(duchy.settlements)}"'
            f' data-parties="{len(duchy.parties)}"'
            f"{player_attr}"
            f">{status_text}</div>"
        )

    if battle is not None:
        battle_svg = render_battle_svg(battle)
        battle_report = render_battle_report(battle)
    else:
        battle_svg = ""
        battle_report = ""

    return (
        "<html><body>"
        f"{map_svg}"
        f"{owner_legend}"
        f"{battle_svg}"
        f"{battle_report}"
        f"{settlement_panel}"
        f"{party_panel}"
        f'<div data-calendar="" data-year="{calendar.year}"'
        f' data-month="{calendar.month}">'
        f"Rok {calendar.year}, miesiąc {calendar.month}</div>"
        f"{''.join(duchy_parts)}"
        f'<div data-result="{result}"></div>'
        f'<p data-result-text="{result_text}">{result_text}</p>'
        "</body></html>"
    )
