"""Tests for ``tbbbridge.persist`` (G67.1a — round-trip ``Resources``).

Tests live next to the module under test per task-324 "Ścieżki testów".
"""

import copy
import json

from tbb.resources import Resources
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
