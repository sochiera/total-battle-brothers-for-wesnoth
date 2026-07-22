"""Deterministic HTML fragment for duchy economy alert (starving settlements)."""

from __future__ import annotations

import html

from tbb.game import GameState
from tbbui.gamelookup import player_duchy


def render_economy_alert(
    game: GameState, player_duchy_id: str | None = None
) -> str:
    """Return a parsable HTML fragment with starving-settlement count and rows.

    Root is ``<div data-economy-alert="">``. When ``player_duchy_id`` matches a
    duchy in ``game.duchies``, the root carries ``data-starving-settlements="N"``
    where ``N`` is the number of settlements in that duchy with
    ``consumption.wheat > production.wheat`` (strict greater-than; equal
    balance does not count), visible text ``Osady na deficycie pszenicy: N``
    matching that count, and one child
    ``<div data-starving-settlement="<name>" data-wheat-deficit="D"></div>``
    per starving settlement in ``duchy.settlements`` order, where
    ``name`` is ``html.escape(settlement.name, quote=True)`` and
    ``D = consumption.wheat - production.wheat`` (positive; no visible child
    text). Settlements without a wheat deficit produce no row. When
    ``player_duchy_id`` is ``None`` or not present in ``game.duchies``, returns
    a bare empty root (no ``data-starving-settlements``, no text, no children).
    Pure and deterministic: no RNG/IO; ``game`` is not mutated.
    """
    duchy = player_duchy(game, player_duchy_id)
    if duchy is None:
        return '<div data-economy-alert=""></div>'

    rows: list[str] = []
    for s in duchy.settlements:
        deficit = s.consumption.wheat - s.production.wheat
        if deficit > 0:
            name = html.escape(s.name, quote=True)
            rows.append(
                f'<div data-starving-settlement="{name}"'
                f' data-wheat-deficit="{deficit}"></div>'
            )
    n = len(rows)
    text = f"Osady na deficycie pszenicy: {n}"
    return (
        f'<div data-economy-alert=""'
        f' data-starving-settlements="{n}"'
        f">{text}{''.join(rows)}</div>"
    )
