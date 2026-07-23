"""Persystencja round-trip — serializacja typów liściowych rdzenia.

Ten moduł to fundament zapisu/wczytywania stanu partii. Reużywa wyłącznie
publiczne API rdzenia, bez żadnej logiki reguł.
"""

from tbb.resources import Resources
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
