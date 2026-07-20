"""Deterministic HTML fragment for owner-color legend on the strategic map."""

from __future__ import annotations

from tbb.world import WorldMap
from tbbui.palette import owner_palette


def render_owner_legend(world: WorldMap) -> str:
    """Return a parsable HTML fragment listing owners and their map colors.

    Root is ``<div data-owner-legend="">`` with one ``data-owner-legend-row``
    child per entry of ``owner_palette(world)``, in that order. Each row carries
    ``data-owner`` / ``data-color`` and visible text ``<owner_id>: <color>``.
    Empty palette → bare, childless root. Pure and deterministic: no RNG/IO;
    ``world`` is not mutated.
    """
    rows: list[str] = []
    for owner_id, color in owner_palette(world).items():
        text = f"{owner_id}: {color}"
        rows.append(
            f'<div data-owner-legend-row="{owner_id}"'
            f' data-owner="{owner_id}"'
            f' data-color="{color}"'
            f">{text}</div>"
        )
    return f'<div data-owner-legend="">{"".join(rows)}</div>'
