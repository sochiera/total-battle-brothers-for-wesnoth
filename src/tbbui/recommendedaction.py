"""Deterministic HTML fragment for a one-line recommended action."""

from __future__ import annotations

import html

from tbb import ai
from tbb.game import GameState
from tbb.world import WorldMap
from tbbui.engagementpreview import (
    advantageous_target_count,
    first_advantageous_target,
)
from tbbui.gamelookup import player_duchy
from tbbui.maplookup import first_party_region, is_hostile_owner
from tbbui.situationreport import net_posture
from tbbui.threatalert import first_threatened_region, threatened_position_count
from tbbui.unitstrength import combat_totals


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


def recommended_battle_forecast(
    world: WorldMap,
    game: GameState,
    player_duchy_id: str | None = None,
) -> tuple[int, int] | None:
    """Return ``(own_total, enemy_total)`` for a recommended battle order.

    Scalar combat strength is ``sum(combat_totals(...))`` (``hp+attack+defense``).
    Returns ``None`` when ``recommended_order(world, game, player_duchy_id)`` is
    ``None`` or the action is not in ``{"assault", "engage", "defend"}``
    (``march`` / ``develop`` / ``muster`` → ``None``). For ``assault`` with
    target region name ``R``: own strength from the player party at
    ``first_party_region``, enemy from the settlement garrison in ``R``. For
    ``engage``: enemy from the hostile party in ``R``. For ``defend`` with
    target ``R``: own strength from the player settlement garrison in ``R``
    when present, otherwise the player party there; enemy from the first
    adjacent hostile party (``is_hostile_owner``, ``world.neighbors`` order —
    same rule as threat-alert). Pure and deterministic: no RNG/IO; does not
    mutate ``world`` or ``game``; delegates action/target selection to
    ``recommended_order`` (K51.1a / K51.1b).
    """
    order = recommended_order(world, game, player_duchy_id)
    if order is None:
        return None
    action, target = order
    if action not in {"assault", "engage", "defend"}:
        return None

    assert player_duchy_id is not None
    assert target is not None
    target_region = next(r for r in world.regions if r.name == target)

    if action == "defend":
        settlement = world.settlement_at(target_region)
        if (
            settlement is not None
            and settlement.owner_id == player_duchy_id
        ):
            own_total = sum(combat_totals(settlement.garrison))
        else:
            party = world.party_at(target_region)
            assert party is not None
            own_total = sum(combat_totals((party.hero, *party.units)))
        enemy = None
        for neighbor in world.neighbors(target_region):
            p = world.party_at(neighbor)
            if p is not None and is_hostile_owner(p.owner_id, player_duchy_id):
                enemy = p
                break
        assert enemy is not None
        enemy_total = sum(combat_totals((enemy.hero, *enemy.units)))
        return (own_total, enemy_total)

    origin = first_party_region(world, player_duchy_id)
    assert origin is not None
    party = world.party_at(origin)
    assert party is not None
    own_total = sum(combat_totals((party.hero, *party.units)))

    if action == "assault":
        settlement = world.settlement_at(target_region)
        assert settlement is not None
        enemy_total = sum(combat_totals(settlement.garrison))
    else:
        enemy = world.party_at(target_region)
        assert enemy is not None
        enemy_total = sum(combat_totals((enemy.hero, *enemy.units)))
    return (own_total, enemy_total)


def recommended_battle_forecast_text(
    world: WorldMap,
    game: GameState,
    player_duchy_id: str | None = None,
) -> str:
    """Return a human-readable battle-strength forecast for the advice line.

    Returns ``""`` when ``recommended_battle_forecast(world, game,
    player_duchy_id) is None`` (no player, or non-battle orders muster /
    march / develop). When the forecast is ``(own, enemy)``, returns exactly
    ``f"Przewidywana siła: Ty {own} vs wróg {enemy} — {verdict}"`` with
    ``verdict = "przewaga"`` if ``own >= enemy``, else ``"ryzyko"``. Pure and
    deterministic: no RNG/IO; does not mutate ``world`` or ``game``; delegates
    the forecast decision to ``recommended_battle_forecast`` (K51.1c).
    """
    forecast = recommended_battle_forecast(world, game, player_duchy_id)
    if forecast is None:
        return ""
    own, enemy = forecast
    verdict = "przewaga" if own >= enemy else "ryzyko"
    return f"Przewidywana siła: Ty {own} vs wróg {enemy} — {verdict}"


def recommended_battle_is_risky(
    world: WorldMap,
    game: GameState,
    player_duchy_id: str | None = None,
) -> bool:
    """Return whether the recommended battle has a predicted strength deficit.

    Returns ``False`` when ``recommended_battle_forecast(world, game,
    player_duchy_id) is None`` (no player / order ``None`` / action
    ``muster`` / ``march`` / ``develop``). When the forecast is
    ``(own, enemy)``, returns ``True`` iff ``own < enemy`` (same threshold as
    the ``ryzyko`` verdict in ``recommended_battle_forecast_text``), otherwise
    ``False``. Pure and deterministic: no RNG/IO; does not mutate ``world``
    or ``game``; delegates the forecast decision to
    ``recommended_battle_forecast`` as the sole source of the prediction
    (K52.1a).
    """
    forecast = recommended_battle_forecast(world, game, player_duchy_id)
    if forecast is None:
        return False
    own, enemy = forecast
    return own < enemy


def _escaped_paragraph(attr: str, text: str) -> str:
    """Return an HTML ``<p data-{attr}="…">…</p>`` or ``""`` if ``text`` is empty.

    Empty ``text`` → ``""``. Otherwise ``html.escape(text, quote=True)`` is used
    for both the attribute value and the element body. Shared by
    ``render_recommended_action`` and ``GameApp._recommended_order_form``.
    """
    if not text:
        return ""
    escaped = html.escape(text, quote=True)
    return f'<p data-{attr}="{escaped}">{escaped}</p>'


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


def recommended_order_reason(
    world: WorldMap,
    game: GameState,
    player_duchy_id: str | None = None,
) -> str:
    """Return a human-readable *why* for the recommended order.

    Delegates the decision to ``recommended_order`` (sole source of
    ``(action, target)``). Returns ``""`` when that call returns ``None``
    (no player / id not in ``game.duchies``). Otherwise exact text per
    action: muster / assault / engage / defend / march / develop (K50.1a).
    Pure and deterministic: no RNG/IO; does not mutate ``world`` or ``game``.
    """
    order = recommended_order(world, game, player_duchy_id)
    if order is None:
        return ""
    action, target = order
    if action == "muster":
        return (
            "Masz bohatera i wolną osadę, lecz żaden oddział nie stoi na mapie"
        )
    if action == "assault":
        return f"Twój oddział ma przewagę nad garnizonem osady {target}"
    if action == "engage":
        return f"Twój oddział ma przewagę nad wrogim oddziałem w {target}"
    if action == "defend":
        return f"Pozycję {target} zagraża sąsiedni wrogi oddział"
    if action == "march":
        return (
            f"Brak celów i zagrożeń w zasięgu; najbliższa wroga osada to {target}"
        )
    return "Brak zagrożeń i celów w zasięgu — rozwijaj gospodarkę"


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
    line), plus exactly one child
    ``<p data-recommendation-reason="{reason}">{reason}</p>`` from
    ``recommended_order_reason`` (``html.escape(..., quote=True)`` on attribute
    and body). When ``recommended_battle_forecast_text`` is non-empty, a second
    child ``<p data-recommended-forecast="{text}">{text}</p>`` follows the
    reason (same escape rule); empty forecast or no player → no forecast
    element (K51.1d). Pure and deterministic: no RNG/IO; does not mutate
    ``world`` or ``game``.
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
    reason = recommended_order_reason(world, game, player_duchy_id)
    reason_html = _escaped_paragraph("recommendation-reason", reason)
    forecast = recommended_battle_forecast_text(
        world, game, player_duchy_id
    )
    forecast_html = _escaped_paragraph("recommended-forecast", forecast)
    return (
        f'<div data-recommended-action="" data-posture="{posture}" '
        f'data-action="{action}">{text}'
        f"{reason_html}"
        f"{forecast_html}</div>"
    )
