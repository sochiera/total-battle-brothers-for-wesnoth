"""Deterministic HTML fragment for threatened-position alert."""

from __future__ import annotations

from tbb.game import GameState
from tbb.party import Party
from tbb.world import Region, WorldMap
from tbbui.gamelookup import player_duchy
from tbbui.maplookup import is_hostile_owner
from tbbui.unitstrength import combat_totals


def _first_hostile_neighbor(
    world: WorldMap, region: Region, player_duchy_id: str
) -> tuple[Region, Party] | None:
    """Return (neighbor region, party) of first hostile adjacent party.

    Walks ``world.neighbors(region)`` order; skips empty regions and parties
    without explicit ``owner_id`` or with ``owner_id == player_duchy_id``.
    """
    for neighbor in world.neighbors(region):
        party = world.party_at(neighbor)
        if party is None:
            continue
        if is_hostile_owner(party.owner_id, player_duchy_id):
            return neighbor, party
    return None


def _strength_attrs_and_suffix(
    own_units, enemy_party: Party
) -> tuple[str, str]:
    """Return (HTML attrs fragment, visible text suffix) for own vs enemy strength.

    Includes ``data-defensible`` (after ``data-enemy-defense``) and a final
    verdict suffix: own sum (HP+attack+defense) ≥ enemy sum → true /
    `` — obronisz się``; otherwise false / `` — przewaga wroga``.
    """
    own_hp, own_attack, own_defense = combat_totals(own_units)
    enemy_hp, enemy_attack, enemy_defense = combat_totals(
        (enemy_party.hero, *enemy_party.units)
    )
    own_sum = own_hp + own_attack + own_defense
    enemy_sum = enemy_hp + enemy_attack + enemy_defense
    defensible = own_sum >= enemy_sum
    defensible_attr = "true" if defensible else "false"
    verdict = " — obronisz się" if defensible else " — przewaga wroga"
    attrs = (
        f' data-own-hp="{own_hp}"'
        f' data-own-attack="{own_attack}"'
        f' data-own-defense="{own_defense}"'
        f' data-enemy-hp="{enemy_hp}"'
        f' data-enemy-attack="{enemy_attack}"'
        f' data-enemy-defense="{enemy_defense}"'
        f' data-defensible="{defensible_attr}"'
    )
    suffix = (
        f" · siła obronna: HP {own_hp}, atak {own_attack},"
        f" obrona {own_defense}"
        f" · siła wroga: HP {enemy_hp}, atak {enemy_attack},"
        f" obrona {enemy_defense}"
        f"{verdict}"
    )
    return attrs, suffix


def _row_html(
    region: Region,
    kind: str,
    kind_label: str,
    enemy_region: Region,
    enemy_owner: str,
    own_units,
    enemy_party: Party,
) -> str:
    """One threatened-position row: identity attrs, strength attrs, and text."""
    strength_attrs, strength_suffix = _strength_attrs_and_suffix(
        own_units, enemy_party
    )
    return (
        f'<div data-threatened-region="{region.name}"'
        f' data-threatened-kind="{kind}"'
        f' data-enemy-region="{enemy_region.name}"'
        f' data-enemy-owner="{enemy_owner}"'
        f"{strength_attrs}>"
        f"{kind_label} {region.name}: zagrożenie od {enemy_owner}"
        f" z {enemy_region.name}{strength_suffix}</div>"
    )


def _threatened_rows(world: WorldMap, player_duchy_id: str) -> list[str]:
    """Build HTML row fragments for each threatened own position.

    Order follows ``world.regions``; within a region, settlement before party.
    """
    rows: list[str] = []
    for region in world.regions:
        hostile = _first_hostile_neighbor(world, region, player_duchy_id)
        if hostile is None:
            continue
        enemy_region, enemy_party = hostile
        enemy_owner = enemy_party.owner_id
        assert enemy_owner is not None

        settlement = world.settlement_at(region)
        if settlement is not None and settlement.owner_id == player_duchy_id:
            rows.append(
                _row_html(
                    region,
                    "settlement",
                    "Osada",
                    enemy_region,
                    enemy_owner,
                    settlement.garrison,
                    enemy_party,
                )
            )
        party = world.party_at(region)
        if party is not None and party.owner_id == player_duchy_id:
            rows.append(
                _row_html(
                    region,
                    "party",
                    "Oddział",
                    enemy_region,
                    enemy_owner,
                    (party.hero, *party.units),
                    enemy_party,
                )
            )
    return rows


def threatened_position_count(
    world: WorldMap,
    game: GameState,
    player_duchy_id: str | None,
) -> int:
    """Return the number of own positions threatened by adjacent enemy parties.

    Same rule as ``render_threat_alert`` rows: settlement and party counted
    separately; neighbor with explicit hostile party. When
    ``player_duchy(...) is None``, returns ``0``. Pure and deterministic: no
    RNG/IO; does not mutate ``world`` or ``game``.
    """
    if player_duchy(game, player_duchy_id) is None:
        return 0
    assert player_duchy_id is not None
    return len(_threatened_rows(world, player_duchy_id))


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
    text ``Zagrożone pozycje: N``, plus one child row per threatened own
    position (settlement and/or party, counted separately; order of
    ``world.regions``, settlement before party in the same region). Each row is
    ``data-threatened-region`` / ``data-threatened-kind`` /
    ``data-enemy-region`` / ``data-enemy-owner`` for the first neighboring
    party with explicit ``owner_id != player_duchy_id`` in ``world.neighbors``
    order, plus ``data-own-hp`` / ``data-own-attack`` / ``data-own-defense``
    (settlement garrison or party hero+units via ``combat_totals``) and
    ``data-enemy-hp`` / ``data-enemy-attack`` / ``data-enemy-defense`` (hostile
    party), then ``data-defensible`` (``"true"`` when own HP+attack+defense ≥
    enemy sum, else ``"false"``), with matching strength text suffix and
    final `` — obronisz się`` / `` — przewaga wroga``. ``N`` equals
    ``threatened_position_count`` (number of emitted rows). Pure and
    deterministic: no RNG/IO; does not mutate ``world`` or ``game``.
    """
    if player_duchy(game, player_duchy_id) is None:
        return '<div data-threat-alert=""></div>'

    # player_duchy is not None ⇒ player_duchy_id is a known str
    assert player_duchy_id is not None
    rows = _threatened_rows(world, player_duchy_id)
    n = threatened_position_count(world, game, player_duchy_id)
    return (
        f'<div data-threat-alert="" data-threats="{n}">'
        f"Zagrożone pozycje: {n}"
        f"{''.join(rows)}</div>"
    )
