"""Deterministic HTML fragment for duchy economy alert (starving settlements)."""

from __future__ import annotations

from tbb.game import GameState
from tbbui.gamelookup import player_duchy


def render_economy_alert(
    game: GameState, player_duchy_id: str | None = None
) -> str:
    """Return a parsable HTML fragment with starving-settlement count.

    Root is ``<div data-economy-alert="">``. When ``player_duchy_id`` matches a
    duchy in ``game.duchies``, the root carries ``data-starving-settlements="N"``
    where ``N`` is the number of settlements in that duchy with
    ``consumption.wheat > production.wheat`` (strict greater-than; equal
    balance does not count). When ``player_duchy_id`` is ``None`` or not
    present in ``game.duchies``, returns a bare empty root (no
    ``data-starving-settlements``). Pure and deterministic: no RNG/IO;
    ``game`` is not mutated.
    """
    duchy = player_duchy(game, player_duchy_id)
    if duchy is None:
        return '<div data-economy-alert=""></div>'

    n = sum(
        1
        for s in duchy.settlements
        if s.consumption.wheat > s.production.wheat
    )
    return (
        f'<div data-economy-alert=""'
        f' data-starving-settlements="{n}"></div>'
    )
