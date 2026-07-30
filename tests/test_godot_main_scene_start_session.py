import json
import os
import shlex
from pathlib import Path

from godot_runner import map_player_result, run_godot_script
from tbbbridge.persist import read_session
from tbbbridge.session import apply_command, new_session


ROOT = Path(__file__).resolve().parents[1]
GAME = ROOT / "game"
PROBE = "res://tests/start_session_probe.gd"
INVALID_CONFIG_PROBE = "res://tests/start_session_invalid_config_probe.gd"
PREFIX = "START_SESSION "
INVALID_PREFIX = "START_SESSION_INVALID "
ENVIRONMENT_AUTOSTART_PROBE = "res://tests/environment_autostart_probe.gd"
ENVIRONMENT_AUTOSTART_PREFIX = "ENVIRONMENT_AUTOSTART "
START_STATUS_PROBE = "res://tests/start_status_probe.gd"
START_STATUS_PREFIX = "START_STATUS "
SEED = 73
BROKEN_BRIDGE_COMMAND = "/nonexistent/python-brak"
START_FAILURE_STATUS = "Nie udało się uruchomić mostu ani rozpocząć partii."


def _controls(snapshot: dict) -> dict:
    player_status = next(
        duchy
        for duchy in snapshot["duchies"]
        if duchy["id"] == snapshot["player_duchy"]
    )
    return {
        "date": (
            f"Rok {snapshot['calendar']['year']}, "
            f"miesiąc {snapshot['calendar']['month']}"
        ),
        "result": map_player_result(snapshot['result']['player_result']),
        "duchy_status": (
            f"Morale: {player_status['morale']}, "
            f"osady: {player_status['settlements']}, "
            f"oddziały: {player_status['parties']}"
        ),
        "regions": [region["name"] for region in snapshot["map"]["regions"]],
    }


def _environment_controls(snapshot: dict, order_status: str = "") -> dict:
    return {**_controls(snapshot), "order_status": order_status}


def _environment_autostart_payload(result) -> dict:
    assert result.returncode == 0, result.stderr
    assert "SCRIPT ERROR" not in result.stderr, result.stderr
    lines = [
        line
        for line in result.stdout.splitlines()
        if line.startswith(ENVIRONMENT_AUTOSTART_PREFIX)
    ]
    assert len(lines) == 1, result.stdout
    return json.loads(lines[0][len(ENVIRONMENT_AUTOSTART_PREFIX) :])


def _start_status_payload(result) -> dict:
    assert result.returncode == 0, result.stderr
    assert "SCRIPT ERROR" not in result.stderr, result.stderr
    lines = [
        line
        for line in result.stdout.splitlines()
        if line.startswith(START_STATUS_PREFIX)
    ]
    assert len(lines) == 1, result.stdout
    return json.loads(lines[0][len(START_STATUS_PREFIX) :])


def _assert_bridge_start_failure_status(payload: dict, *, expect_started: bool | None) -> None:
    """Publiczny kontrakt: gracz widzi czytelny komunikat startu, nie puste kontrolki."""
    assert payload["available"] is True
    assert payload["has_start_status_label"] is True
    assert payload["start_status"] == START_FAILURE_STATUS, payload
    assert payload["order_status"] == ""
    assert payload["date"] == ""
    assert payload["duchy_status"] == ""
    assert payload["regions"] == []
    assert payload["state_exists"] is False
    if expect_started is not None:
        assert payload["started"] is expect_started


def _assert_successful_start_has_no_error_status(payload: dict, snapshot: dict) -> None:
    assert payload["available"] is True
    assert payload["has_start_status_label"] is True
    # Po udanym starcie etykieta jest pusta (bez komunikatu błędu).
    assert payload["start_status"] == "", payload
    assert payload["order_status"] == ""
    assert payload["date"] == (
        f"Rok {snapshot['calendar']['year']}, "
        f"miesiąc {snapshot['calendar']['month']}"
    )
    player_status = next(
        duchy
        for duchy in snapshot["duchies"]
        if duchy["id"] == snapshot["player_duchy"]
    )
    assert payload["duchy_status"] == (
        f"Morale: {player_status['morale']}, "
        f"osady: {player_status['settlements']}, "
        f"oddziały: {player_status['parties']}"
    )
    assert payload["regions"] == [region["name"] for region in snapshot["map"]["regions"]]
    # G88.1e: udany start utrwala partię; nieudany (powyżej) zostawia brak pliku.
    assert payload["state_exists"] is True


def test_start_session_renders_fresh_game_without_advancing_then_binds_next_turn(tmp_path):
    """Defekt: start sesji tylko czyta snapshot, więc plik stanu nie powstaje —
    gracz zamyka grę po samym starcie i przy kolejnym uruchomieniu traci partię.
    Kontrakt G88.1e: sam start utrwala partię (wznawialny plik stanu), bez tury.
    """
    command_prefix = (
        f"PYTHONPATH={shlex.quote(str(ROOT / 'src'))} python3 -m tbbbridge"
    )
    state_path = tmp_path / "session.json"
    result = run_godot_script(
        GAME, PROBE, command_prefix, str(state_path), str(SEED), timeout=30
    )

    assert result.returncode == 0, result.stderr
    assert "SCRIPT ERROR" not in result.stderr, result.stderr
    lines = [line for line in result.stdout.splitlines() if line.startswith(PREFIX)]
    assert len(lines) == 1, result.stdout

    session = new_session(SEED)
    assert json.loads(lines[0][len(PREFIX) :]) == {
        "available": True,
        "started": True,
        # G88.1e: plik stanu zaraz po starcie (przed pierwszym rozkazem/turą).
        "state_exists_after_start": True,
        "after_start": _controls(session.snapshot()),
        "after_first_press": _controls(session.next_turn().snapshot()),
    }


def test_start_session_rejects_invalid_config_without_changing_scene_or_starting_bridge(tmp_path):
    environment = os.environ.copy()
    environment["XDG_DATA_HOME"] = str(tmp_path / "xdg-data")
    result = run_godot_script(
        GAME,
        INVALID_CONFIG_PROBE,
        str(tmp_path / "session.json"),
        str(tmp_path / "bridge-started"),
        timeout=30,
        env=environment,
    )

    assert result.returncode == 0, result.stderr
    assert "SCRIPT ERROR" not in result.stderr, result.stderr
    lines = [
        line for line in result.stdout.splitlines() if line.startswith(INVALID_PREFIX)
    ]
    assert len(lines) == 1, result.stdout
    assert json.loads(lines[0][len(INVALID_PREFIX) :]) == {
        "available": True,
        "results": [False] * 11,
        "controls_unchanged": True,
        "bridge_started": False,
        "state_exists": False,
        "request_exists": False,
        "has_start_status_label": True,
        # Niepoprawna konfiguracja to też nieudany start — scena nie może zostać niema.
        "start_status": START_FAILURE_STATUS,
    }


def test_scene_autostarts_from_environment_and_resumes_after_next_turn(tmp_path):
    state_path = tmp_path / "autostart-session.json"
    environment = os.environ.copy()
    environment.update(
        {
            "TBB_BRIDGE_COMMAND": (
                f"PYTHONPATH={shlex.quote(str(ROOT / 'src'))} python3 -m tbbbridge"
            ),
            "TBB_STATE_PATH": str(state_path),
            "TBB_SEED": str(SEED),
        }
    )

    first = run_godot_script(
        GAME,
        ENVIRONMENT_AUTOSTART_PROBE,
        "--press",
        timeout=30,
        env=environment,
    )
    second = run_godot_script(
        GAME, ENVIRONMENT_AUTOSTART_PROBE, timeout=30, env=environment
    )

    fresh = new_session(SEED)
    after_turn = fresh.next_turn()
    assert _environment_autostart_payload(first) == {
        "after_start": _environment_controls(fresh.snapshot()),
        "after_press": _environment_controls(after_turn.snapshot()),
        "state_exists": True,
    }
    assert _environment_autostart_payload(second) == {
        "after_start": _environment_controls(after_turn.snapshot()),
        "after_press": _environment_controls(after_turn.snapshot()),
        "state_exists": True,
    }


def test_scene_autostarts_persists_development_and_then_advances_on_the_next_process(tmp_path):
    state_path = tmp_path / "autostart-develop-session.json"
    environment = os.environ.copy()
    environment.update(
        {
            "TBB_BRIDGE_COMMAND": (
                f"PYTHONPATH={shlex.quote(str(ROOT / 'src'))} python3 -m tbbbridge"
            ),
            "TBB_STATE_PATH": str(state_path),
            "TBB_SEED": str(SEED),
        }
    )

    first = run_godot_script(
        GAME,
        ENVIRONMENT_AUTOSTART_PROBE,
        "--develop",
        timeout=30,
        env=environment,
    )
    second = run_godot_script(
        GAME,
        ENVIRONMENT_AUTOSTART_PROBE,
        "--press",
        timeout=30,
        env=environment,
    )

    fresh = new_session(SEED)
    developed = apply_command(fresh, {"type": "order", "order": "develop"})
    after_turn = developed.next_turn()
    assert _environment_autostart_payload(first) == {
        "after_start": _environment_controls(fresh.snapshot()),
        "after_press": _environment_controls(
            developed.snapshot(), "Rozkaz rozwoju zmienił stan."
        ),
        "state_exists": True,
    }
    assert _environment_autostart_payload(second) == {
        "after_start": _environment_controls(developed.snapshot()),
        "after_press": _environment_controls(after_turn.snapshot()),
        "state_exists": True,
    }


def test_scene_development_status_survives_resume_and_reports_no_change(tmp_path):
    state_path = tmp_path / "autostart-develop-status-session.json"
    environment = os.environ.copy()
    environment.update(
        {
            "TBB_BRIDGE_COMMAND": (
                f"PYTHONPATH={shlex.quote(str(ROOT / 'src'))} python3 -m tbbbridge"
            ),
            "TBB_STATE_PATH": str(state_path),
            "TBB_SEED": str(SEED),
        }
    )

    # G92.2a: two player keeps each accept four develops → eight changes, then no-op.
    develop_args = ["--develop"] * 8
    first = run_godot_script(
        GAME,
        ENVIRONMENT_AUTOSTART_PROBE,
        *develop_args,
        timeout=30,
        env=environment,
    )
    second = run_godot_script(
        GAME, ENVIRONMENT_AUTOSTART_PROBE, "--develop", timeout=30, env=environment
    )

    session = new_session(SEED)
    for _ in range(8):
        session = apply_command(session, {"type": "order", "order": "develop"})
    assert _environment_autostart_payload(first) == {
        "after_start": _environment_controls(new_session(SEED).snapshot()),
        "after_press": {
            **_environment_controls(
                session.snapshot(), "Rozkaz rozwoju zmienił stan."
            ),
        },
        "state_exists": True,
    }
    assert _environment_autostart_payload(second) == {
        "after_start": _environment_controls(session.snapshot()),
        "after_press": {
            **_environment_controls(
                session.snapshot(), "Rozkaz rozwoju nie zmienił stanu."
            ),
        },
        "state_exists": True,
    }


def test_scene_entry_without_environment_uses_default_session_config_and_resumes_turn(
    tmp_path,
):
    environment = os.environ.copy()
    for variable in ("TBB_BRIDGE_COMMAND", "TBB_STATE_PATH", "TBB_SEED"):
        environment.pop(variable, None)
    xdg_data = tmp_path / "xdg-data"
    environment["XDG_DATA_HOME"] = str(xdg_data)

    # Sonda liczy state_exists z BridgeConfig.from_environment() — ta sama ścieżka
    # co domyślny zapis. Gdyby XDG_DATA_HOME nie przenosiło user://, test byłby
    # zielony mimo zapisu do prawdziwego ~/.local/share. Asercje poniżej trzymają
    # trwałość w izolowanym katalogu i dom poza zakresem.
    home_godot = Path.home() / ".local" / "share" / "godot"
    home_state_before = {
        path: (path.stat().st_mtime_ns, path.stat().st_size)
        for path in home_godot.rglob("bridge_state.jsonl")
    } if home_godot.exists() else {}

    first = run_godot_script(
        GAME, ENVIRONMENT_AUTOSTART_PROBE, "--press", timeout=30, env=environment
    )
    second = run_godot_script(
        GAME, ENVIRONMENT_AUTOSTART_PROBE, timeout=30, env=environment
    )

    fresh = new_session(0)
    after_turn = fresh.next_turn()
    assert _environment_autostart_payload(first) == {
        "after_start": _environment_controls(fresh.snapshot()),
        "after_press": _environment_controls(after_turn.snapshot()),
        "state_exists": True,
    }
    assert _environment_autostart_payload(second) == {
        "after_start": _environment_controls(after_turn.snapshot()),
        "after_press": _environment_controls(after_turn.snapshot()),
        "state_exists": True,
    }

    state_files = list(xdg_data.rglob("bridge_state.jsonl"))
    assert len(state_files) == 1, state_files
    assert state_files[0].is_file()
    assert state_files[0].stat().st_size > 0

    home_state_after = {
        path: (path.stat().st_mtime_ns, path.stat().st_size)
        for path in home_godot.rglob("bridge_state.jsonl")
    } if home_godot.exists() else {}
    assert home_state_after == home_state_before


def test_start_session_shows_start_status_when_bridge_command_cannot_run(tmp_path):
    """Defekt: valid config + padający most → false i puste kontrolki, bez komunikatu."""
    state_path = tmp_path / "broken-bridge-session.json"
    environment = os.environ.copy()
    # _ready też woła start_session — zły most w env, żeby nie zapełnić sceny wcześniej.
    environment.update(
        {
            "TBB_BRIDGE_COMMAND": BROKEN_BRIDGE_COMMAND,
            "TBB_STATE_PATH": str(state_path),
            "TBB_SEED": str(SEED),
            "XDG_DATA_HOME": str(tmp_path / "xdg-data"),
        }
    )

    result = run_godot_script(
        GAME,
        START_STATUS_PROBE,
        BROKEN_BRIDGE_COMMAND,
        str(state_path),
        str(SEED),
        timeout=30,
        env=environment,
    )
    payload = _start_status_payload(result)
    _assert_bridge_start_failure_status(payload, expect_started=False)


def test_scene_autostart_shows_start_status_when_bridge_command_cannot_run(tmp_path):
    """Defekt: _ready z TBB_BRIDGE_COMMAND=/nonexistent… zostawia niemą scenę."""
    state_path = tmp_path / "autostart-broken-bridge.json"
    environment = os.environ.copy()
    environment.update(
        {
            "TBB_BRIDGE_COMMAND": BROKEN_BRIDGE_COMMAND,
            "TBB_STATE_PATH": str(state_path),
            "TBB_SEED": str(SEED),
            "XDG_DATA_HOME": str(tmp_path / "xdg-data"),
        }
    )

    result = run_godot_script(
        GAME, START_STATUS_PROBE, timeout=30, env=environment
    )
    payload = _start_status_payload(result)
    _assert_bridge_start_failure_status(payload, expect_started=None)


def test_start_session_start_status_is_not_an_error_when_bridge_starts(tmp_path):
    """Udany start bez tury: brak komunikatu błędu + wznawialny plik stanu (G88.1e)."""
    state_path = tmp_path / "start-status-ok-session.json"
    environment = os.environ.copy()
    environment["XDG_DATA_HOME"] = str(tmp_path / "xdg-data")
    for variable in ("TBB_BRIDGE_COMMAND", "TBB_STATE_PATH", "TBB_SEED"):
        environment.pop(variable, None)
    command_prefix = (
        f"PYTHONPATH={shlex.quote(str(ROOT / 'src'))} python3 -m tbbbridge"
    )

    result = run_godot_script(
        GAME,
        START_STATUS_PROBE,
        command_prefix,
        str(state_path),
        str(SEED),
        timeout=30,
        env=environment,
    )
    payload = _start_status_payload(result)
    assert payload["started"] is True
    fresh = new_session(SEED).snapshot()
    _assert_successful_start_has_no_error_status(payload, fresh)
    # Sonda nie naciska tury — plik musi być zapisem świeżej partii, nie śmieciem.
    resumed = read_session(state_path)
    assert resumed.snapshot()["calendar"] == fresh["calendar"]
    assert resumed.seed == SEED

