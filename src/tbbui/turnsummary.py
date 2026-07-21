"""Deterministic HTML fragment summarizing changes after a turn (tbbui)."""

from __future__ import annotations

from tbb.game import GameState


def render_turn_summary(before: GameState | None, after: GameState) -> str:
    """Return a parsable HTML fragment flagging whether the turn changed state.

    Root is ``<div data-turn-summary="">``. When ``before is None``, returns a
    bare empty root (no ``data-changed``, no ``data-change-count``, no text).
    When ``before`` is a ``GameState``, the root carries ``data-changed`` and
    ``data-change-count`` for duchies matched by ``duchy_id`` that differ in
    ``len(settlements)`` or ``has_hero``, plus one ``data-turn-duchy`` child per
    such duchy (order of ``after.duchies``) and visible text
    ``Zmiany w tej turze: tak|nie``. Pure and deterministic: no RNG/IO; does
    not mutate ``before`` or ``after``.
    """
    if before is None:
        return '<div data-turn-summary=""></div>'

    before_by_id = {d.duchy_id: d for d in before.duchies}
    rows: list[str] = []
    for d_after in after.duchies:
        d_before = before_by_id.get(d_after.duchy_id)
        if d_before is None:
            continue
        sett_before = len(d_before.settlements)
        sett_after = len(d_after.settlements)
        hero_before = d_before.has_hero
        hero_after = d_after.has_hero
        if sett_before == sett_after and hero_before == hero_after:
            continue
        duchy_id = d_after.duchy_id
        hero_before_attr = "true" if hero_before else "false"
        hero_after_attr = "true" if hero_after else "false"
        hero_before_text = "tak" if hero_before else "nie"
        hero_after_text = "tak" if hero_after else "nie"
        rows.append(
            f'<div data-turn-duchy="{duchy_id}"'
            f' data-settlements-before="{sett_before}"'
            f' data-settlements-after="{sett_after}"'
            f' data-hero-before="{hero_before_attr}"'
            f' data-hero-after="{hero_after_attr}">'
            f"{duchy_id}: osady {sett_before}→{sett_after}, "
            f"bohater {hero_before_text}→{hero_after_text}</div>"
        )

    count = len(rows)
    changed = count > 0
    flag = "true" if changed else "false"
    text = "Zmiany w tej turze: tak" if changed else "Zmiany w tej turze: nie"
    return (
        f'<div data-turn-summary="" data-changed="{flag}"'
        f' data-change-count="{count}">{text}{"".join(rows)}</div>'
    )
