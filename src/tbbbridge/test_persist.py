"""Tests for ``tbbbridge.persist`` (G67.1a — round-trip ``Resources``,
G67.1b — round-trip ``Wound``, G67.1c — round-trip ``Unit``,
G67.1e — round-trip ``Calendar``, G67.3b — round-trip ``Rng``,
G67.4a — round-trip ``Session``).

Tests live next to the module under test per task-324 "Ścieżki testów".
"""

import copy
import json

from tbb import Rng
from tbb.building import BARRACKS, FARM, MARKET, SMITH, Building
from tbb.duchy import Duchy
from tbb.party import Party
from tbb.resources import Resources
from tbb.settlement import Settlement
from tbb.turn import Calendar
from tbb.unit import Unit
from tbb.wound import BRUISE, MAIMED, Wound
from tbb.world import Region, WorldMap
from tbbbridge import persist
from tbbbridge.session import Session


def test_dump_resources_returns_json_serializable_dict_with_wheat_gold():
    """G67.1a kryt-1: ``dump_resources(Resources(3, 7))`` zwraca słownik
    z kluczami ``wheat`` i ``gold`` o wartościach ``res.wheat``/``res.gold``,
    a wynik przechodzi przez ``json.dumps``."""
    res = Resources(wheat=3, gold=7)

    dumped = persist.dump_resources(res)

    assert dumped == {"wheat": 3, "gold": 7}
    json.dumps(dumped)


def test_dump_resources_zero_values_json_serializable():
    """G67.1a kryt-1: zero-value ``Resources`` też serializuje się do JSON."""
    res = Resources(wheat=0, gold=0)

    dumped = persist.dump_resources(res)

    assert dumped == {"wheat": 0, "gold": 0}
    json.dumps(dumped)


def test_load_resources_returns_resources_from_dict_wheat_gold():
    """G67.1a kryt-2: ``load_resources({"wheat": 5, "gold": 9})`` zwraca
    ``Resources(wheat=5, gold=9)``."""
    data = {"wheat": 5, "gold": 9}

    loaded = persist.load_resources(data)

    assert loaded == Resources(wheat=5, gold=9)


def test_round_trip_load_dump_restores_resources_equality_various():
    """G67.1a kryt-2: dla każdego ``Resources r`` zachodzi
    ``load_resources(dump_resources(r)) == r`` (równość dataclass)."""
    samples = [
        Resources(wheat=0, gold=0),
        Resources(wheat=1, gold=0),
        Resources(wheat=0, gold=1),
        Resources(wheat=42, gold=99),
        Resources(wheat=1_000_000, gold=2_500_000),
    ]

    for res in samples:
        round_tripped = persist.load_resources(persist.dump_resources(res))
        assert round_tripped == res


def test_dump_resources_does_not_mutate_input_resources():
    """G67.1a kryt-3: ``dump_resources`` jest czysta — nie mutuje wejścia."""
    res = Resources(wheat=10, gold=20)
    res_before = copy.copy(res)

    persist.dump_resources(res)

    assert res == res_before


def test_load_resources_does_not_mutate_input_dict():
    """G67.1a kryt-3: ``load_resources`` jest czysta — nie mutuje słownika
    wejściowego."""
    data = {"wheat": 8, "gold": 4}
    data_before = copy.deepcopy(data)

    persist.load_resources(data)

    assert data == data_before


def test_dump_wound_returns_json_serializable_dict_with_name_accuracy_defense_duration():
    """G67.1b kryt-1: ``dump_wound(wound)`` zwraca json-serializowalny słownik z
    kluczami ``name``, ``accuracy_mod``, ``defense_mod``, ``duration_months``
    o wartościach pobranych z pól ``Wound`` (``duration_months`` może być
    ``None``); wynik przechodzi ``json.dumps``."""
    bruise = Wound(name="Bruise", accuracy_mod=-1, defense_mod=-1, duration_months=2)
    maimed = Wound(name="Maimed", accuracy_mod=-2, defense_mod=-2, duration_months=None)

    dumped_bruise = persist.dump_wound(bruise)
    dumped_maimed = persist.dump_wound(maimed)

    assert dumped_bruise == {
        "name": "Bruise",
        "accuracy_mod": -1,
        "defense_mod": -1,
        "duration_months": 2,
    }
    assert dumped_maimed == {
        "name": "Maimed",
        "accuracy_mod": -2,
        "defense_mod": -2,
        "duration_months": None,
    }
    assert json.dumps(dumped_bruise)
    assert json.dumps(dumped_maimed)


def test_round_trip_load_dump_restores_wound_equality_bruise_and_maimed():
    """G67.1b kryt-2: dla każdej rany (w tym ``BRUISE`` z ``duration_months=2``
    oraz ``MAIMED`` z ``duration_months=None``) zachodzi
    ``load_wound(dump_wound(w)) == w``."""
    samples = [
        BRUISE,
        MAIMED,
        Wound(name="Cut", accuracy_mod=-1, defense_mod=0, duration_months=1),
        Wound(name="Shatter", accuracy_mod=0, defense_mod=-3, duration_months=4),
    ]

    for wound in samples:
        round_tripped = persist.load_wound(persist.dump_wound(wound))
        assert round_tripped == wound


def test_dump_wound_does_not_mutate_input_wound():
    """G67.1b kryt-3: ``dump_wound`` jest czysta — nie mutuje wejściowego ``Wound``.

    ``Wound`` ma ``frozen=True`` (immutable), ale test weryfikuje kontrakt
    braku mutacji wejścia (idempotencja)."""
    wound = Wound(name="Bruise", accuracy_mod=-1, defense_mod=-1, duration_months=2)
    wound_before = copy.copy(wound)

    persist.dump_wound(wound)

    assert wound == wound_before


def test_load_wound_does_not_mutate_input_dict():
    """G67.1b kryt-3: ``load_wound`` jest czysta — nie mutuje słownika wejściowego."""
    data = {
        "name": "Maimed",
        "accuracy_mod": -2,
        "defense_mod": -2,
        "duration_months": None,
    }
    data_before = copy.deepcopy(data)

    persist.load_wound(data)

    assert data == data_before


def test_dump_unit_returns_json_serializable_dict_with_all_keys_and_wounds_list():
    """G67.1c kryt-1: ``dump_unit(unit)`` zwraca json-serializowalny słownik z
    kluczami ``training``, ``equipment``, ``experience``, ``ranged_range``,
    ``wounds``, ``stunned``, ``training_progress``, ``equipment_progress``;
    ``wounds`` = lista ``dump_wound(w)`` w kolejności ``unit.wounds``;
    wynik przechodzi ``json.dumps``."""
    unit = Unit(
        training=3,
        equipment=2,
        experience=5,
        ranged_range=3,
        wounds=(BRUISE, MAIMED),
        stunned=True,
        training_progress=1,
        equipment_progress=1,
    )

    dumped = persist.dump_unit(unit)

    assert dumped == {
        "training": 3,
        "equipment": 2,
        "experience": 5,
        "ranged_range": 3,
        "wounds": [persist.dump_wound(BRUISE), persist.dump_wound(MAIMED)],
        "stunned": True,
        "training_progress": 1,
        "equipment_progress": 1,
    }
    assert dumped["wounds"] == [
        persist.dump_wound(BRUISE),
        persist.dump_wound(MAIMED),
    ]
    json.dumps(dumped)


def test_round_trip_load_dump_restores_unit_equality_wounded_stunned_progress_ranged():
    """G67.1c kryt-2: dla dowolnego ``Unit u`` — w tym rannego, ogłuszonego,
    z niezerowym ``training_progress``/``equipment_progress`` i ``ranged_range >= 2``
    — zachodzi ``load_unit(dump_unit(u)) == u``.

    Próbka pokrywa naraz wszystkie filary (trening/uzbrojenie/doświadczenie),
    postęp resztkowy obu filarów, stan bojowy (rany przez ``Wound`` + ogłuszenie)
    i zasięg dystansowy — czyli wszystkiego, co musi przetrwać zapis.
    """
    unit = Unit(
        training=3,
        equipment=2,
        experience=5,
        ranged_range=3,
        wounds=(BRUISE, MAIMED),
        stunned=True,
        training_progress=1,
        equipment_progress=1,
    )

    round_tripped = persist.load_unit(persist.dump_unit(unit))

    assert round_tripped == unit
    assert round_tripped.wounds == unit.wounds
    assert isinstance(round_tripped.wounds, tuple)


def test_round_trip_load_dump_restores_building_equality_for_catalog():
    """G67.1d kryt-2: dla każdego budynku katalogu (``FARM``, ``SMITH``,
    ``MARKET``, ``BARRACKS``) zachodzi ``load_building(dump_building(b)) == b``.

    ``dump_building`` ma zwracać json-serializowalny ``dict`` z kluczami ``name``,
    ``staff``, ``output`` (gdzie ``output`` = ``dump_resources(building.output)``);
    ``load_building`` odtwarza ``Building(name=..., staff=...,
    output=load_resources(data["output"]))``. Cały katalog przechodzi round-trip z
    równością dataclass (``Building`` jest ``frozen=True``).
    """
    catalog = (FARM, SMITH, MARKET, BARRACKS)

    for building in catalog:
        dumped = persist.dump_building(building)

        assert set(dumped.keys()) == {"name", "staff", "output"}
        assert dumped["name"] == building.name
        assert dumped["staff"] == building.staff
        assert dumped["output"] == persist.dump_resources(building.output)
        json.dumps(dumped)

        round_tripped = persist.load_building(dumped)

        assert round_tripped == building


def test_dump_calendar_returns_json_serializable_dict_with_year_month():
    """G67.1e kryt-1: ``dump_calendar(calendar)`` zwraca json-serializowalny
    słownik z kluczami ``year`` i ``month`` (wartości = ``calendar.year`` /
    ``calendar.month``); wynik przechodzi ``json.dumps``."""
    calendar = Calendar(year=3, month=7)

    dumped = persist.dump_calendar(calendar)

    assert dumped == {"year": 3, "month": 7}
    json.dumps(dumped)


def test_load_calendar_returns_calendar_from_dict_year_month():
    """G67.1e kryt-2: ``load_calendar({"year": 5, "month": 9})`` zwraca
    ``Calendar(year=5, month=9)``."""
    data = {"year": 5, "month": 9}

    loaded = persist.load_calendar(data)

    assert loaded == Calendar(year=5, month=9)


def test_round_trip_load_dump_restores_calendar_equality_including_year77_month13():
    """G67.1e kryt-2: dla dowolnego ``Calendar c`` (w tym ``Calendar(year=77,
    month=13)``) zachodzi ``load_calendar(dump_calendar(c)) == c``."""
    samples = [
        Calendar(year=1, month=1),
        Calendar(year=77, month=13),
        Calendar(year=2, month=4),
        Calendar(year=999, month=13),
    ]

    for calendar in samples:
        round_tripped = persist.load_calendar(persist.dump_calendar(calendar))
        assert round_tripped == calendar


def test_dump_calendar_does_not_mutate_input_calendar():
    """G67.1e kryt-3: ``dump_calendar`` jest czysta — nie mutuje wejścia.

    ``Calendar`` ma ``frozen=True`` (immutable), ale test weryfikuje kontrakt
    braku mutacji wejścia (idempotencja)."""
    calendar = Calendar(year=3, month=7)
    calendar_before = copy.copy(calendar)

    persist.dump_calendar(calendar)

    assert calendar == calendar_before


def test_load_calendar_does_not_mutate_input_dict():
    """G67.1e kryt-3: ``load_calendar`` jest czysta — nie mutuje słownika
    wejściowego."""
    data = {"year": 4, "month": 11}
    data_before = copy.deepcopy(data)

    persist.load_calendar(data)

    assert data == data_before


def test_dump_party_returns_json_serializable_dict_with_hero_units_owner_id():
    """G67.2a kryt-1: ``dump_party(party)`` zwraca json-serializowalny ``dict``
    z kluczami ``hero`` (= ``dump_unit(party.hero)``), ``units`` (lista
    ``dump_unit(u)`` w kolejności ``party.units``) i ``owner_id``
    (= ``party.owner_id``).

    Próbka obejmuje party z podwładnymi, rannym bohaterem oraz jawny
    ``owner_id`` — wszystkie три filary kryt-1 jednocześnie.
    """
    wounded_hero = Unit(
        training=3,
        equipment=2,
        experience=5,
        ranged_range=3,
        wounds=(BRUISE,),
        stunned=True,
        training_progress=1,
        equipment_progress=1,
    )
    subordinate = Unit(training=1, equipment=0, experience=0, ranged_range=0)
    party = Party(
        hero=wounded_hero,
        units=(subordinate,),
        owner_id="player",
    )

    dumped = persist.dump_party(party)

    assert dumped == {
        "hero": persist.dump_unit(wounded_hero),
        "units": [persist.dump_unit(subordinate)],
        "owner_id": "player",
    }
    assert dumped["units"] == [persist.dump_unit(subordinate)]
    assert dumped["owner_id"] == party.owner_id
    json.dumps(dumped)


def test_round_trip_load_dump_restores_party_equality_wounded_subordinate_owner_none():
    """G67.2a kryt-2: dla dowolnej ``Party p`` (w tym z podwładnymi, rannym
    bohaterem oraz ``owner_id=None``) zachodzi
    ``load_party(dump_party(p)) == p``.

    Próbka naraz: ranny bohater (``BRUISE`` + ogłuszenie), niepusty podwładny,
    jawny ``owner_id`` oraz przypadek z ``owner_id=None`` — weryfikują, że
    ``load_party`` reużywa ``load_unit`` (hero + ``units`` jako krotka) i
    przenosi ``owner_id`` przez round-trip.
    """
    wounded_hero = Unit(
        training=3,
        equipment=2,
        experience=5,
        ranged_range=3,
        wounds=(BRUISE, MAIMED),
        stunned=True,
        training_progress=1,
        equipment_progress=1,
    )
    subordinate = Unit(training=2, equipment=1, experience=3, ranged_range=2)
    samples = [
        Party(hero=wounded_hero, units=(subordinate,), owner_id="player"),
        Party(hero=wounded_hero, units=(subordinate,), owner_id=None),
        Party(hero=wounded_hero, units=(), owner_id="player"),
        Party(hero=wounded_hero, units=(), owner_id=None),
    ]

    for party in samples:
        round_tripped = persist.load_party(persist.dump_party(party))

        assert round_tripped == party
        assert round_tripped.owner_id == party.owner_id
        assert isinstance(round_tripped.units, tuple)


def test_dump_settlement_returns_json_serializable_dict_with_all_keys():
    """G67.2b kryt-1: ``dump_settlement(settlement)`` zwraca json-serializowalny
    ``dict`` z kluczami ``name``, ``population``, ``occupied``,
    ``active_buildings`` (lista ``dump_building``), ``storage``
    (= ``dump_resources``), ``capacity`` (int lub ``None``), ``garrison``
    (lista ``dump_unit``) oraz ``owner_id``; wynik przechodzi ``json.dumps``.

    Próbka naraz: osada z niepustym garnizonem (ranny jednostka), aktywnym
    budynkiem (``FARM``), obsadą, magazynem, ``capacity`` int oraz jawny
    ``owner_id`` — wszystkie filary kryt-1 jednocześnie.
    """
    garrison_unit = Unit(
        training=3,
        equipment=2,
        experience=5,
        ranged_range=3,
        wounds=(BRUISE, MAIMED),
        stunned=True,
        training_progress=1,
        equipment_progress=1,
    )
    settlement = Settlement(
        name="Oakhaven",
        population=12,
        occupied=3,
        active_buildings=(FARM,),
        storage=Resources(wheat=7, gold=4),
        capacity=20,
        garrison=(garrison_unit,),
        owner_id="player",
    )

    dumped = persist.dump_settlement(settlement)

    assert set(dumped.keys()) == {
        "name",
        "population",
        "occupied",
        "active_buildings",
        "storage",
        "capacity",
        "garrison",
        "owner_id",
    }
    assert dumped["name"] == "Oakhaven"
    assert dumped["population"] == 12
    assert dumped["occupied"] == 3
    assert dumped["active_buildings"] == [persist.dump_building(FARM)]
    assert dumped["storage"] == persist.dump_resources(Resources(wheat=7, gold=4))
    assert dumped["capacity"] == 20
    assert dumped["garrison"] == [persist.dump_unit(garrison_unit)]
    assert dumped["owner_id"] == "player"
    json.dumps(dumped)


def test_round_trip_load_dump_restores_settlement_equality_buildings_garrison_capacity_none_owner_none():
    """G67.2b kryt-2: dla dowolnej ``Settlement s`` (w tym z budynkami,
    garnizonem, ``capacity=None`` oraz ``owner_id=None``) zachodzi
    ``load_settlement(dump_settlement(s)) == s``.

    ``load_settlement`` reużywa ``load_building``/``load_resources``/
    ``load_unit`` (``active_buildings`` i ``garrison`` jako krotki).

    Próbki naraz: osada z dwoma budynkami, rannym garnizonem, obsadą i
    magazynem; ``capacity`` int / ``None``; ``owner_id`` jawny / ``None``,
    z pustym garnizonem; puste budynki — weryfikują pełny round-trip.
    """
    garrison_unit = Unit(
        training=3,
        equipment=2,
        experience=5,
        ranged_range=3,
        wounds=(BRUISE,),
        stunned=True,
        training_progress=1,
        equipment_progress=1,
    )
    samples = [
        Settlement(
            name="Oakhaven",
            population=12,
            occupied=3,
            active_buildings=(FARM, MARKET),
            storage=Resources(wheat=7, gold=4),
            capacity=20,
            garrison=(garrison_unit,),
            owner_id="player",
        ),
        Settlement(
            name="Freehold",
            population=5,
            occupied=0,
            active_buildings=(),
            storage=Resources(wheat=0, gold=0),
            capacity=None,
            garrison=(),
            owner_id=None,
        ),
        Settlement(
            name="Rivermouth",
            population=8,
            occupied=1,
            active_buildings=(SMITH,),
            storage=Resources(wheat=2, gold=9),
            capacity=10,
            garrison=(Unit(),),
            owner_id=None,
        ),
    ]

    for settlement in samples:
        round_tripped = persist.load_settlement(
            persist.dump_settlement(settlement)
        )

        assert round_tripped == settlement
        assert isinstance(round_tripped.active_buildings, tuple)
        assert isinstance(round_tripped.garrison, tuple)
        assert round_tripped.owner_id == settlement.owner_id
        assert round_tripped.capacity == settlement.capacity


def test_dump_and_load_settlement_do_not_mutate_input():
    """G67.2b kryt-3: ``dump_settlement`` i ``load_settlement`` są czyste —
    nie mutują wejścia (ani obiektu ``Settlement``, ani słownika danych).

    ``Settlement`` jest ``frozen=True`` (immutable), ale test weryfikuje kontrakt
    braku mutacji wejścia (idempotencja), wzorem par liściowych
    (``dump_wound``/``load_wound``, ``dump_calendar``/``load_calendar``).
    """
    garrison_unit = Unit(
        training=3,
        equipment=2,
        experience=5,
        ranged_range=3,
        wounds=(BRUISE,),
        stunned=True,
        training_progress=1,
        equipment_progress=1,
    )
    settlement = Settlement(
        name="Oakhaven",
        population=12,
        occupied=3,
        active_buildings=(FARM, SMITH),
        storage=Resources(wheat=7, gold=4),
        capacity=20,
        garrison=(garrison_unit,),
        owner_id="player",
    )
    settlement_before = copy.copy(settlement)

    dumped = persist.dump_settlement(settlement)

    assert settlement == settlement_before
    data_before = copy.deepcopy(dumped)

    persist.load_settlement(dumped)

    assert dumped == data_before


def test_dump_region_returns_json_serializable_dict_with_name():
    """G67.2c kryt-1: ``dump_region(region)`` zwraca json-serializowalny
    ``dict`` z kluczem ``name`` (= ``region.name``); wynik przechodzi
    ``json.dumps``."""
    region = Region(name="Oakhaven")

    dumped = persist.dump_region(region)

    assert dumped == {"name": "Oakhaven"}
    json.dumps(dumped)


def test_load_region_returns_region_from_dict_name():
    """G67.2c kryt-2: ``load_region({"name": "Rivermouth"})`` zwraca
    ``Region(name="Rivermouth")``."""
    data = {"name": "Rivermouth"}

    loaded = persist.load_region(data)

    assert loaded == Region(name="Rivermouth")


def test_round_trip_load_dump_restores_region_equality_various():
    """G67.2c kryt-2: dla dowolnego ``Region r`` zachodzi
    ``load_region(dump_region(r)) == r`` (równość dataclass)."""
    samples = [
        Region(name="Oakhaven"),
        Region(name="Rivermouth"),
        Region(name=""),
        Region(name="Freehold"),
    ]

    for region in samples:
        round_tripped = persist.load_region(persist.dump_region(region))
        assert round_tripped == region


def test_dump_and_load_region_do_not_mutate_input():
    """G67.2c kryt-3: ``dump_region`` i ``load_region`` są czyste — nie mutują
    wejścia (ani ``Region``, ani słownika danych).

    ``Region`` ma ``frozen=True`` (immutable), ale test weryfikuje kontrakt
    braku mutacji wejścia (idempotencja), wzorem par liściowych
    (``dump_wound``/``load_wound``, ``dump_calendar``/``load_calendar``,
    ``dump_and_load_settlement``).
    """
    region = Region(name="Oakhaven")
    region_before = copy.copy(region)

    dumped = persist.dump_region(region)

    assert region == region_before
    data_before = copy.deepcopy(dumped)

    persist.load_region(dumped)

    assert dumped == data_before


def _sample_world_with_settlement_and_party():
    """Zbuduj ``WorldMap`` z regionami, połączeniami, osadą i party — pełny
    kompozyt do testów persystencji świata."""
    regions = (
        Region(name="Oakhaven"),
        Region(name="Rivermouth"),
        Region(name="Freehold"),
        Region(name="Stagford"),
    )
    connections = (
        (regions[0], regions[1]),
        (regions[1], regions[2]),
        (regions[2], regions[3]),
    )
    settlement = Settlement(
        name="Oakhaven",
        population=12,
        occupied=3,
        active_buildings=(FARM, SMITH),
        storage=Resources(wheat=7, gold=4),
        capacity=20,
        garrison=(
            Unit(
                training=3,
                equipment=2,
                experience=5,
                ranged_range=3,
                wounds=(BRUISE,),
                stunned=True,
                training_progress=1,
                equipment_progress=1,
            ),
        ),
        owner_id="player",
    )
    party = Party(
        hero=Unit(
            training=2,
            equipment=1,
            experience=3,
            ranged_range=2,
            wounds=(MAIMED,),
            stunned=False,
        ),
        units=(Unit(training=1, equipment=0, experience=0, ranged_range=0),),
        owner_id="ai",
    )
    world = WorldMap(
        regions,
        connections,
        settlements={regions[0]: settlement},
        parties={regions[2]: party},
    )
    return world, regions


def test_round_trip_load_world_restores_world_equality_and_region_identity():
    """G67.2d kryt-1/2: ``dump_world(world)`` zwraca json-serializowalny ``dict``
    z kluczami ``regions`` (lista ``dump_region`` w kolejności ``world.regions``),
    ``connections`` (lista par ``[i, j]`` — indeksy w liście ``regions``),
    ``settlements`` i ``parties`` (listy par ``[i, dump_settlement(s)]`` /
    ``[i, dump_party(p)]`` po indeksie regionu); ``load_world(dump_world(w))``
    odtwarza ``WorldMap`` reużywając ``load_region``/``load_settlement``/
    ``load_party``; połączenia i mapowania osad/party wiążą się z tymi samymi
    obiektami ``Region`` z odtworzonej listy regionów (po indeksie); dla dowolnej
    ``WorldMap w`` zachodzi ``load_world(dump_world(w)) == w``.

    Próbka naraz: 4 regiony, 3 połączenia, osada z garnizonem/budynkami
    w regionie 0, party z rannym bohaterem i podwładnym w regionie 2.
    Weryfikuje: (a) strukturę dump (klucze, kolejność regionów, indeksy
    połączeń i par osad/party), (b) ``json.dumps``, (c) round-trip
    ``load_world(...) == world``, oraz (d) identyczność regionów (a nie tylko
    równość ``name``) w połączeniach i kluczach mapowań — spoiwo indeksów ma
    sens tylko wtedy, gdy odtworzone obiekty ``Region`` są tymi samymi
    referencjami w odtworzonym świecie.
    """
    world, regions = _sample_world_with_settlement_and_party()
    settlement = world.settlements[regions[0]]
    party = world.parties[regions[2]]

    dumped = persist.dump_world(world)

    assert set(dumped.keys()) == {"regions", "connections", "settlements", "parties"}
    assert dumped["regions"] == [persist.dump_region(r) for r in world.regions]
    assert dumped["connections"] == [[0, 1], [1, 2], [2, 3]]
    assert dumped["settlements"] == [[0, persist.dump_settlement(settlement)]]
    assert dumped["parties"] == [[2, persist.dump_party(party)]]
    json.dumps(dumped)

    round_tripped = persist.load_world(dumped)

    assert round_tripped == world
    assert round_tripped.regions == world.regions

    restored_regions = round_tripped.regions
    for first, second in round_tripped.connections:
        assert first in restored_regions
        assert second in restored_regions
        assert first is not regions[0]
        assert second is not regions[0]
    for settlement_region in round_tripped.settlements:
        assert settlement_region in restored_regions
        assert settlement_region is not regions[0]
    for party_region in round_tripped.parties:
        assert party_region in restored_regions
        assert party_region is not regions[2]

    assert round_tripped.settlements[restored_regions[0]] == settlement
    assert round_tripped.parties[restored_regions[2]] == party


def test_dump_and_load_world_do_not_mutate_input():
    """G67.2d kryt-3: ``dump_world`` i ``load_world`` są czyste — nie mutują
    wejścia (ani ``WorldMap``, ani słownika danych).

    Wzorem par liściowych (``dump_and_load_settlement``,
    ``dump_and_load_region``) weryfikuje kontrakt braku mutacji wejścia
    (idempotencja). ``WorldMap`` oraz ``Region`` są ``frozen=True``, ale test
    chroni przed regresją, gdyby freeze został kiedyś zdjęty lub gdyby mutowano
    kolekcje wewnątrz ``WorldMap``.

    ``WorldMap`` trzyma ``MappingProxyType``, którego nie da się
    ``copy.deepcopy`` (nie jest picklowalny), więc snapshot wejścia budujemy
    ręcznie jako krotkę pól publicznych i porównujemy wartość po wywołaniu
    ``dump_world``/``load_world``.
    """
    world, _regions = _sample_world_with_settlement_and_party()

    def _snapshot():
        return (
            world.regions,
            world.connections,
            tuple(world.settlements.items()),
            tuple(world.parties.items()),
        )

    snapshot_before = _snapshot()

    dumped = persist.dump_world(world)

    assert _snapshot() == snapshot_before
    data_before = copy.deepcopy(dumped)

    persist.load_world(dumped)

    assert _snapshot() == snapshot_before
    assert dumped == data_before


def _sample_duchies():
    """Zbuduj listę ``Duchy`` pokrywających warianty opcjonalnych pól
    (``hero``/``heir`` = ``None`` oraz osady/drużyny) dla testów persystencji."""
    hero = Unit(
        training=3,
        equipment=2,
        experience=5,
        ranged_range=3,
        wounds=(BRUISE, MAIMED),
        stunned=True,
        training_progress=1,
        equipment_progress=1,
    )
    heir = Unit(
        training=2,
        equipment=1,
        experience=3,
        ranged_range=2,
        wounds=(MAIMED,),
    )
    settlement = Settlement(
        name="Oakhaven",
        population=12,
        occupied=3,
        active_buildings=(FARM, SMITH),
        storage=Resources(wheat=7, gold=4),
        capacity=20,
        garrison=(
            Unit(
                training=1,
                equipment=0,
                experience=0,
                ranged_range=0,
                wounds=(BRUISE,),
            ),
        ),
        owner_id="player",
    )
    party = Party(
        hero=Unit(
            training=2,
            equipment=1,
            experience=3,
            ranged_range=2,
        ),
        units=(Unit(training=1, equipment=0, experience=0, ranged_range=0),),
        owner_id="player",
    )
    return [
        Duchy(
            duchy_id="player",
            hero=hero,
            morale=7,
            heir=heir,
            settlements=(settlement,),
            parties=(party,),
        ),
        Duchy(
            duchy_id="ai",
            hero=Unit(training=1, equipment=0, experience=0, ranged_range=0),
            morale=3,
            heir=None,
            settlements=(),
            parties=(),
        ),
        Duchy(
            duchy_id="bandits",
            hero=None,
            morale=0,
            heir=None,
            settlements=(),
            parties=(),
        ),
    ]


def test_dump_duchy_returns_json_serializable_dict_with_all_keys_hero_heir_none():
    """G67.2e kryt-1: ``dump_duchy(duchy)`` zwraca json-serializowalny ``dict``
    z kluczami ``duchy_id``, ``hero`` (= ``dump_unit`` lub ``None``), ``morale``,
    ``heir`` (= ``dump_unit`` lub ``None``), ``settlements`` (lista
    ``dump_settlement``) oraz ``parties`` (lista ``dump_party``); wynik przechodzi
    ``json.dumps``.

    Próbka naraz: księstwo z bohaterem, dziedzicem, osadą i drużyną (wszystkie
    filary) oraz przypadek z ``hero=None``/``heir=None`` (opcjonalne pola jako
    ``None``) — weryfikują strukturę dump w obu wariantach.
    """
    duchy_full, _duchy_hero_only, duchy_empty = _sample_duchies()

    dumped_full = persist.dump_duchy(duchy_full)
    dumped_empty = persist.dump_duchy(duchy_empty)

    assert set(dumped_full.keys()) == {
        "duchy_id",
        "hero",
        "morale",
        "heir",
        "settlements",
        "parties",
    }
    assert dumped_full["duchy_id"] == duchy_full.duchy_id
    assert dumped_full["hero"] == persist.dump_unit(duchy_full.hero)
    assert dumped_full["morale"] == duchy_full.morale
    assert dumped_full["heir"] == persist.dump_unit(duchy_full.heir)
    assert dumped_full["settlements"] == [
        persist.dump_settlement(s) for s in duchy_full.settlements
    ]
    assert dumped_full["parties"] == [
        persist.dump_party(p) for p in duchy_full.parties
    ]
    assert json.dumps(dumped_full)

    assert dumped_empty["duchy_id"] == duchy_empty.duchy_id
    assert dumped_empty["hero"] is None
    assert dumped_empty["morale"] == duchy_empty.morale
    assert dumped_empty["heir"] is None
    assert dumped_empty["settlements"] == []
    assert dumped_empty["parties"] == []
    assert json.dumps(dumped_empty)


def test_round_trip_load_dump_restores_duchy_equality_hero_none_heir_settlements_parties():
    """G67.2e kryt-2: dla dowolnego ``Duchy d`` (w tym z ``hero=None``,
    ``heir=None``, osadami i drużynami) zachodzi
    ``load_duchy(dump_duchy(d)) == d``.

    ``load_duchy`` reużywa ``load_unit``/``load_settlement``/``load_party``
    (``hero``/``heir`` = ``load_unit`` lub ``None``; ``settlements``/``parties``
    jako krotki). Próbki naraz: bohater+dziedzic+osada+drużyna, bohater bez
    dziedzica, oraz ``hero=None``/``heir=None`` (puste osady/drużyny) — weryfikują
    pełny round-trip w obu wariantach opcjonalnych pól.
    """
    samples = _sample_duchies()

    for duchy in samples:
        round_tripped = persist.load_duchy(persist.dump_duchy(duchy))

        assert round_tripped == duchy
        assert isinstance(round_tripped.settlements, tuple)
        assert isinstance(round_tripped.parties, tuple)
        assert round_tripped.hero == duchy.hero
        assert round_tripped.heir == duchy.heir


def test_dump_and_load_duchy_do_not_mutate_input():
    """G67.2e kryt-3: ``dump_duchy`` i ``load_duchy`` są czyste — nie mutują
    wejścia (ani ``Duchy``, ani słownika danych).

    Wzorem par liściowych weryfikuje kontrakt braku mutacji wejścia (idempotencja).
    ``Duchy`` jest ``frozen=True``, ale test chroni przed regresją, gdyby freeze
    został kiedyś zdjęty lub gdyby mutowano kolekcje wewnątrz ``Duchy``.
    """
    duchy = _sample_duchies()[0]
    duchy_before = copy.copy(duchy)

    dumped = persist.dump_duchy(duchy)

    assert duchy == duchy_before
    data_before = copy.deepcopy(dumped)

    persist.load_duchy(dumped)

    assert dumped == data_before


def test_load_duchy_reuses_load_unit_load_settlement_load_party():
    """G67.2e kryt-2: ``load_duchy`` reużywa ``load_unit``/``load_settlement``/
    ``load_party`` —round-trip odtwarza równość na poziomie komponentów,
    a nie tylko dataclass ``Duchy``. Osada i drużyna z round-trip musi być
    równa oryginałowi, co jest możliwe tylko wtedy, gdy ``load_duchy`` deleguje
    do ``load_settlement``/``load_party`` (a te do ``load_unit``).
    """
    sample = _sample_duchies()[0]

    round_tripped = persist.load_duchy(persist.dump_duchy(sample))

    assert round_tripped.settlements[0] == sample.settlements[0]
    assert round_tripped.parties[0] == sample.parties[0]
    assert round_tripped.hero == sample.hero


def test_dump_gamestate_returns_json_serializable_dict_with_duchies_key_in_order():
    """G67.2f kryt-1: ``dump_gamestate(game)`` zwraca json-serializowalny
    ``dict`` z pojedynczym kluczem ``duchies`` (lista ``dump_duchy(d)`` w
    kolejności ``game.duchies``); wynik przechodzi ``json.dumps``.

    Próbka naraz: ``GameState`` z wieloma księstwami (pełne z osadą/drużyną,
    bez dziedzica oraz księstwo bez bohatera) — weryfikuje, że dump ma tylko
    klucz ``duchies``, kolejność listy odpowiada ``game.duchies``, a każdy
    element to dokładnie ``dump_duchy`` odpowiedniego księstwa.
    """
    from tbb.game import GameState

    duchies = _sample_duchies()
    game = GameState(tuple(duchies))

    dumped = persist.dump_gamestate(game)

    assert set(dumped.keys()) == {"duchies"}
    assert dumped["duchies"] == [persist.dump_duchy(d) for d in game.duchies]
    assert [entry["duchy_id"] for entry in dumped["duchies"]] == [
        d.duchy_id for d in game.duchies
    ]
    json.dumps(dumped)


def test_round_trip_load_dump_restores_gamestate_equality_multiple_duchies_hero_none_settlements_parties():
    """G67.2f kryt-2: dla dowolnego ``GameState g`` (w tym z wieloma księstwami,
    księstwem bez bohatera i księstwem z osadami/drużynami) zachodzi
    ``load_gamestate(dump_gamestate(g)) == g``.

    ``load_gamestate`` reużywa ``load_duchy`` (``duchies`` jako krotka). Próbki
    naraz: pełne księstwo z bohaterem+dziedzicem+osadą+drużyną, księstwo z
    bohaterem bez dziedzica, oraz ``hero=None`` (puste osady/drużyny), oraz
    jednoksięstwowy ``GameState`` — weryfikują pełny round-trip ``GameState``.
    """
    from tbb.game import GameState

    samples = [
        GameState(tuple(_sample_duchies())),
        GameState(tuple(_sample_duchies()[:1])),
        GameState(tuple(_sample_duchies()[1:])),
    ]

    for game in samples:
        round_tripped = persist.load_gamestate(persist.dump_gamestate(game))

        assert round_tripped == game
        assert isinstance(round_tripped.duchies, tuple)
        assert round_tripped.duchies == game.duchies


def test_dump_and_load_gamestate_do_not_mutate_input():
    """G67.2f kryt-3: ``dump_gamestate`` i ``load_gamestate`` są czyste — nie
    mutują wejścia (ani ``GameState``, ani słownika danych).

    ``GameState`` jest immutable (``frozen=True``), ale test weryfikuje kontrakt
    braku mutacji wejścia (idempotencja), wzorem par liściowych
    (``dump_duchy``/``load_duchy``, ``dump_and_load_duchy``).
    """
    from tbb.game import GameState

    game = GameState(tuple(_sample_duchies()))
    duchies_before = game.duchies

    dumped = persist.dump_gamestate(game)

    assert game.duchies == duchies_before
    data_before = copy.deepcopy(dumped)

    persist.load_gamestate(dumped)

    assert game.duchies == duchies_before
    assert dumped == data_before


def test_dump_rng_returns_json_serializable_dict_with_state_key():
    """G67.3b kryt-1: ``dump_rng(rng)`` zwraca json-serializowalny ``dict`` z
    kluczem ``state`` (wartość = ``rng.state()`` z krotkami zamienionymi na listy);
    wynik przechodzi ``json.dumps``.
    """
    rng = Rng(7)
    for _ in range(5):
        rng.randint(1, 100)

    dumped = persist.dump_rng(rng)

    assert "state" in dumped
    assert isinstance(dumped["state"], (list, tuple))
    json.dumps(dumped)


def test_round_trip_load_dump_rng_restores_rng_sequence_via_json_round_trip():
    """G67.3b kryt-2: dla ``r = Rng(7)`` po dowolnej liczbie rzutów,
    ``load_rng(dump_rng(r))`` produkuje tę samą kolejną sekwencję
    ``randint(1, 100)`` co dalsze rzuty ``r``; round-trip przez
    ``json.loads(json.dumps(...))`` zachowuje sekwencję.
    """
    r = Rng(7)
    for _ in range(5):
        r.randint(1, 100)

    dumped = persist.dump_rng(r)
    json_round_tripped = json.loads(json.dumps(dumped))
    restored = persist.load_rng(json_round_tripped)

    expected = [r.randint(1, 100) for _ in range(10)]
    actual = [restored.randint(1, 100) for _ in range(10)]

    assert actual == expected


def test_dump_rng_does_not_mutate_input_rng():
    """G67.3b kryt-3: ``dump_rng`` jest czysta — nie mutuje wejściowego ``Rng``.

    ``Rng`` nie jest ``frozen``, ale test weryfikuje kontrakt braku mutacji
    wejścia (idempotencja state) — stan przed i po wywołaniu musi być
    identyczny, a dalsze rzuty dają tę samą sekwencję.
    """
    rng = Rng(13)
    for _ in range(3):
        rng.randint(1, 100)

    state_before = rng.state()
    expected_continuation = [rng.randint(1, 100) for _ in range(5)]

    rng_after_dump = Rng.from_state(state_before)
    persist.dump_rng(rng_after_dump)

    state_after = rng_after_dump.state()
    actual_continuation = [rng_after_dump.randint(1, 100) for _ in range(5)]

    assert state_after == state_before
    assert actual_continuation == expected_continuation


def test_load_rng_does_not_mutate_input_dict():
    """G67.3b kryt-3: ``load_rng`` jest czysta — nie mutuje słownika
    wejściowego.
    """
    r = Rng(7)
    for _ in range(3):
        r.randint(1, 100)

    data = persist.dump_rng(r)
    data_before = copy.deepcopy(data)

    persist.load_rng(data)

    assert data == data_before


def test_dump_session_returns_json_serializable_dict_with_keys_world_game_calendar_rng_player_duchy_id_seed_no_last_battle():
    """G67.4a kryt-1: ``dump_session(session)`` zwraca json-serializowalny
    ``dict`` z kluczami ``world`` (= ``dump_world``), ``game`` (= ``dump_gamestate``),
    ``calendar`` (= ``dump_calendar``), ``rng`` (= ``dump_rng``), ``player_duchy_id``
    (``str | None``) oraz ``seed`` (int); klucza ``last_battle`` **brak**; wynik
    przechodzi ``json.dumps``.
    """
    from tbb.game import GameState

    session = Session(
        world=_sample_world_with_settlement_and_party()[0],
        game=GameState(tuple(_sample_duchies())),
        calendar=Calendar(year=5, month=8),
        rng=Rng(42),
        player_duchy_id="player",
        seed=42,
        last_battle=None,
    )

    dumped = persist.dump_session(session)

    assert set(dumped.keys()) == {
        "world",
        "game",
        "calendar",
        "rng",
        "player_duchy_id",
        "seed",
    }
    assert "last_battle" not in dumped
    assert dumped["world"] == persist.dump_world(session.world)
    assert dumped["game"] == persist.dump_gamestate(session.game)
    assert dumped["calendar"] == persist.dump_calendar(session.calendar)
    assert dumped["rng"] == persist.dump_rng(session.rng)
    assert dumped["player_duchy_id"] == "player"
    assert dumped["seed"] == 42
    json.dumps(dumped)


def test_dump_session_with_last_battle_omits_last_battle_key():
    """G67.4a kryt-1: ``dump_session`` dla sesji z ``last_battle`` ustawionym
    również pomija klucz ``last_battle`` — pole jest nietrwałe.
    """
    from tbb.battle import BattleSide, HexBattle, Hex
    from tbb.game import GameState
    from tbb.terrain import PLAINS

    session = Session(
        world=_sample_world_with_settlement_and_party()[0],
        game=GameState(tuple(_sample_duchies()[:1])),
        calendar=Calendar(),
        rng=Rng(7),
        player_duchy_id="player",
        seed=7,
        last_battle=HexBattle(
            battlefield={Hex(0, 0): PLAINS},
            units={Hex(0, 0): Unit()},
            sides={Hex(0, 0): BattleSide.ATTACKER},
        ),
    )

    dumped = persist.dump_session(session)

    assert "last_battle" not in dumped
    json.dumps(dumped)


def test_round_trip_load_dump_session_restores_session_equality_and_rng_sequence():
    """G67.4a kryt-2: dla ``s = new_session()`` po round-tripie
    ``r = load_session(dump_session(s))`` zachodzi ``r.world == s.world``,
    ``r.game == s.game``, ``r.calendar == s.calendar``, ``r.player_duchy_id ==
    s.player_duchy_id``, ``r.seed == s.seed``, ``r.last_battle is None``, a
    ``r.rng`` produkuje tę samą sekwencję ``randint(1, 100)`` co ``s.rng``.
    """
    from tbbbridge.session import new_session

    s = new_session(seed=73, player_duchy_id="player")
    orig_rng_sequence = [s.rng.randint(1, 100) for _ in range(10)]

    dumped = persist.dump_session(s)
    expected_continuation = [s.rng.randint(1, 100) for _ in range(10)]
    r = persist.load_session(dumped)

    assert r.world == s.world
    assert r.game == s.game
    assert r.calendar == s.calendar
    assert r.player_duchy_id == s.player_duchy_id
    assert r.seed == s.seed
    assert r.last_battle is None
    restored_rng_sequence = [r.rng.randint(1, 100) for _ in range(10)]
    assert restored_rng_sequence == expected_continuation


def test_round_trip_load_dump_session_with_last_battle_restores_with_last_battle_none():
    """G67.4a kryt-3: Round-trip działa też dla sesji z ustawionym
    ``last_battle`` (pole jest po prostu pomijane, wynik ``load_session`` ma
    ``last_battle=None``).
    """
    from tbb.battle import BattleSide, HexBattle, Hex
    from tbb.terrain import PLAINS
    from tbbbridge.session import new_session

    s = new_session(seed=73, player_duchy_id="player")
    dummy_battle = HexBattle(
        battlefield={Hex(0, 0): PLAINS},
        units={Hex(0, 0): Unit()},
        sides={Hex(0, 0): BattleSide.ATTACKER},
    )
    s.last_battle = dummy_battle

    dumped = persist.dump_session(s)
    r = persist.load_session(dumped)

    assert r.last_battle is None
    assert r.world == s.world
    assert r.game == s.game
    assert r.calendar == s.calendar
    assert r.player_duchy_id == s.player_duchy_id
    assert r.seed == s.seed


def test_dump_session_does_not_mutate_input_session():
    """G67.4a kryt-3: ``dump_session`` jest czysta — nie mutuje wejściowej
    sesji.
    """
    from tbbbridge.session import new_session

    s = new_session(seed=73, player_duchy_id="player")
    orig_world = s.world
    orig_game = s.game
    orig_calendar = s.calendar
    orig_rng_state = s.rng.state()
    orig_last_battle = s.last_battle

    dumped = persist.dump_session(s)

    assert s.world is orig_world
    assert s.game is orig_game
    assert s.calendar is orig_calendar
    assert s.rng.state() == orig_rng_state
    assert s.last_battle is orig_last_battle
    json.dumps(dumped)


def test_load_session_does_not_mutate_input_dict():
    """G67.4a kryt-3: ``load_session`` jest czysta — nie mutuje słownika
    wejściowego.
    """
    from tbbbridge.session import new_session

    s = new_session(seed=73, player_duchy_id="player")
    data = persist.dump_session(s)
    data_before = copy.deepcopy(data)

    persist.load_session(data)

    assert data == data_before


def test_save_session_writes_json_indented_utf8_with_trailing_newline(tmp_path):
    """G68.1a kryt-1: ``save_session(session, path)`` zapisuje plik JSON z
    ``indent=2``, ``ensure_ascii=False``, zakończony pojedynczym ``\\n``,
    kodowanie UTF-8; nie mutuje sesji; dwa wywołania dają bajt-w-bajt
    identyczny plik.
    """
    import os
    from tbbbridge.session import new_session

    s = new_session(seed=73, player_duchy_id="player")
    path = tmp_path / "session.json"

    persist.save_session(s, path)

    assert path.exists()
    content = path.read_text(encoding="utf-8")
    assert content.endswith("\n")
    assert not content.endswith("\n\n")
    loaded = json.loads(content)
    assert json.dumps(loaded, indent=2, ensure_ascii=False) + "\n" == content
    path.unlink()

    persist.save_session(s, path)
    content2 = path.read_text(encoding="utf-8")
    assert content == content2


def test_read_session_roundtrip_restores_world_game_calendar_player_duchy_id_seed_rng_sequence(tmp_path):
    """G68.1a kryt-2: ``read_session(path)`` wczytuje plik zapisany przez
    ``save_session`` i zwraca ``Session`` (``load_session(json.load(...))``);
    dla ``s = new_session()`` po ``save_session(s, tmp)`` sesja
    ``r = read_session(tmp)`` spełnia ``r.world == s.world``,
    ``r.game == s.game``, ``r.calendar == s.calendar``,
    ``r.player_duchy_id == s.player_duchy_id``, ``r.seed == s.seed``,
    ``r.last_battle is None``, a ``r.rng`` produkuje tę samą sekwencję
    ``randint(1, 100)`` co ``s.rng``.
    """
    from tbbbridge.session import new_session

    s = new_session(seed=73, player_duchy_id="player")
    path = tmp_path / "session.json"

    persist.save_session(s, path)
    r = persist.read_session(path)

    assert r.world == s.world
    assert r.game == s.game
    assert r.calendar == s.calendar
    assert r.player_duchy_id == s.player_duchy_id
    assert r.seed == s.seed
    assert r.last_battle is None

    expected_rng_sequence = [s.rng.randint(1, 100) for _ in range(10)]
    actual_rng_sequence = [r.rng.randint(1, 100) for _ in range(10)]
    assert actual_rng_sequence == expected_rng_sequence
