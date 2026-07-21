"""Deterministic HTML fragment for the next-objective hint."""

from __future__ import annotations

import html

from tbb.game import GameState
from tbbui.gamelookup import player_duchy


def render_next_objective(
    game: GameState, player_duchy_id: str | None = None
) -> str:
    """Return a one-sentence next-step hint for the player.

    Root is always ``<p data-next-objective="TEXT">TEXT</p>`` where attribute
    and body are the same characters (empty when no valid player). Pure and
    deterministic: no RNG/IO; ``game`` is not mutated.
    """
    if player_duchy(game, player_duchy_id) is None:
        return '<p data-next-objective=""></p>'

    undefeated = tuple(
        d
        for d in game.duchies
        if d.duchy_id != player_duchy_id and not d.is_defeated
    )
    if not undefeated:
        text = "Cel osiągnięty: wszyscy wrogowie pokonani"
    else:
        settlements_left = sum(len(d.settlements) for d in undefeated)
        if settlements_left > 0:
            text = f"Odbierz wrogie osady (pozostało: {settlements_left})"
        else:
            heroes_left = sum(1 for d in undefeated if d.has_hero)
            text = f"Dobij wrogich bohaterów (pozostało: {heroes_left})"

    escaped = html.escape(text, quote=True)
    return f'<p data-next-objective="{escaped}">{escaped}</p>'
