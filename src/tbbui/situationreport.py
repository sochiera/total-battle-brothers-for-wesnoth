"""Deterministic HTML fragment for a one-line tactical situation report."""

from __future__ import annotations

from tbb.game import GameState
from tbb.world import WorldMap
from tbbui.gamelookup import player_duchy
from tbbui.threatalert import threatened_position_count


def render_situation_report(
    world: WorldMap,
    game: GameState,
    player_duchy_id: str | None = None,
) -> str:
    """Return a one-line situation-report root for threatened own positions.

    Root is ``<div data-situation-report="">``. When ``player_duchy_id`` is
    ``None`` or not in ``game.duchies`` (``player_duchy(...) is None``), returns
    a bare empty root with no ``data-threatened-count``, no visible text, and no
    children. When the player is known, the root carries
    ``data-threatened-count="N"`` (via ``threatalert.threatened_position_count``,
    same rule as ``render_threat_alert``) and visible text
    ``Sytuacja: zagrożone pozycje N``. Pure and deterministic: no RNG/IO; does
    not mutate ``world`` or ``game``.
    """
    if player_duchy(game, player_duchy_id) is None:
        return '<div data-situation-report=""></div>'

    # player_duchy is not None ⇒ player_duchy_id is a known str
    assert player_duchy_id is not None
    n = threatened_position_count(world, game, player_duchy_id)
    return (
        f'<div data-situation-report="" data-threatened-count="{n}">'
        f"Sytuacja: zagrożone pozycje {n}</div>"
    )
