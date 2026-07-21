"""Deterministic HTML fragment for victory progress (enemies remaining)."""

from __future__ import annotations

from tbb.game import GameState


def render_victory_progress(
    game: GameState, player_duchy_id: str | None = None
) -> str:
    """Return a parsable HTML fragment with enemies remaining for the player.

    Root is ``<div data-victory-progress="">``. When ``player_duchy_id`` matches
    a duchy in ``game.duchies``, the root carries ``data-enemies-remaining="N"``
    (``N`` = number of other duchies with ``not is_defeated``) and visible text
    ``Wrogów do pokonania: N``, plus one child ``<div data-enemy-duchy>`` per
    other duchy in ``game.duchies`` order (settlements/hero/defeated state).
    When ``player_duchy_id`` is ``None`` or not present in ``game.duchies``,
    returns a bare empty root. Pure and deterministic: no RNG/IO; ``game`` is
    not mutated.
    """
    if player_duchy_id is None:
        return '<div data-victory-progress=""></div>'

    player = next(
        (d for d in game.duchies if d.duchy_id == player_duchy_id),
        None,
    )
    if player is None:
        return '<div data-victory-progress=""></div>'

    n = sum(
        1
        for d in game.duchies
        if d.duchy_id != player_duchy_id and not d.is_defeated
    )
    text = f"Wrogów do pokonania: {n}"
    rows: list[str] = []
    for d in game.duchies:
        if d.duchy_id == player_duchy_id:
            continue
        settlements = len(d.settlements)
        hero = "true" if d.has_hero else "false"
        hero_pl = "tak" if d.has_hero else "nie"
        defeated = "true" if d.is_defeated else "false"
        row_text = f"{d.duchy_id}: osady {settlements}, bohater {hero_pl}"
        if d.is_defeated:
            row_text += " — pokonany"
        rows.append(
            f'<div data-enemy-duchy="{d.duchy_id}"'
            f' data-settlements="{settlements}"'
            f' data-hero="{hero}"'
            f' data-defeated="{defeated}"'
            f">{row_text}</div>"
        )
    return (
        f'<div data-victory-progress=""'
        f' data-enemies-remaining="{n}"'
        f">{text}{''.join(rows)}</div>"
    )
