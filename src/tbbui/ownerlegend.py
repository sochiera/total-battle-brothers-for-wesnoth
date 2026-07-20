"""Deterministic HTML fragment for owner-color legend on the strategic map."""

from __future__ import annotations

from tbb.world import WorldMap
from tbbui.palette import owner_palette


def render_owner_legend(
    world: WorldMap, player_duchy_id: str | None = None
) -> str:
    """Return a parsable HTML fragment listing owners and their map colors.

    Root is ``<div data-owner-legend="">`` with one ``data-owner-legend-row``
    child per entry of ``owner_palette(world)``, in that order. Each row carries
    ``data-owner`` / ``data-color`` and visible text ``<owner_id>: <color>``.
    When ``player_duchy_id`` is not ``None``, the row whose ``owner_id`` matches
    gets ``data-player-owner=""`` and a visible ``» `` text prefix. Empty
    palette → bare, childless root. Pure and deterministic: no RNG/IO;
    ``world`` is not mutated.
    """
    rows: list[str] = []
    for owner_id, color in owner_palette(world).items():
        is_player = player_duchy_id is not None and owner_id == player_duchy_id
        text = f"{owner_id}: {color}"
        if is_player:
            text = f"» {text}"
        player_attr = ' data-player-owner=""' if is_player else ""
        rows.append(
            f'<div data-owner-legend-row="{owner_id}"'
            f' data-owner="{owner_id}"'
            f' data-color="{color}"'
            f"{player_attr}"
            f">{text}</div>"
        )
    return f'<div data-owner-legend="">{"".join(rows)}</div>'
