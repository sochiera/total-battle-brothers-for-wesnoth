"""Pure game-state lookup helpers for player duchy resolution."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tbb.duchy import Duchy
    from tbb.game import GameState


def player_duchy(game: GameState, player_duchy_id: str | None) -> Duchy | None:
    """Return the first duchy in ``game.duchies`` with *player_duchy_id*.

    Returns ``None`` when *player_duchy_id* is ``None`` or no duchy matches.
    Pure: does not mutate *game*.
    """
    if player_duchy_id is None:
        return None
    return next(
        (d for d in game.duchies if d.duchy_id == player_duchy_id),
        None,
    )
