from pathlib import Path

from godot_runner import run_godot_script

ROOT = Path(__file__).resolve().parents[1]
GAME = ROOT / "game"


def test_snapshot_model_projects_year_and_month_from_fixture():
    result = run_godot_script(GAME, "res://tests/test_snapshot_model.gd")
    assert result.returncode == 0
