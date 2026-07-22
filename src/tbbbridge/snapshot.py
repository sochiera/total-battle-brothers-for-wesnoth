"""Czysta serializacja stanu rdzenia gry do json-serializowalnych słowników."""

import json
from typing import Any

from tbb.party import Party
from tbb.settlement import Settlement
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
