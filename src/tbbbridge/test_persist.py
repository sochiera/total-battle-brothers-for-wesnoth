"""Tests for ``tbbbridge.persist`` (G67.1a — round-trip ``Resources``,
G67.1b — round-trip ``Wound``, G67.1c — round-trip ``Unit``,
G67.1e — round-trip ``Calendar``).

Tests live next to the module under test per task-324 "Ścieżki testów".
"""

import copy
import json

from tbb.building import BARRACKS, FARM, MARKET, SMITH, Building
from tbb.party import Party
from tbb.resources import Resources
from tbb.settlement import Settlement
from tbb.turn import Calendar
from tbb.unit import Unit
from tbb.wound import BRUISE, MAIMED, Wound
from tbb.world import Region, WorldMap
from tbbbridge import persist


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
