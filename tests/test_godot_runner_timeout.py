from pathlib import Path
import subprocess

import pytest

from godot_runner import run_godot_script

ROOT = Path(__file__).resolve().parents[1]
GAME = ROOT / "game"


def test_hanging_script_raises_timeout_instead_of_blocking_forever():
    with pytest.raises(subprocess.TimeoutExpired):
        run_godot_script(GAME, "res://tests/test_hang.gd", timeout=5)


def test_well_behaved_script_finishes_within_timeout():
    result = run_godot_script(GAME, "res://tests/test_exit_code.gd", timeout=30)
    assert result.returncode == 0
