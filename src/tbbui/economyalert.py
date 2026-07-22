"""Deterministic HTML fragment for duchy economy alert (starving settlements)."""

from __future__ import annotations

import html

from tbb.game import GameState
from tbbui.gamelookup import player_duchy


_CAUTION_TEXT = "Reaguj: część osad głoduje i nie rośnie"


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
    those starving settlements (``0`` when none), and when ``N>0`` also empty
    ``data-economy-critical=""`` immediately after the total-deficit attribute.
    Visible header text matches that count (``Osady na deficycie pszenicy: N``
    when ``N==0``; when ``N>0`` the same plus suffix
    `` (łączny deficyt: D pszenicy/mies.)`` consistent with
    ``data-total-wheat-deficit``). When ``N>0``, after the header and before
    settlement rows the root embeds
    ``<p data-economy-caution="…">Reaguj: część osad głoduje i nie rośnie</p>``
    (attribute via ``html.escape(..., quote=True)``). Then one child
    ``<div data-starving-settlement="<name>" data-wheat-deficit="D">…</div>``
    per starving settlement in ``duchy.settlements`` order, where
    ``name`` is ``html.escape(settlement.name, quote=True)``,
    per-settlement ``D = consumption.wheat - production.wheat`` (positive), and
    the child body is ``<name>: deficyt D pszenicy/mies.`` (escaped name,
    consistent with attributes). Settlements without a wheat deficit produce no
    row. When ``N==0`` there is no ``data-economy-critical`` and no caution
    child. When ``player_duchy_id`` is ``None`` or not present in
    ``game.duchies``, returns a bare empty root (no
    ``data-starving-settlements``, no ``data-total-wheat-deficit``, no text, no
    children). Pure and deterministic: no RNG/IO; ``game`` is not mutated.
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
    critical_attr = ""
    caution = ""
    if n > 0:
        text += f" (łączny deficyt: {total_deficit} pszenicy/mies.)"
        critical_attr = ' data-economy-critical=""'
        caution_escaped = html.escape(_CAUTION_TEXT, quote=True)
        caution = (
            f'<p data-economy-caution="{caution_escaped}">'
            f"{_CAUTION_TEXT}</p>"
        )
    return (
        f'<div data-economy-alert=""'
        f' data-starving-settlements="{n}"'
        f' data-total-wheat-deficit="{total_deficit}"'
        f"{critical_attr}"
        f">{text}{caution}{''.join(rows)}</div>"
    )
