"""Deterministic HTML fragment for a one-line tactical situation report."""

from __future__ import annotations

from tbb.game import GameState
from tbb.world import WorldMap
from tbbui.engagementpreview import advantageous_target_count
from tbbui.gamelookup import player_duchy
from tbbui.threatalert import threatened_position_count

_POSTURE_LABELS = {
    "offensive": "ofensywna",
    "defensive": "defensywna",
    "balanced": "zrównoważona",
}


def net_posture(opportunity_count: int, threatened_count: int) -> str:
    """Return posture from M (opportunities) vs N (threats).

    ``"offensive"`` when M>N, ``"defensive"`` when N>M, ``"balanced"`` when
    M==N. Pure and deterministic; no side effects.
    """
    if opportunity_count > threatened_count:
        return "offensive"
    if threatened_count > opportunity_count:
        return "defensive"
    return "balanced"


def render_situation_report(
    world: WorldMap,
    game: GameState,
    player_duchy_id: str | None = None,
) -> str:
    """Return a one-line situation-report root for threats and opportunities.

    Root is ``<div data-situation-report="">``. When ``player_duchy_id`` is
    ``None`` or not in ``game.duchies`` (``player_duchy(...) is None``), returns
    a bare empty root with no ``data-threatened-count``, no
    ``data-opportunity-count``, no ``data-net-posture``, no visible text, and no
    children. When the player is known, the root carries
    ``data-threatened-count="N"`` (via ``threatalert.threatened_position_count``),
    ``data-opportunity-count="M"`` (via
    ``engagementpreview.advantageous_target_count``), ``data-net-posture``
    immediately after (from public ``net_posture(M, N)``) and visible text
    ``Sytuacja: zagrożone pozycje N, korzystne cele M — postawa:
    ofensywna|defensywna|zrównoważona``. Pure and deterministic: no RNG/IO;
    does not mutate ``world`` or ``game``.
    """
    if player_duchy(game, player_duchy_id) is None:
        return '<div data-situation-report=""></div>'

    # player_duchy is not None ⇒ player_duchy_id is a known str
    assert player_duchy_id is not None
    n = threatened_position_count(world, game, player_duchy_id)
    m = advantageous_target_count(world, game, player_duchy_id)
    posture = net_posture(m, n)
    label = _POSTURE_LABELS[posture]
    return (
        f'<div data-situation-report=""'
        f' data-threatened-count="{n}"'
        f' data-opportunity-count="{m}"'
        f' data-net-posture="{posture}">'
        f"Sytuacja: zagrożone pozycje {n}, korzystne cele {m}"
        f" — postawa: {label}</div>"
    )
