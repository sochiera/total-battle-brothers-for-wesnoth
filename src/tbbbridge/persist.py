"""Persystencja round-trip — serializacja typów liściowych rdzenia.

Ten moduł to fundament zapisu/wczytywania stanu partii. Reużywa wyłącznie
publiczne API rdzenia, bez żadnej logiki reguł.
"""

import json
import os
from typing import Any

from tbb.building import Building
from tbb.duchy import Duchy
from tbb.party import Party
from tbb.resources import Resources
from tbb.settlement import Settlement
from tbb.terrain import Terrain
from tbb.turn import Calendar
from tbb.unit import Unit
from tbb.wound import Wound
from tbb.battlefield import Battlefield
from tbb.game import GameState
from tbb.hex import Hex
from tbb.rng import Rng
from tbb.world import Region, WorldMap
from tbbbridge.session import Session


def _convert_state(value, make_seq):
    """Rekurencyjnie zamienia sekwencje (``list``/``tuple``) na typ ``make_seq``.

    Służy do konwersji stanu ``random.Random`` między krotkami a listami:
    ``json.dumps`` akceptuje tylko listy, ``setstate`` wymaga krotek.
    """
    if isinstance(value, (list, tuple)):
        return make_seq(_convert_state(item, make_seq) for item in value)
    return value


def dump_rng(rng: Rng) -> dict:
    """Zwraca json-serializowalny słownik ``{"state": ...}`` dla ``Rng``.

    Stan pobierany jest przez ``rng.state()`` i sprowadzany do struktur
    JSON-owych (krotki zamieniane na listy).
    """
    return {"state": _convert_state(rng.state(), list)}


def load_rng(data: dict) -> Rng:
    """Odtwarza ``Rng`` ze słownika wyprodukowanego przez ``dump_rng``.

    Reużywa ``Rng.from_state`` z pola ``state`` (krotki przywrócone z list JSON).
    """
    return Rng.from_state(_convert_state(data["state"], tuple))


def dump_gamestate(game: GameState) -> dict:
    """Zwraca json-serializowalny słownik ``{"duchies": [...]}``.

    Lista ``duchies`` zawiera ``dump_duchy(duchy)`` w kolejności ``game.duchies``.
    """
    return {"duchies": [dump_duchy(duchy) for duchy in game.duchies]}


def load_gamestate(data: dict) -> GameState:
    """Odtwarza ``GameState`` ze słownika wyprodukowanego przez ``dump_gamestate``."""
    return GameState(tuple(load_duchy(d) for d in data["duchies"]))


def dump_hex(hex_coord: Hex) -> dict:
    """Zwraca json-serializowalny słownik ``{"q": int, "r": int}`` dla ``Hex``."""
    return {"q": hex_coord.q, "r": hex_coord.r}


def load_hex(data: dict) -> Hex:
    """Odtwarza ``Hex`` ze słownika wyprodukowanego przez ``dump_hex``."""
    return Hex(q=data["q"], r=data["r"])


def dump_terrain(terrain: Terrain) -> dict:
    """Zwraca json-serializowalny słownik ``Terrain``.

    Klucze: ``name`` (str), ``move_cost`` (int), ``defense_mod`` (int),
    ``accuracy_mod`` (int).
    """
    return {
        "name": terrain.name,
        "move_cost": terrain.move_cost,
        "defense_mod": terrain.defense_mod,
        "accuracy_mod": terrain.accuracy_mod,
    }


def dump_battlefield(battlefield: Battlefield) -> dict:
    """Zwraca json-serializowalny słownik ``{"terrain": [...]}`` dla ``Battlefield``.

    Każdy element zawiera ``{"hex": dump_hex(h), "terrain": dump_terrain(t)}``
    dla nadpisanych heksów, uporządkowany deterministycznie po ``(q, r)``.
    Pusta mapa daje ``{"terrain": []}``.
    """
    entries = sorted(
        ({"hex": dump_hex(hex_coord), "terrain": dump_terrain(terrain)}
         for hex_coord, terrain in battlefield._terrain.items()),
        key=lambda entry: (entry["hex"]["q"], entry["hex"]["r"]),
    )
    return {"terrain": entries}


def load_battlefield(data: dict) -> Battlefield:
    """Odtwarza ``Battlefield`` ze słownika wyprodukowanego przez ``dump_battlefield``.

    Mapa ``{load_hex(e["hex"]): load_terrain(e["terrain"]) for e in data["terrain"]}``.
    """
    return Battlefield(
        {load_hex(entry["hex"]): load_terrain(entry["terrain"])
         for entry in data["terrain"]}
    )


def load_terrain(data: dict) -> Terrain:
    """Odtwarza ``Terrain`` ze słownika wyprodukowanego przez ``dump_terrain``."""
    return Terrain(
        name=data["name"],
        move_cost=data["move_cost"],
        defense_mod=data["defense_mod"],
        accuracy_mod=data["accuracy_mod"],
    )


def dump_resources(res: Resources) -> dict:
    """Zwraca json-serializowalny słownik ``{"wheat": int, "gold": int}``."""
    return {"wheat": res.wheat, "gold": res.gold}


def load_resources(data: dict) -> Resources:
    """Odtwarza ``Resources`` ze słownika wyprodukowanego przez ``dump_resources``."""
    return Resources(wheat=data["wheat"], gold=data["gold"])


def dump_wound(wound: Wound) -> dict:
    """Zwraca json-serializowalny słownik ``Wound`` z polami
    ``name``, ``accuracy_mod``, ``defense_mod``, ``duration_months``.
    """
    return {
        "name": wound.name,
        "accuracy_mod": wound.accuracy_mod,
        "defense_mod": wound.defense_mod,
        "duration_months": wound.duration_months,
    }


def load_wound(data: dict) -> Wound:
    """Odtwarza ``Wound`` ze słownika wyprodukowanego przez ``dump_wound``."""
    return Wound(
        name=data["name"],
        accuracy_mod=data["accuracy_mod"],
        defense_mod=data["defense_mod"],
        duration_months=data["duration_months"],
    )


def dump_building(building: Building) -> dict:
    """Zwraca json-serializowalny słownik ``Building``.

    Klucze: ``name`` (str), ``staff`` (int), ``output`` (``dump_resources``).
    """
    return {
        "name": building.name,
        "staff": building.staff,
        "output": dump_resources(building.output),
    }


def load_building(data: dict) -> Building:
    """Odtwarza ``Building`` ze słownika wyprodukowanego przez ``dump_building``."""
    return Building(
        name=data["name"],
        staff=data["staff"],
        output=load_resources(data["output"]),
    )


def dump_unit(unit: Unit) -> dict:
    """Zwraca json-serializowalny słownik ``Unit``.

    Klucze: ``training``, ``equipment``, ``experience``, ``ranged_range``,
    ``wounds``, ``stunned``, ``training_progress``, ``equipment_progress``.
    ``wounds`` to lista wyników ``dump_wound`` w kolejności ``unit.wounds``.
    """
    return {
        "training": unit.training,
        "equipment": unit.equipment,
        "experience": unit.experience,
        "ranged_range": unit.ranged_range,
        "wounds": [dump_wound(w) for w in unit.wounds],
        "stunned": unit.stunned,
        "training_progress": unit.training_progress,
        "equipment_progress": unit.equipment_progress,
    }


def load_unit(data: dict) -> Unit:
    """Odtwarza ``Unit`` ze słownika wyprodukowanego przez ``dump_unit``."""
    return Unit(
        training=data["training"],
        equipment=data["equipment"],
        experience=data["experience"],
        ranged_range=data["ranged_range"],
        wounds=tuple(load_wound(w) for w in data["wounds"]),
        stunned=data["stunned"],
        training_progress=data["training_progress"],
        equipment_progress=data["equipment_progress"],
    )


def dump_party(party: Party) -> dict:
    """Zwraca json-serializowalny słownik ``Party``.

    Klucze: ``hero`` (``dump_unit``), ``units`` (lista ``dump_unit``),
    ``owner_id`` (``str | None``).
    """
    return {
        "hero": dump_unit(party.hero),
        "units": [dump_unit(unit) for unit in party.units],
        "owner_id": party.owner_id,
    }


def load_party(data: dict) -> Party:
    """Odtwarza ``Party`` ze słownika wyprodukowanego przez ``dump_party``."""
    return Party(
        hero=load_unit(data["hero"]),
        units=tuple(load_unit(u) for u in data["units"]),
        owner_id=data["owner_id"],
    )


def dump_region(region: Region) -> dict:
    """Zwraca json-serializowalny słownik ``{"name": region.name}``."""
    return {"name": region.name}


def load_region(data: dict) -> Region:
    """Odtwarza ``Region`` ze słownika wyprodukowanego przez ``dump_region``."""
    return Region(name=data["name"])


def dump_calendar(calendar: Calendar) -> dict:
    """Zwraca json-serializowalny słownik ``{"year": int, "month": int}``."""
    return {"year": calendar.year, "month": calendar.month}


def load_calendar(data: dict) -> Calendar:
    """Odtwarza ``Calendar`` ze słownika wyprodukowanego przez ``dump_calendar``."""
    return Calendar(year=data["year"], month=data["month"])


def dump_world(world: WorldMap) -> dict:
    """Zwraca json-serializowalny słownik ``WorldMap``.

    Klucze: ``regions`` (lista ``dump_region`` w kolejności ``world.regions``),
    ``connections`` (lista par ``[i, j]`` — indeksy w liście regionów),
    ``settlements`` i ``parties`` (listy par ``[i, dump_*]`` po indeksie regionu).
    """
    regions = world.regions
    region_index = {region: index for index, region in enumerate(regions)}
    return {
        "regions": [dump_region(region) for region in regions],
        "connections": [
            [region_index[first], region_index[second]]
            for first, second in world.connections
        ],
        "settlements": [
            [region_index[region], dump_settlement(settlement)]
            for region, settlement in world.settlements.items()
        ],
        "parties": [
            [region_index[region], dump_party(party)]
            for region, party in world.parties.items()
        ],
    }


def load_world(data: dict) -> WorldMap:
    """Odtwarza ``WorldMap`` ze słownika wyprodukowanego przez ``dump_world``."""
    regions = tuple(load_region(region_data) for region_data in data["regions"])
    connections = tuple(
        (regions[first_index], regions[second_index])
        for first_index, second_index in data["connections"]
    )
    settlements = {
        regions[index]: load_settlement(settlement_data)
        for index, settlement_data in data["settlements"]
    }
    parties = {
        regions[index]: load_party(party_data)
        for index, party_data in data["parties"]
    }
    return WorldMap(
        regions=regions,
        connections=connections,
        settlements=settlements,
        parties=parties,
    )


def dump_settlement(settlement: Settlement) -> dict:
    """Zwraca json-serializowalny słownik ``Settlement``.

    Klucze: ``name`` (str), ``population`` (int), ``occupied`` (int),
    ``active_buildings`` (lista ``dump_building``), ``storage``
    (``dump_resources``), ``capacity`` (int lub ``None``), ``garrison``
    (lista ``dump_unit``), ``owner_id`` (``str | None``).
    """
    return {
        "name": settlement.name,
        "population": settlement.population,
        "occupied": settlement.occupied,
        "active_buildings": [
            dump_building(building) for building in settlement.active_buildings
        ],
        "storage": dump_resources(settlement.storage),
        "capacity": settlement.capacity,
        "garrison": [dump_unit(unit) for unit in settlement.garrison],
        "owner_id": settlement.owner_id,
    }


def load_settlement(data: dict) -> Settlement:
    """Odtwarza ``Settlement`` ze słownika wyprodukowanego przez ``dump_settlement``."""
    return Settlement(
        name=data["name"],
        population=data["population"],
        occupied=data["occupied"],
        active_buildings=tuple(
            load_building(building) for building in data["active_buildings"]
        ),
        storage=load_resources(data["storage"]),
        capacity=data["capacity"],
        garrison=tuple(load_unit(unit) for unit in data["garrison"]),
        owner_id=data["owner_id"],
    )


def dump_duchy(duchy: Duchy) -> dict:
    """Zwraca json-serializowalny słownik ``Duchy``.

    Klucze: ``duchy_id`` (str), ``hero`` (``dump_unit`` lub ``None``),
    ``morale`` (int), ``heir`` (``dump_unit`` lub ``None``),
    ``settlements`` (lista ``dump_settlement``), ``parties`` (lista ``dump_party``).
    """
    return {
        "duchy_id": duchy.duchy_id,
        "hero": dump_unit(duchy.hero) if duchy.hero is not None else None,
        "morale": duchy.morale,
        "heir": dump_unit(duchy.heir) if duchy.heir is not None else None,
        "settlements": [dump_settlement(s) for s in duchy.settlements],
        "parties": [dump_party(p) for p in duchy.parties],
    }


def load_duchy(data: dict) -> Duchy:
    """Odtwarza ``Duchy`` ze słownika wyprodukowanego przez ``dump_duchy``."""
    return Duchy(
        duchy_id=data["duchy_id"],
        hero=load_unit(data["hero"]) if data["hero"] is not None else None,
        morale=data["morale"],
        heir=load_unit(data["heir"]) if data["heir"] is not None else None,
        settlements=tuple(load_settlement(s) for s in data["settlements"]),
        parties=tuple(load_party(p) for p in data["parties"]),
    )


def dump_session(session: Session) -> dict:
    """Zwraca json-serializowalny słownik ``Session``.

    Klucze: ``world`` (``dump_world``), ``game`` (``dump_gamestate``),
    ``calendar`` (``dump_calendar``), ``rng`` (``dump_rng``),
    ``player_duchy_id`` (``str | None``), ``seed`` (int).
    Klucza ``last_battle`` nie ma — pole jest nietrwałym stanem prezentacji.
    """
    return {
        "world": dump_world(session.world),
        "game": dump_gamestate(session.game),
        "calendar": dump_calendar(session.calendar),
        "rng": dump_rng(session.rng),
        "player_duchy_id": session.player_duchy_id,
        "seed": session.seed,
    }


def load_session(data: dict) -> Session:
    """Odtwarza ``Session`` ze słownika wyprodukowanego przez ``dump_session``.

    ``last_battle`` jest zawsze ``None`` — stan bitwy nie podlega persystencji.
    """
    return Session(
        world=load_world(data["world"]),
        game=load_gamestate(data["game"]),
        calendar=load_calendar(data["calendar"]),
        rng=load_rng(data["rng"]),
        player_duchy_id=data["player_duchy_id"],
        seed=data["seed"],
        last_battle=None,
    )


def _write_json(obj: Any, path: str | os.PathLike) -> None:
    """Wewnętrzny helper: zapis UTF-8 JSON z ``indent=2`` i pojedynczym ``\\n``.

    Nie tworzy katalogów docelowych.
    """
    with open(path, "w", encoding="utf-8") as f:
        f.write(json.dumps(obj, indent=2, ensure_ascii=False))
        f.write("\n")


def save_session(session: Session, path: str | os.PathLike) -> None:
    """Zapisuje ``dump_session(session)`` do pliku ``path`` jako UTF-8 JSON.

    Format: ``indent=2``, ``ensure_ascii=False``, zakończony pojedynczym ``\\n``.
    Nie mutuje sesji, nie tworzy katalogów docelowych.
    """
    _write_json(dump_session(session), path)


def read_session(path: str | os.PathLike) -> Session:
    """Wczytuje plik zapisany przez ``save_session`` i zwraca ``Session``."""
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return load_session(data)
