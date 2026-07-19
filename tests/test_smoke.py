"""Smoke test — potwierdza, że framework testów i pakiet rdzenia działają."""

from types import SimpleNamespace

import tbb


def test_package_imports_and_has_version():
    assert isinstance(tbb.__version__, str)
    assert tbb.__version__  # niepusta wersja


def test_headless_main_runs_full_game_and_reports_result(capsys):
    from tbb.__main__ import main

    assert main() == 0
    output = capsys.readouterr().out.strip().lower()
    assert "zwycięzca: ai" in output
    assert "rok: 1" in output
    assert "miesiąc: 2" in output


def test_headless_main_reports_final_calendar_date(capsys):
    from tbb.__main__ import main

    assert main() == 0
    output = capsys.readouterr().out.lower()
    assert "zwycięzca: ai" in output
    assert "rok: 1" in output
    assert "miesiąc: 2" in output


def test_headless_main_delegates_to_driver_and_prints_winner(monkeypatch, capsys):
    import tbb.__main__ as headless

    starting_world = object()
    starting_game = object()
    result_world = object()
    result_game = SimpleNamespace(
        winner=SimpleNamespace(duchy_id="review-winner")
    )
    result_calendar = SimpleNamespace(year=8, month=9)
    calls = []

    monkeypatch.setattr(
        headless.game,
        "create_headless_game",
        lambda: (starting_world, starting_game),
    )

    def fake_run(world, game, rng):
        calls.append((world, game, rng))
        return result_world, result_game, result_calendar

    monkeypatch.setattr(headless.driver, "run_headless_game", fake_run)

    exit_code = headless.main()

    output = capsys.readouterr().out.strip().lower()
    assert exit_code == 0
    assert len(calls) == 1
    assert calls[0][:2] == (starting_world, starting_game)
    assert isinstance(calls[0][2], headless.Rng)
    assert output == "zwycięzca: review-winner rok: 8, miesiąc: 9."


def test_headless_main_prints_draw_when_driver_has_no_winner(monkeypatch, capsys):
    import tbb.__main__ as headless

    starting_world = object()
    starting_game = object()
    result_game = SimpleNamespace(winner=None)
    result_calendar = SimpleNamespace(year=3, month=11)

    monkeypatch.setattr(
        headless.game,
        "create_headless_game",
        lambda: (starting_world, starting_game),
    )
    monkeypatch.setattr(
        headless.driver,
        "run_headless_game",
        lambda world, game, rng: (object(), result_game, result_calendar),
    )

    exit_code = headless.main()

    output = capsys.readouterr().out.strip().lower()
    assert exit_code == 0
    assert output == (
        "wynik: remis — brak zwycięzcy. rok: 3, miesiąc: 11."
    )
