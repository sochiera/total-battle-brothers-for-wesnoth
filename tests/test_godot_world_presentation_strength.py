"""task-625 G113.1a: WorldPresentation renders party/settlement strength as Polish text."""

from __future__ import annotations

import json
import re
from pathlib import Path

from godot_runner import run_godot_script

ROOT = Path(__file__).resolve().parents[1]
GAME = ROOT / "game"
PROBE = GAME / "tests" / "world_presentation_strength_probe.gd"
PREFIX = "WORLD_PRESENTATION_STRENGTH "

OWNER_PLAYER_RE = re.compile(r"gracz|własn", re.IGNORECASE)
OWNER_AI_RE = re.compile(r"\bai\b|wr[oó]g", re.IGNORECASE)


def _has_digit(text: str) -> bool:
    return any(char.isdigit() for char in text)


def _load_texts() -> dict:
    assert PROBE.is_file(), "missing res://tests/world_presentation_strength_probe.gd"

    result = run_godot_script(
        GAME, "res://tests/world_presentation_strength_probe.gd", timeout=30
    )

    assert result.returncode == 0, result.stderr
    assert "SCRIPT ERROR" not in result.stderr, result.stderr
    lines = [line for line in result.stdout.splitlines() if line.startswith(PREFIX)]
    assert len(lines) == 1, result.stdout
    return json.loads(lines[0][len(PREFIX) :])


def test_party_strength_text_reports_side_size_and_hp():
    texts = _load_texts()["party"]

    full = texts["player_full"]
    assert OWNER_PLAYER_RE.search(full), full
    assert "5" in full, full
    assert "73" in full, full


def test_party_strength_text_uses_singular_form_for_one_unit():
    texts = _load_texts()["party"]

    singular = texts["ai_singular"]
    assert OWNER_AI_RE.search(singular), singular
    assert re.search(r"1\s*jednostk[ai]\b", singular), singular
    assert not re.search(r"1\s*jednostek\b", singular), singular


def test_party_strength_text_falls_back_to_no_army_without_fabricating_numbers():
    texts = _load_texts()["party"]

    for case_name in ("missing", "non_dict", "empty_owner"):
        text = texts[case_name]
        assert text == "brak armii", f"{case_name}: {text!r}"


def test_party_strength_text_omits_size_and_hp_when_not_numeric():
    texts = _load_texts()["party"]

    for case_name in ("missing_size", "non_numeric_size"):
        text = texts[case_name]
        assert OWNER_PLAYER_RE.search(text), f"{case_name}: {text!r}"
        assert "0" not in text, f"{case_name}: {text!r}"


def test_settlement_strength_text_reports_name_and_garrison_including_zero():
    texts = _load_texts()["settlement"]

    zero_garrison = texts["keep_garrison_zero"]
    assert "Twierdza gracza" in zero_garrison, zero_garrison
    assert "0" in zero_garrison, zero_garrison

    five_garrison = texts["outpost_garrison_five"]
    assert "Posterunek gracza" in five_garrison, five_garrison
    assert "5" in five_garrison, five_garrison


def test_settlement_strength_text_falls_back_without_fabricating_garrison():
    texts = _load_texts()["settlement"]

    assert texts["missing"] == "brak osady", texts["missing"]

    missing_garrison = texts["missing_garrison"]
    assert "Twierdza wroga" in missing_garrison, missing_garrison
    assert not _has_digit(missing_garrison), missing_garrison

    non_numeric_garrison = texts["non_numeric_garrison"]
    assert "Posterunek wroga" in non_numeric_garrison, non_numeric_garrison
    assert not _has_digit(non_numeric_garrison), non_numeric_garrison


def test_settlement_strength_text_reports_free_population_alongside_garrison():
    texts = _load_texts()["settlement"]

    # G114.1c (task-637) AC3: wiersz osady dokłada wolną ludność obok garnizonu
    # z K113. Zero jest realną wartością (jak garnizon: 0), więc go nie trać.
    zero_free = texts["keep_garrison_zero_free_zero"]
    assert "Twierdza gracza" in zero_free, zero_free
    assert "garnizon: 0" in zero_free, zero_free
    assert "wolni mieszkańcy: 0" in zero_free, zero_free

    three_free = texts["outpost_garrison_five_free_three"]
    assert "Posterunek gracza" in three_free, three_free
    assert "garnizon: 5" in three_free, three_free
    assert "wolni mieszkańcy: 3" in three_free, three_free


def test_settlement_strength_text_omits_free_population_without_fabricating_zero():
    texts = _load_texts()["settlement"]

    # G114.1c (task-637) AC4: brakujące/nieliczbowe ``free`` → dotychczasowy
    # tekst zastępczy BEZ „0" wziętego z powietrza (symetrycznie do garnizonu).
    missing_free = texts["keep_garrison_two_missing_free"]
    assert "Twierdza wroga" in missing_free, missing_free
    assert "garnizon: 2" in missing_free, missing_free
    assert "wolni" not in missing_free.lower(), missing_free

    non_numeric_free = texts["keep_garrison_two_non_numeric_free"]
    assert "Posterunek wroga" in non_numeric_free, non_numeric_free
    assert "garnizon: 2" in non_numeric_free, non_numeric_free
    assert "wolni" not in non_numeric_free.lower(), non_numeric_free
