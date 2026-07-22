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
    balance does not count), ``data-total-wheat-deficit="D"`` immediately after
    it where ``D`` is the sum of ``(consumption.wheat - production.wheat)`` over
    those starving settlements (``0`` when none), visible text
    ``Osady na deficycie pszenicy: N`` matching that count, and one child
    ``<div data-starving-settlement="<name>" data-wheat-deficit="D">…</div>``
    per starving settlement in ``duchy.settlements`` order, where
    ``name`` is ``html.escape(settlement.name, quote=True)``,
    per-settlement ``D = consumption.wheat - production.wheat`` (positive), and
    the child body is ``<name>: deficyt D pszenicy/mies.`` (escaped name,
    consistent with attributes). Settlements without a wheat deficit produce no
    row. When ``player_duchy_id`` is ``None`` or not present in ``game.duchies``,
    returns a bare empty root (no ``data-starving-settlements``, no
    ``data-total-wheat-deficit``, no text, no children). Pure and deterministic:
    no RNG/IO; ``game`` is not mutated.
    """
    duchy = player_duchy(game, player_duchy_id)
    if duchy is None:
        return '<div data-economy-alert=""></div>'

    rows: list[str] = []
    total_deficit = 0
    for s in duchy.settlements:
        deficit = s.consumption.wheat - s.production.wheat
        if deficit > 0:
            total_deficit += deficit
            name = html.escape(s.name, quote=True)
            body = f"{name}: deficyt {deficit} pszenicy/mies."
            rows.append(
                f'<div data-starving-settlement="{name}"'
                f' data-wheat-deficit="{deficit}">{body}</div>'
            )
    n = len(rows)
    text = f"Osady na deficycie pszenicy: {n}"
    return (
        f'<div data-economy-alert=""'
        f' data-starving-settlements="{n}"'
        f' data-total-wheat-deficit="{total_deficit}"'
        f">{text}{''.join(rows)}</div>"
    )
