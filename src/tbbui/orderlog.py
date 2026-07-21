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


def render_order_log(entries: Sequence[str], at_limit: bool = False) -> str:
    """Return a parsable HTML fragment listing order-log text entries.

    Root is ``<div data-order-log="" data-count="N">`` where ``N`` is
    ``len(entries)`` (header is not counted). First child is always
    ``<h2 data-order-log-header="">Dziennik rozkazów ({N})</h2>`` (also for
    empty sequence with ``N=0``). When ``entries`` is empty, the header is
    followed by exactly one
    ``<p data-order-log-empty="">Brak rozkazów w tej kampanii</p>`` and no
    entry children; when non-empty that empty-state node is omitted and each
    entry becomes one ``<div data-order-log-entry="">`` with body
    ``html.escape(entry, quote=True)`` in reverse input order (newest first:
    first entry child = ``entries[-1]``, last = ``entries[0]``). The newest
    (first) entry also carries ``data-order-log-latest=""`` and a leading
    literal badge ``<span data-order-log-latest-badge="">najnowszy</span>``
    before the escaped body; older entries have neither. When
    ``at_limit=True`` and ``entries`` is non-empty, after the last entry
    child and before the root close, exactly one
    ``<p data-order-log-truncated="">Pokazano ostatnie wpisy</p>`` is
    appended; when ``at_limit=False`` or ``entries`` is empty that node is
    omitted (default ``at_limit=False`` preserves prior output). Pure and
    deterministic: no RNG/IO; does not mutate ``entries``.
    """
    count = len(entries)
    header = f'<h2 data-order-log-header="">Dziennik rozkazów ({count})</h2>'
    if count == 0:
        body = (
            f'{header}'
            f'<p data-order-log-empty="">Brak rozkazów w tej kampanii</p>'
        )
    else:
        parts: list[str] = []
        for index, entry in enumerate(reversed(entries)):
            escaped = html.escape(entry, quote=True)
            if index == 0:
                parts.append(
                    f'<div data-order-log-entry="" data-order-log-latest="">'
                    f'<span data-order-log-latest-badge="">najnowszy</span>'
                    f"{escaped}</div>"
                )
            else:
                parts.append(
                    f'<div data-order-log-entry="">{escaped}</div>'
                )
        body = f"{header}{''.join(parts)}"
        if at_limit:
            body = (
                f'{body}'
                f'<p data-order-log-truncated="">Pokazano ostatnie wpisy</p>'
            )
    return f'<div data-order-log="" data-count="{count}">{body}</div>'
