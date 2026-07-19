"""Smoke test — potwierdza, że framework testów i pakiet rdzenia działają."""

import tbb


def test_package_imports_and_has_version():
    assert isinstance(tbb.__version__, str)
    assert tbb.__version__  # niepusta wersja


def test_headless_main_returns_zero():
    from tbb.__main__ import main

    assert main() == 0


def test_headless_main_runs_full_game_and_prints_winner(capsys):
    from tbb.__main__ import main

    exit_code = main()

    output = capsys.readouterr().out.strip().lower()
    assert exit_code == 0
    assert "zwycięzca" in output
    assert any(duchy_id in output for duchy_id in ("player", "ai"))
