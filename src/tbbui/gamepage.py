"""Deterministic HTML page for one observer party snapshot (map + panels)."""

from __future__ import annotations

from tbb.game import GameState
from tbb.turn import Calendar
from tbb.world import WorldMap
from tbbui.worldsvg import render_world_svg


def _result_value(game: GameState) -> str:
    """Map game-over state to the ``data-result`` attribute value."""
    if not game.is_over:
        return "ongoing"
    if game.winner is not None:
        return game.winner.duchy_id
    return "draw"


def render_game_page(world: WorldMap, game: GameState, calendar: Calendar) -> str:
    """Return a parsable HTML string for one party snapshot.

    Embeds the strategic map SVG from ``render_world_svg``, a calendar stamp,
    one duchy panel row per ``game.duchies``, and a result marker. Pure and
    deterministic: no RNG/IO; inputs are not mutated.
    """
    map_svg = render_world_svg(world)
    result = _result_value(game)

    duchy_parts: list[str] = []
    for duchy in game.duchies:
        duchy_parts.append(
            "<div"
            f' data-duchy="{duchy.duchy_id}"'
            f' data-morale="{duchy.morale}"'
            f' data-settlements="{len(duchy.settlements)}"'
            f' data-parties="{len(duchy.parties)}"'
            "></div>"
        )

    return (
        "<html><body>"
        f"{map_svg}"
        f'<div data-calendar="" data-year="{calendar.year}"'
        f' data-month="{calendar.month}"></div>'
        f"{''.join(duchy_parts)}"
        f'<div data-result="{result}"></div>'
        "</body></html>"
    )
