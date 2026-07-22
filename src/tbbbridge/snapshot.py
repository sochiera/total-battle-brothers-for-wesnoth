"""Czysta serializacja stanu rdzenia gry do json-serializowalnych słowników."""

import json
import os
from typing import Any

from tbb.battle import HexBattle
from tbb.duchy import Duchy
from tbb.game import GameState
from tbb.party import Party
from tbb.settlement import Settlement
from tbb.turn import Calendar
from tbb.world import WorldMap
from tbbui.layout import layout_world
from tbbui.unitstrength import combat_totals, wounded_count


def _assert_json_serializable(state: dict[str, Any]) -> None:
    """Sprawdź, że słownik da się zapisać do JSON."""
    json.dumps(state)


def settlement_state(settlement: Settlement) -> dict[str, Any]:
    """Zwróć json-serializowalny snapshot pojedynczej osady.

    Funkcja jest czysta i deterministyczna — nie mutuje wejścia, nie wykonuje
    IO, a wynik przechodzi przez `json.dumps`.

    Klucze wyniku i ich źródła w publicznym API `Settlement`:
      name               -> settlement.name
      owner              -> settlement.owner_id
      wheat              -> settlement.storage.wheat
      gold               -> settlement.storage.gold
      population         -> settlement.population
      free               -> settlement.free
      garrison           -> len(settlement.garrison)
      buildings          -> [b.name for b in settlement.active_buildings]
      wheat_production   -> settlement.production.wheat
      gold_production    -> settlement.production.gold
      wheat_consumption  -> settlement.consumption.wheat
    """
    state: dict[str, Any] = {
        "name": settlement.name,
        "owner": settlement.owner_id,
        "wheat": settlement.storage.wheat,
        "gold": settlement.storage.gold,
        "population": settlement.population,
        "free": settlement.free,
        "garrison": len(settlement.garrison),
        "buildings": [building.name for building in settlement.active_buildings],
        "wheat_production": settlement.production.wheat,
        "gold_production": settlement.production.gold,
        "wheat_consumption": settlement.consumption.wheat,
    }
    # Weryfikacja serializowalności — gdyby kiedykolwiek ktoś dodał
    # niestandardowy obiekt, test od razu to złapie.
    _assert_json_serializable(state)
    return state


def party_state(party: Party) -> dict[str, Any]:
    """Zwróć json-serializowalny snapshot pojedynczego oddziału.

    Funkcja jest czysta i deterministyczna — nie mutuje wejścia, nie wykonuje
    IO, a wynik przechodzi przez `json.dumps`.

    Klucze wyniku i ich źródła w publicznym API `Party` oraz `tbbui.unitstrength`:
      owner    -> party.owner_id
      size     -> len(party.units)
      hp       -> combat_totals((party.hero, *party.units))[0]
      attack   -> combat_totals((party.hero, *party.units))[1]
      defense  -> combat_totals((party.hero, *party.units))[2]
      wounded  -> wounded_count((party.hero, *party.units))
    """
    roster = (party.hero, *party.units)
    hp, attack, defense = combat_totals(roster)
    state: dict[str, Any] = {
        "owner": party.owner_id,
        "size": len(party.units),
        "hp": hp,
        "attack": attack,
        "defense": defense,
        "wounded": wounded_count(roster),
    }
    _assert_json_serializable(state)
    return state


def _owner_from(settlement: Settlement | None, party: Party | None) -> str | None:
    """Region owner: settlement first, then party, otherwise None.

    Matches the strategic-map rule visualised by the diagnostic UI: the
    settlement's owner is decisive when present; if there is only a party,
    the party's owner controls the region.
    """
    if settlement is not None:
        return settlement.owner_id
    if party is not None:
        return party.owner_id
    return None


def map_state(world: WorldMap) -> dict[str, Any]:
    """Zwróć json-serializowalny snapshot grafu świata dla klienta Godot.

    Funkcja jest czysta, deterministyczna i bez mutacji wejścia.

    Klucze wyniku i ich źródła:
      regions     -> lista regionów z `world.regions`, każdy z:
        name        -> region.name
        col, row    -> layout_world(world)[region]
        owner       -> owner osady, potem owner party, potem None
        settlement  -> settlement_state(world.settlement_at(region)) lub None
        party       -> party_state(world.party_at(region)) lub None
      connections -> {"from": a.name, "to": b.name} dla world.connections
    """
    positions = layout_world(world)
    regions: list[dict[str, Any]] = []
    for region in world.regions:
        col, row = positions[region]
        settlement = world.settlement_at(region)
        party = world.party_at(region)
        regions.append({
            "name": region.name,
            "col": col,
            "row": row,
            "owner": _owner_from(settlement, party),
            "settlement": settlement_state(settlement) if settlement is not None else None,
            "party": party_state(party) if party is not None else None,
        })

    connections = [
        {"from": a.name, "to": b.name}
        for a, b in world.connections
    ]

    state: dict[str, Any] = {
        "regions": regions,
        "connections": connections,
    }
    _assert_json_serializable(state)
    return state


def _duchy_state(duchy: Duchy) -> dict[str, Any]:
    """Json-serializowalny status jednego księstwa."""
    return {
        "id": duchy.duchy_id,
        "morale": duchy.morale,
        "settlements": len(duchy.settlements),
        "parties": len(duchy.parties),
        "has_hero": duchy.has_hero,
        "has_heir": duchy.heir is not None,
        "is_defeated": duchy.is_defeated,
    }


def _player_result(game: GameState, player_duchy_id: str | None) -> str | None:
    """Wynik z perspektywy gracza."""
    if player_duchy_id is None:
        return None
    if not game.is_over:
        return "ongoing"
    if game.winner is None:
        return "draw"
    if game.winner.duchy_id == player_duchy_id:
        return "victory"
    return "defeat"


def game_state(
    world: WorldMap,
    game: GameState,
    calendar: Calendar,
    player_duchy_id: str | None = None,
    battle: HexBattle | None = None,
) -> dict[str, Any]:
    """Zwróć json-serializowalny snapshot pełnego stanu gry.

    Funkcja jest czysta, deterministyczna i bez mutacji wejść; wynik przechodzi
    przez `json.dumps`.

    Gdy `battle` jest podane, jako ostatni klucz osadzany jest
    `battle_state(battle)`. Gdy `battle is None` (domyślnie), wynik pozostaje
    bajt-w-bajt identyczny z wcześniejszą postacią funkcji.

    Klucze wyniku dokładnie w kolejności:
      calendar -> {"year": calendar.year, "month": calendar.month}
      duchies  -> lista statusów księstw (kolejność game.duchies)
      map      -> map_state(world)
      result   -> {"is_over": ..., "winner": ..., "player_result": ...}
      battle   -> battle_state(battle) (tylko gdy battle is not None)
    """
    state: dict[str, Any] = {
        "calendar": {"year": calendar.year, "month": calendar.month},
        "duchies": [_duchy_state(duchy) for duchy in game.duchies],
        "map": map_state(world),
        "result": {
            "is_over": game.is_over,
            "winner": game.winner.duchy_id if game.winner is not None else None,
            "player_result": _player_result(game, player_duchy_id),
        },
    }
    if battle is not None:
        state["battle"] = battle_state(battle)
    _assert_json_serializable(state)
    return state


def battle_state(battle: HexBattle) -> dict[str, Any]:
    """Zwróć json-serializowalny snapshot bitwy heksowej.

    Funkcja jest czysta, deterministyczna i bez mutacji `battle`; wynik
    przechodzi przez `json.dumps`.

    Klucze wyniku i ich źródła w publicznym API `HexBattle`:
      hexes  -> lista zajętych heksów `battle.units`, posortowana po (q, r),
                każdy z kluczami q, r, terrain, side, hp, stunned
      result -> `battle.result().value` gdy rozstrzygnięta, inaczej `None`
    """
    hexes: list[dict[str, Any]] = []
    for hex_pos in sorted(battle.units.keys(), key=lambda h: (h.q, h.r)):
        unit = battle.units[hex_pos]
        hexes.append({
            "q": hex_pos.q,
            "r": hex_pos.r,
            "terrain": battle.battlefield.terrain_at(hex_pos).name,
            "side": battle.side_at(hex_pos).value,
            "hp": battle.current_hp_at(hex_pos),
            "stunned": bool(unit.stunned),
        })

    result = battle.result()
    state: dict[str, Any] = {
        "hexes": hexes,
        "result": result.value if result is not None else None,
    }
    _assert_json_serializable(state)
    return state


def save_state(
    world: WorldMap,
    game: GameState,
    calendar: Calendar,
    path: str | os.PathLike[str],
    player_duchy_id: str | None = None,
) -> None:
    """Zapisz deterministyczny JSON snapshot pełnego stanu gry do pliku.

    Funkcja jest czysta względem stanu gry — nie mutuje `world`, `game` ani
    `calendar`. Nie tworzy katalogów docelowych; zapis do nieistniejącego
    katalogu zakończy się błędem systemowym.

    Format pliku: `json.dumps(game_state(...), indent=2, ensure_ascii=False)`
    zakończony pojedynczym znakiem "\\n", kodowanie UTF-8.
    """
    payload = json.dumps(
        game_state(world, game, calendar, player_duchy_id),
        indent=2,
        ensure_ascii=False,
    )
    with open(path, "w", encoding="utf-8") as f:
        f.write(payload)
        f.write("\n")
