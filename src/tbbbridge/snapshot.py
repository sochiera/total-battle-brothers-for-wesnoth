"""Czysta serializacja stanu rdzenia gry do json-serializowalnych słowników."""

import json
from typing import Any

from tbb.party import Party
from tbb.settlement import Settlement
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
