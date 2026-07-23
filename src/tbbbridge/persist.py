"""Persystencja round-trip — serializacja typów liściowych rdzenia.

Ten moduł to fundament zapisu/wczytywania stanu partii. Reużywa wyłącznie
publiczne API rdzenia, bez żadnej logiki reguł.
"""

from tbb.resources import Resources


def dump_resources(res: Resources) -> dict:
    """Zwraca json-serializowalny słownik ``{"wheat": int, "gold": int}``."""
    return {"wheat": res.wheat, "gold": res.gold}


def load_resources(data: dict) -> Resources:
    """Odtwarza ``Resources`` ze słownika wyprodukowanego przez ``dump_resources``."""
    return Resources(wheat=data["wheat"], gold=data["gold"])
