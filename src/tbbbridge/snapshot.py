"""Czysta serializacja stanu rdzenia gry do json-serializowalnych słowników."""

import json
from typing import Any

from tbb.settlement import Settlement


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
    json.dumps(state)
    return state
