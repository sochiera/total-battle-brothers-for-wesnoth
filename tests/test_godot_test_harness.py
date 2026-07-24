from pathlib import Path

from godot_runner import run_godot_script

ROOT = Path(__file__).resolve().parents[1]
GAME = ROOT / "game"


def test_run_godot_script_reports_success_and_failure_via_real_returncode():
    ok_result = run_godot_script(GAME, "res://tests/test_exit_code.gd")
    assert ok_result.returncode == 0

    fail_result = run_godot_script(GAME, "res://tests/test_exit_code.gd", "--fail")
    assert fail_result.returncode != 0
