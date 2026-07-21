"""Deterministic HTML fragment for threatened-position alert."""

from __future__ import annotations

from tbb.game import GameState
from tbb.world import Region, WorldMap
from tbbui.gamelookup import player_duchy


def _has_hostile_neighbor(
    world: WorldMap, region: Region, player_duchy_id: str
) -> bool:
    for neighbor in world.neighbors(region):
        party = world.party_at(neighbor)
        if party is None:
            continue
        owner = party.owner_id
        if owner is not None and owner != player_duchy_id:
            return True
    return False


def _count_threatened_positions(
    world: WorldMap, player_duchy_id: str
) -> int:
    """Count own settlement and party positions threatened by adjacent enemies.

    Settlement and party in the same region count separately. A position is
    threatened when at least one neighbor has a party with explicit
    ``owner_id != player_duchy_id``.
    """
    count = 0
    for region in world.regions:
        threatened = _has_hostile_neighbor(world, region, player_duchy_id)
        if not threatened:
            continue
        settlement = world.settlement_at(region)
        if settlement is not None and settlement.owner_id == player_duchy_id:
            count += 1
        party = world.party_at(region)
        if party is not None and party.owner_id == player_duchy_id:
            count += 1
    return count


def render_threat_alert(
    world: WorldMap,
    game: GameState,
    player_duchy_id: str | None = None,
) -> str:
    """Return an alert root for own positions threatened by adjacent enemy parties.

    Root is ``<div data-threat-alert="">``. When ``player_duchy_id`` is ``None``
    or not in ``game.duchies`` (``player_duchy(...) is None``), returns a bare
    empty root with no ``data-threats``, no visible text, and no children.
    When the player is known, the root carries ``data-threats="N"`` and visible
    text ``Zagrożone pozycje: N``, where ``N`` is the number of own map
    positions (player settlement and/or party, counted separately per region
    and kind) that have at least one neighboring region with a party whose
    ``owner_id`` is set and ``!= player_duchy_id``. No child rows at this stage.
    Pure and deterministic: no RNG/IO; does not mutate ``world`` or ``game``.
    """
    if player_duchy(game, player_duchy_id) is None:
        return '<div data-threat-alert=""></div>'

    # player_duchy is not None ⇒ player_duchy_id is a known str
    assert player_duchy_id is not None
    n = _count_threatened_positions(world, player_duchy_id)
    return (
        f'<div data-threat-alert="" data-threats="{n}">'
        f"Zagrożone pozycje: {n}"
        f"</div>"
    )
