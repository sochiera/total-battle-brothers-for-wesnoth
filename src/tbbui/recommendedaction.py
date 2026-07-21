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


def _offensive_order_text(
    world: WorldMap,
    game: GameState,
    player_duchy_id: str,
) -> str:
    """Name the first advantageous assault/engage target for offensive posture.

    Offensive posture implies M≥1, so a target exists. Settlement →
    ``szturmuj osadę <region>``; party → ``zaatakuj oddział <region>``.
    """
    target = first_advantageous_target(world, game, player_duchy_id)
    assert target is not None
    region, kind = target
    if kind == "settlement":
        return f"Zalecany rozkaz: szturmuj osadę {region}"
    return f"Zalecany rozkaz: zaatakuj oddział {region}"


def _defensive_order_text(
    world: WorldMap,
    game: GameState,
    player_duchy_id: str,
) -> str:
    """Name the first threatened own position for defensive posture.

    Defensive posture implies N≥1, so a region exists.
    """
    region = first_threatened_region(world, game, player_duchy_id)
    assert region is not None
    return f"Zalecany rozkaz: broń pozycji {region}"


def render_recommended_action(
    world: WorldMap,
    game: GameState,
    player_duchy_id: str | None = None,
) -> str:
    """Return a one-line recommended-action root for the player's posture.

    Root is ``<div data-recommended-action="">``. When ``player_duchy_id`` is
    ``None`` or not in ``game.duchies`` (``player_duchy(...) is None``), returns
    a bare empty root with no ``data-posture``, no visible text, and no children.
    When the player is known, the root carries ``data-posture`` from
    ``situationreport.net_posture(M, N)`` (M =
    ``engagementpreview.advantageous_target_count``, N =
    ``threatalert.threatened_position_count``) and visible text:
    offensive → ``Zalecany rozkaz: szturmuj osadę <region>`` or
    ``zaatakuj oddział <region>`` from ``first_advantageous_target``;
    defensive → ``broń pozycji <region>`` from ``first_threatened_region``;
    balanced → ``rozwijaj księstwo``. Pure and deterministic: no RNG/IO; does
    not mutate ``world`` or ``game``.
    """
    if player_duchy(game, player_duchy_id) is None:
        return '<div data-recommended-action=""></div>'

    assert player_duchy_id is not None
    m = advantageous_target_count(world, game, player_duchy_id)
    n = threatened_position_count(world, game, player_duchy_id)
    posture = net_posture(m, n)
    if posture == "offensive":
        text = _offensive_order_text(world, game, player_duchy_id)
    elif posture == "defensive":
        text = _defensive_order_text(world, game, player_duchy_id)
    else:
        text = _BALANCED_ORDER
    return (
        f'<div data-recommended-action="" data-posture="{posture}">'
        f"{text}</div>"
    )
