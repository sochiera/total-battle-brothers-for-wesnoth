"""Deterministic HTML fragment for a one-line recommended action."""

from __future__ import annotations

from tbb.game import GameState
from tbb.world import WorldMap
from tbbui.engagementpreview import advantageous_target_count
from tbbui.gamelookup import player_duchy
from tbbui.situationreport import net_posture
from tbbui.threatalert import threatened_position_count

_POSTURE_ORDERS = {
    "offensive": "Zalecany rozkaz: atakuj",
    "defensive": "Zalecany rozkaz: broń się",
    "balanced": "Zalecany rozkaz: rozwijaj księstwo",
}


def render_recommended_action(
    world: WorldMap,
    game: GameState,
    player_duchy_id: str | None = None,
) -> str:
    """Return a one-line recommended-action root for the player's posture.

    Root is ``<div data-recommended-action="">``. When ``player_duchy_id`` is
    ``None`` or not in ``game.duchies`` (``player_duchy(...) is None``), returns
    a bare empty root with no ``data-posture``, no visible text, and no children.
    When the player is known, the root carries ``data-posture`` from
    ``situationreport.net_posture(M, N)`` (M =
    ``engagementpreview.advantageous_target_count``, N =
    ``threatalert.threatened_position_count``) and visible text
    ``Zalecany rozkaz: atakuj|broń się|rozwijaj księstwo`` for
    ``offensive|defensive|balanced``. Pure and deterministic: no RNG/IO;
    does not mutate ``world`` or ``game``.
    """
    if player_duchy(game, player_duchy_id) is None:
        return '<div data-recommended-action=""></div>'

    assert player_duchy_id is not None
    m = advantageous_target_count(world, game, player_duchy_id)
    n = threatened_position_count(world, game, player_duchy_id)
    posture = net_posture(m, n)
    text = _POSTURE_ORDERS[posture]
    return (
        f'<div data-recommended-action="" data-posture="{posture}">'
        f"{text}</div>"
    )
