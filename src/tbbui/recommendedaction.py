"""Deterministic HTML fragment for a one-line recommended action."""

from __future__ import annotations

from tbb import ai
from tbb.game import GameState
from tbb.world import WorldMap
from tbbui.engagementpreview import (
    advantageous_target_count,
    first_advantageous_target,
)
from tbbui.gamelookup import player_duchy
from tbbui.maplookup import first_party_region
from tbbui.situationreport import net_posture
from tbbui.threatalert import first_threatened_region, threatened_position_count


def player_march_target(
    world: WorldMap,
    game: GameState,
    player_duchy_id: str | None,
) -> str | None:
    """Return the name of a distant enemy settlement for idle march advice.

    ``None`` when ``player_duchy(game, player_duchy_id) is None`` or
    ``first_party_region(world, player_duchy_id) is None``. When the player has
    a party in region R and ``ai.nearest_enemy_settlement(world, R, id)`` exists
    with ``ai.region_distance(world, R, target) >= 2``, returns ``target.name``;
    when the nearest enemy settlement is ``None`` or has distance ``< 2``,
    returns ``None``. Pure and deterministic: no RNG/IO; does not mutate
    ``world`` or ``game``.
    """
    if player_duchy(game, player_duchy_id) is None:
        return None
    assert player_duchy_id is not None
    origin = first_party_region(world, player_duchy_id)
    if origin is None:
        return None
    target = ai.nearest_enemy_settlement(world, origin, player_duchy_id)
    if target is None:
        return None
    distance = ai.region_distance(world, origin, target)
    if distance is None or distance < 2:
        return None
    return target.name


def player_can_muster(
    world: WorldMap,
    game: GameState,
    player_duchy_id: str | None,
) -> bool:
    """Return whether the player can muster a party on the strategic map.

    True iff ``player_duchy(game, player_duchy_id)`` is known, the duchy has a
    hero (``Duchy.has_hero``), ``first_party_region(world, player_duchy_id)``
    is ``None`` (no player party on the map), and some region in
    ``world.regions`` holds an own settlement with a free party slot
    (``settlement.owner_id == player_duchy_id and region not in world.parties``)
    — same free-settlement predicate as successful ``ai.muster_duchy_party``.
    Otherwise False (including ``player_duchy_id`` None/unknown, no hero,
    party already fielded, or no free own settlement). Pure and deterministic:
    no RNG/IO; does not mutate ``world`` or ``game``.
    """
    duchy = player_duchy(game, player_duchy_id)
    if duchy is None:
        return False
    assert player_duchy_id is not None
    if not duchy.has_hero:
        return False
    if first_party_region(world, player_duchy_id) is not None:
        return False
    for region in world.regions:
        settlement = world.settlement_at(region)
        if (
            settlement is not None
            and settlement.owner_id == player_duchy_id
            and region not in world.parties
        ):
            return True
    return False


def recommended_order(
    world: WorldMap,
    game: GameState,
    player_duchy_id: str | None = None,
) -> tuple[str, str | None] | None:
    """Return machine decision ``(action, target_region_name)`` for the player.

    ``action`` ∈ ``{"muster", "assault", "engage", "defend", "march",
    "develop"}``; ``target`` is the region name, or ``None`` for
    ``muster``/``develop``. Returns ``None`` when
    ``player_duchy(game, player_duchy_id) is None`` (no player or id not in
    ``game.duchies``). When ``player_can_muster(...)`` is True, returns
    ``("muster", None)`` before posture (K48.1c). Offensive/defensive as
    before; on balanced path, ``("march", player_march_target(...))`` when
    that target is not ``None``, else ``("develop", None)`` (K49.1c). Pure
    and deterministic: no RNG/IO; does not mutate ``world`` or ``game``.
    """
    if player_duchy(game, player_duchy_id) is None:
        return None

    assert player_duchy_id is not None
    if player_can_muster(world, game, player_duchy_id):
        return "muster", None

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
    march_target = player_march_target(world, game, player_duchy_id)
    if march_target is not None:
        return "march", march_target
    return "develop", None


def recommended_order_text(action: str, target_name: str | None) -> str:
    """Descriptive half of the advice line (no ``Zalecany rozkaz: `` prefix).

    ``("assault", R)`` → ``szturmuj osadę <R>``; ``("engage", R)`` →
    ``zaatakuj oddział <R>``; ``("defend", R)`` → ``broń pozycji <R>``;
    ``("march", R)`` → ``maszeruj ku osadzie <R>``; ``("muster", None)`` →
    ``zbierz oddział``; ``("develop", None)`` → ``rozwijaj księstwo``.
    Pure and deterministic. Shared by ``render_recommended_action`` and the
    GameApp button label.
    """
    if action == "assault":
        return f"szturmuj osadę {target_name}"
    if action == "engage":
        return f"zaatakuj oddział {target_name}"
    if action == "defend":
        return f"broń pozycji {target_name}"
    if action == "march":
        return f"maszeruj ku osadzie {target_name}"
    if action == "muster":
        return "zbierz oddział"
    return "rozwijaj księstwo"


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
    visible text from ``recommended_order`` / ``recommended_order_text``
    (``muster|assault|engage|defend|march|develop`` and the matching order
    line). Pure and deterministic: no RNG/IO; does not mutate ``world`` or
    ``game``.
    """
    order = recommended_order(world, game, player_duchy_id)
    if order is None:
        return '<div data-recommended-action=""></div>'

    assert player_duchy_id is not None
    action, target = order
    m = advantageous_target_count(world, game, player_duchy_id)
    n = threatened_position_count(world, game, player_duchy_id)
    posture = net_posture(m, n)
    text = f"Zalecany rozkaz: {recommended_order_text(action, target)}"
    return (
        f'<div data-recommended-action="" data-posture="{posture}" '
        f'data-action="{action}">{text}</div>'
    )
