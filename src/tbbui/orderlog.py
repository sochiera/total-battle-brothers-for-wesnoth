"""Deterministic HTML fragment for the player order log (tbbui)."""

from __future__ import annotations

import html
from collections.abc import Sequence


def render_order_log(entries: Sequence[str]) -> str:
    """Return a parsable HTML fragment listing order-log text entries.

    Root is ``<div data-order-log="" data-count="N">`` where ``N`` is
    ``len(entries)``. Each entry becomes one child
    ``<div data-order-log-entry="">`` with body ``html.escape(entry, quote=True)``
    (input order preserved). Empty sequence → bare root with ``data-count="0"``
    and no children. Pure and deterministic: no RNG/IO; does not mutate
    ``entries``.
    """
    count = len(entries)
    children = "".join(
        f'<div data-order-log-entry="">{html.escape(entry, quote=True)}</div>'
        for entry in entries
    )
    return f'<div data-order-log="" data-count="{count}">{children}</div>'
