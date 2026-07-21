"""Deterministic HTML fragment for threatened-position alert."""

from __future__ import annotations

from tbb.game import GameState
from tbb.world import WorldMap
from tbbui.gamelookup import player_duchy


def render_threat_alert(
    world: WorldMap,
    game: GameState,
    player_duchy_id: str | None = None,
) -> str:
    """Return an alert root for own positions threatened by adjacent enemy parties.

    Root is ``<div data-threat-alert="">``. When ``player_duchy_id`` is ``None``
    or not in ``game.duchies`` (``player_duchy(...) is None``), returns a bare
    empty root with no ``data-threats``, no visible text, and no children.
    Pure and deterministic: no RNG/IO; does not mutate ``world`` or ``game``.
    """
    if player_duchy(game, player_duchy_id) is None:
        return '<div data-threat-alert=""></div>'
    # data-threats / visible count for a known player — later K39.1a increment
    return '<div data-threat-alert=""></div>'
