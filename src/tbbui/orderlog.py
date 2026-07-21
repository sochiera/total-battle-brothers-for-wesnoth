"""Deterministic HTML fragment for the player order log (tbbui)."""

from __future__ import annotations

import html
from collections.abc import Sequence

from tbb.turn import Calendar


def format_log_entry(notice: str, calendar: Calendar) -> str:
    """Return a single order-log line with calendar date prefix.

    Exactly ``f"Rok {calendar.year}, miesiąc {calendar.month} — {notice}"``.
    Pure and deterministic: does not escape (``render_order_log`` does),
    does not mutate ``calendar`` or ``notice``; empty ``notice`` is allowed.
    """
    return f"Rok {calendar.year}, miesiąc {calendar.month} — {notice}"


def render_order_log(entries: Sequence[str]) -> str:
    """Return a parsable HTML fragment listing order-log text entries.

    Root is ``<div data-order-log="" data-count="N">`` where ``N`` is
    ``len(entries)`` (header is not counted). First child is always
    ``<h2 data-order-log-header="">Dziennik rozkazów</h2>`` (also for empty
    sequence). Each entry then becomes one
    ``<div data-order-log-entry="">`` with body ``html.escape(entry, quote=True)``
    (input order preserved). Pure and deterministic: no RNG/IO; does not mutate
    ``entries``.
    """
    count = len(entries)
    header = '<h2 data-order-log-header="">Dziennik rozkazów</h2>'
    entry_children = "".join(
        f'<div data-order-log-entry="">{html.escape(entry, quote=True)}</div>'
        for entry in entries
    )
    return (
        f'<div data-order-log="" data-count="{count}">{header}{entry_children}</div>'
    )
