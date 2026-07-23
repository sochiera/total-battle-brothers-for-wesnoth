"""Tests for ``tbbbridge.persist`` (G67.1a — round-trip ``Resources``,
G67.1b — round-trip ``Wound``, G67.1c — round-trip ``Unit``).

Tests live next to the module under test per task-324 "Ścieżki testów".
"""

import copy
import json

from tbb.resources import Resources
from tbb.unit import Unit
from tbb.wound import BRUISE, MAIMED, Wound
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
