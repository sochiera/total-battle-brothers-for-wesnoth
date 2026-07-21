"""Deterministic HTML fragment for a one-line recommended action."""

from __future__ import annotations

from tbb.game import GameState
from tbb.world import WorldMap
from tbbui.engagementpreview import (
    advantageous_target_count,
    first_advantageous_target,
)
from tbbui.gamelookup import player_duchy
from tbbui.situationreport import net_posture
from tbbui.threatalert import first_threatened_region, threatened_position_count

_BALANCED_ORDER = "Zalecany rozkaz: rozwijaj księstwo"


def recommended_order(
    world: WorldMap,
    game: GameState,
    player_duchy_id: str | None = None,
) -> tuple[str, str | None] | None:
    """Return machine decision ``(action, target_region_name)`` for the player.

    ``action`` ∈ ``{"assault", "engage", "defend", "develop"}``; ``target`` is
    the region name, or ``None`` for ``develop``. Returns ``None`` when
    ``player_duchy(game, player_duchy_id) is None`` (no player or id not in
    ``game.duchies``). Same posture/target rules as
    ``render_recommended_action``. Pure and deterministic: no RNG/IO; does not
    mutate ``world`` or ``game``.
    """
    if player_duchy(game, player_duchy_id) is None:
        return None

    assert player_duchy_id is not None
    m = advantageous_target_count(world, game, player_duchy_id)
    n = threatened_position_count(world, game, player_duchy_id)
    posture = net_posture(m, n)
    if posture == "offensive":
        target = first_advantageous_target(world, game, player_duchy_id)
        assert target is not None
        region, kind = target
        if kind == "settlement":
            return "assault", region
        return "engage", region
    if posture == "defensive":
        region = first_threatened_region(world, game, player_duchy_id)
        assert region is not None
        return "defend", region
    return "develop", None


def _order_visible_text(action: str, target: str | None) -> str:
    """Map ``recommended_order`` result to the visible recommendation line."""
    if action == "assault":
        return f"Zalecany rozkaz: szturmuj osadę {target}"
    if action == "engage":
        return f"Zalecany rozkaz: zaatakuj oddział {target}"
    if action == "defend":
        return f"Zalecany rozkaz: broń pozycji {target}"
    return _BALANCED_ORDER


def render_recommended_action(
    world: WorldMap,
    game: GameState,
    player_duchy_id: str | None = None,
) -> str:
    """Return a one-line recommended-action root for the player's posture.

    Root is ``<div data-recommended-action="">``. When ``player_duchy_id`` is
    ``None`` or not in ``game.duchies`` (``player_duchy(...) is None``), returns
    a bare empty root with no ``data-posture``, no ``data-action``, no visible
    text, and no children. When the player is known, the root carries
    ``data-posture`` from ``situationreport.net_posture(M, N)`` (M =
    ``engagementpreview.advantageous_target_count``, N =
    ``threatalert.threatened_position_count``), then ``data-action`` and
    visible text from ``recommended_order`` (``assault|engage|defend|develop``
    and the matching order line). Pure and deterministic: no RNG/IO; does not
    mutate ``world`` or ``game``.
    """
    order = recommended_order(world, game, player_duchy_id)
    if order is None:
        return '<div data-recommended-action=""></div>'

    assert player_duchy_id is not None
    action, target = order
    m = advantageous_target_count(world, game, player_duchy_id)
    n = threatened_position_count(world, game, player_duchy_id)
    posture = net_posture(m, n)
    text = _order_visible_text(action, target)
    return (
        f'<div data-recommended-action="" data-posture="{posture}" '
        f'data-action="{action}">{text}</div>'
    )
