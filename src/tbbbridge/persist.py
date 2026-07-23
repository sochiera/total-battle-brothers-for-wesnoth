"""Persystencja round-trip — serializacja typów liściowych rdzenia.

Ten moduł to fundament zapisu/wczytywania stanu partii. Reużywa wyłącznie
publiczne API rdzenia, bez żadnej logiki reguł.
"""

from tbb.resources import Resources
from tbb.unit import Unit
from tbb.wound import Wound


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
