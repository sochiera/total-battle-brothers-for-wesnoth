"""Deterministic HTML fragment summarizing changes after a turn (tbbui)."""

from __future__ import annotations

from tbb.game import GameState


def render_turn_summary(before: GameState | None, after: GameState) -> str:
    """Return a parsable HTML fragment flagging whether the turn changed state.

    Root is ``<div data-turn-summary="">``. When ``before is None``, returns a
    bare empty root (no ``data-changed``, no text). When ``before`` is a
    ``GameState``, the root carries ``data-changed="true|false"`` (true when any
    duchy matched by ``duchy_id`` differs in ``len(settlements)`` or
    ``has_hero``) and visible text ``Zmiany w tej turze: tak|nie``. Pure and
    deterministic: no RNG/IO; does not mutate ``before`` or ``after``.
    """
    if before is None:
        return '<div data-turn-summary=""></div>'

    before_by_id = {d.duchy_id: d for d in before.duchies}
    changed = False
    for d_after in after.duchies:
        d_before = before_by_id.get(d_after.duchy_id)
        if d_before is None:
            continue
        if len(d_before.settlements) != len(d_after.settlements):
            changed = True
            break
        if d_before.has_hero != d_after.has_hero:
            changed = True
            break

    flag = "true" if changed else "false"
    text = "Zmiany w tej turze: tak" if changed else "Zmiany w tej turze: nie"
    return (
        f'<div data-turn-summary="" data-changed="{flag}">{text}</div>'
    )
