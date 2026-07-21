"""Deterministic HTML fragment summarizing the player duchy economy."""

from __future__ import annotations

from tbb.game import GameState


def render_player_summary(
    game: GameState, player_duchy_id: str | None = None
) -> str:
    """Return a parsable HTML fragment with the player duchy economy totals.

    Root is ``<div data-player-summary="">``. When ``player_duchy_id`` matches a
    duchy in ``game.duchies``, the root carries ``data-settlements`` /
    ``data-parties`` (counts), ``data-gold`` / ``data-wheat`` (sums of
    ``settlement.storage`` over that duchy) and visible text
    ``Twoje księstwo: osady N, oddziały M · pszenica W, złoto G``. When
    ``player_duchy_id`` is ``None`` or not present in ``game.duchies``, returns
    a bare empty root. Pure and deterministic: no RNG/IO; ``game`` is not
    mutated.
    """
    if player_duchy_id is None:
        return '<div data-player-summary=""></div>'

    duchy = next(
        (d for d in game.duchies if d.duchy_id == player_duchy_id),
        None,
    )
    if duchy is None:
        return '<div data-player-summary=""></div>'

    n_settlements = len(duchy.settlements)
    n_parties = len(duchy.parties)
    gold = sum(s.storage.gold for s in duchy.settlements)
    wheat = sum(s.storage.wheat for s in duchy.settlements)
    text = (
        f"Twoje księstwo: osady {n_settlements}, oddziały {n_parties}"
        f" · pszenica {wheat}, złoto {gold}"
    )
    return (
        f'<div data-player-summary=""'
        f' data-settlements="{n_settlements}"'
        f' data-parties="{n_parties}"'
        f' data-gold="{gold}"'
        f' data-wheat="{wheat}"'
        f">{text}</div>"
    )
