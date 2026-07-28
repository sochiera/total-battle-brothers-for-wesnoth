"""G88.1f: wyeksportowana gra startuje partię bez terminala (e2e na pakiecie).

Publiczny kontrakt (task-497):
- Bramka buduje pakiet przez ``scripts/package.sh`` do katalogu poza repo i
  uruchamia **wyeksportowane binarium**, nie ``godot --path game``.
- Start w czystym środowisku: izolowany ``HOME``, bez ``TBB_BRIDGE_COMMAND`` /
  ``TBB_STATE_PATH`` / ``TBB_SAVE_PATH`` / ``TBB_SEED``.
- Po starcie w danych użytkownika jest wznawialny plik stanu partii; most z
  ``src/`` pakietu wznawia go i zwraca poprawny snapshot.
- Drugie uruchomienie tego samego pakietu na tym samym HOME kontynuuje partię.
- Bez ``src/`` obok binarium: start kończy się bez zawieszki i bez udawanego
  pliku stanu.
- Bramka nie brudzi ``git status --porcelain``; przy braku szablonów eksportu
  komunikat jest czytelny (nie tautologiczna zieleń).
"""

from __future__ import annotations

import json
import os
import shutil
import stat
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKAGE_SCRIPT = ROOT / "scripts" / "package.sh"
_EXPECTED_BINARY_NAME = "TotalBattleBrothers.x86_64"
_APP_USERDATA_REL = Path(
    ".local/share/godot/app_userdata/Total Battle Brothers"
)
_STATE_NAME = "bridge_state.jsonl"
# _ready woła most synchronicznie (OS.execute); kilka klatek wystarcza do
# wyjścia headless bez serwera X.
_QUIT_AFTER_FRAMES = "8"


def _porcelain() -> str:
    return subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout


def _run_package(dest: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["bash", str(PACKAGE_SCRIPT), str(dest)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=300,
        check=False,
    )


def _find_game_binary(package_dir: Path) -> Path:
    preferred = package_dir / _EXPECTED_BINARY_NAME
    if preferred.is_file() and (preferred.stat().st_mode & stat.S_IXUSR):
        return preferred
    candidates = [
        p
        for p in package_dir.iterdir()
        if p.is_file()
        and not p.name.endswith(".pck")
        and (p.stat().st_mode & stat.S_IXUSR)
        and p.stat().st_size > 0
    ]
    assert candidates, (
        f"package dir must contain an executable game binary under {package_dir}; "
        f"found: {sorted(p.name for p in package_dir.iterdir())}"
    )
    return candidates[0]


def _clean_run_env(home: Path) -> dict[str, str]:
    """Minimalne środowisko: izolowany HOME, PATH z systemowym python3, zero TBB_*."""
    path = os.environ.get("PATH", "/usr/bin:/bin")
    env = {
        "HOME": str(home),
        "PATH": path,
        "LANG": os.environ.get("LANG", "C.UTF-8"),
    }
    # Godot czasem czyta XDG_*; trzymaj je pod izolowanym HOME, nie dziedzicz hosta.
    env["XDG_DATA_HOME"] = str(home / ".local" / "share")
    env["XDG_CONFIG_HOME"] = str(home / ".config")
    env["XDG_CACHE_HOME"] = str(home / ".cache")
    for forbidden in (
        "TBB_BRIDGE_COMMAND",
        "TBB_STATE_PATH",
        "TBB_SAVE_PATH",
        "TBB_SEED",
    ):
        env.pop(forbidden, None)
    return env


def _state_path(home: Path) -> Path:
    return home / _APP_USERDATA_REL / _STATE_NAME


def _run_exported_binary(
    binary: Path, *, home: Path, timeout: float = 90.0
) -> subprocess.CompletedProcess[str]:
    env = _clean_run_env(home)
    return subprocess.run(
        [str(binary), "--headless", "--quit-after", _QUIT_AFTER_FRAMES],
        cwd=binary.parent,
        env=env,
        capture_output=True,
        text=True,
        check=False,
        timeout=timeout,
    )


def _bridge_snapshot_from_state(src_dir: Path, state_path: Path) -> dict:
    """Wznów partię wyłącznie ze źródeł w pakiecie; zwróć snapshot (dict)."""
    env = {**os.environ, "PYTHONPATH": str(src_dir)}
    serve = subprocess.run(
        [
            sys.executable,
            "-m",
            "tbbbridge",
            "serve",
            "--resume",
            str(state_path),
        ],
        input='{"type":"snapshot"}\n',
        cwd=src_dir.parent,  # katalog pakietu, nie drzewo repo
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    assert serve.returncode == 0, (
        f"resume via package sources must exit 0; stderr={serve.stderr!r} "
        f"stdout={serve.stdout!r}"
    )
    lines = [ln for ln in serve.stdout.splitlines() if ln.strip()]
    assert lines, f"expected JSON snapshot line, got empty stdout={serve.stdout!r}"
    payload = json.loads(lines[0])
    assert payload.get("ok") is True, payload
    snapshot = payload.get("snapshot")
    assert isinstance(snapshot, dict), payload
    return snapshot


def _bridge_next_turn_and_save(src_dir: Path, state_path: Path) -> dict:
    """Jedna tura + zapis na istniejącym pliku stanu (dowód ciągłości AC4)."""
    env = {**os.environ, "PYTHONPATH": str(src_dir)}
    serve = subprocess.run(
        [
            sys.executable,
            "-m",
            "tbbbridge",
            "serve",
            "--resume",
            str(state_path),
        ],
        input=(
            '{"type":"next_turn"}\n'
            f'{{"type":"save","path":{json.dumps(str(state_path))}}}\n'
            '{"type":"snapshot"}\n'
        ),
        cwd=src_dir.parent,
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    assert serve.returncode == 0, (
        f"next_turn+save via package sources must exit 0; stderr={serve.stderr!r} "
        f"stdout={serve.stdout!r}"
    )
    lines = [ln for ln in serve.stdout.splitlines() if ln.strip()]
    assert len(lines) >= 3, f"expected 3 JSON lines, got {serve.stdout!r}"
    snap_payload = json.loads(lines[2])
    assert snap_payload.get("ok") is True, snap_payload
    snapshot = snap_payload.get("snapshot")
    assert isinstance(snapshot, dict), snap_payload
    return snapshot


def test_exported_package_autostarts_party_without_terminal_or_tbb_env(tmp_path):
    """Wyeksportowane binarium w czystym HOME utrwala wznawialną partię (e2e).

    Realistic defect: G88.1c buduje pakiet (bin+.pck+src), G88.1a/d sprawdzają
    krótki headless start pod kątem brakujących zasobów, G88.1e dowodzi utrwalenia
    startu tylko przez ``godot --path game`` / sondy. Żadna bramka nie uruchamia
    **wyeksportowanego** binarium bez ``TBB_*`` i nie wymaga pliku stanu w
    ``app_userdata`` ani drugiego startu na tym samym HOME. Po eksporcie
    ``res://`` to PCK — domyślna ścieżka ``src/`` z drzewa źródeł znika; gracz
    dostaje binarium, które nie nawiązuje sesji albo zaczyna partię od zera
    przy każdym starcie.
    """
    assert PACKAGE_SCRIPT.is_file(), (
        "scripts/package.sh must exist (G88.1c) so the e2e builds a real package"
    )

    before = _porcelain()
    dest = tmp_path / "dist-e2e"
    pack = _run_package(dest)
    pack_log = f"{pack.stdout}\n{pack.stderr}"
    if pack.returncode != 0:
        templates_missing = (
            "export template" in pack_log.lower()
            or "szablon" in pack_log.lower()
        )
        hint = (
            "Brak szablonów eksportu Godot 4.2.2 — zainstaluj paczkę pod "
            "~/.local/share/godot/export_templates/4.2.2.stable/ "
            "(linux_release.x86_64). "
            if templates_missing
            else ""
        )
        raise AssertionError(
            f"{hint}scripts/package.sh must build the package for e2e; "
            f"rc={pack.returncode} output:\n{pack_log}"
        )

    binary = _find_game_binary(dest)
    src_dir = binary.parent / "src"
    assert src_dir.is_dir(), f"package must include src/ beside binary: {dest}"

    home = tmp_path / "player-home"
    home.mkdir()
    state = _state_path(home)
    assert not state.exists(), "precondition: clean home has no party state"

    first = _run_exported_binary(binary, home=home)
    first_log = f"{first.stdout}\n{first.stderr}"
    assert first.returncode == 0, (
        f"exported binary headless start must exit 0; rc={first.returncode} "
        f"output:\n{first_log}"
    )
    assert state.is_file() and state.stat().st_size > 0, (
        "after first package start without TBB_* vars, party state must exist "
        f"at {state} (Godot app_userdata under isolated HOME); "
        f"home tree: {sorted(p.relative_to(home) for p in home.rglob('*') if p.is_file())}\n"
        f"output:\n{first_log}"
    )

    snapshot_after_first = _bridge_snapshot_from_state(src_dir, state)
    assert snapshot_after_first.get("calendar") == {"year": 1, "month": 1}, (
        "fresh package start must leave a resumable seed-0 party "
        f"(calendar year 1 month 1); got {snapshot_after_first.get('calendar')!r}"
    )
    assert snapshot_after_first.get("result", {}).get("player_result") == "ongoing"

    # AC4: zewnętrzna tura rozróżnia wznowienie od startu od zera (seed 0
    # po samym starcie wygląda identycznie).
    advanced = _bridge_next_turn_and_save(src_dir, state)
    assert advanced.get("calendar") != {"year": 1, "month": 1}, (
        "oracle next_turn must advance calendar so second binary run can prove resume; "
        f"got {advanced.get('calendar')!r}"
    )
    calendar_after_advance = advanced["calendar"]
    # AC4 wzmocnienie: --quit-after wychodzi 0 także gdy start_session w _ready
    # padnie i nie ruszy pliku. Sam niezmieniony kalendarz nie dowodzi, że
    # binarium realnie wznawiało (persist_snapshot = snapshot+save).
    state_meta_before_second = (state.stat().st_mtime_ns, state.stat().st_size)
    state_bytes_before_second = state.read_bytes()

    second = _run_exported_binary(binary, home=home)
    second_log = f"{second.stdout}\n{second.stderr}"
    assert second.returncode == 0, (
        f"second package start on same HOME must exit 0; rc={second.returncode} "
        f"output:\n{second_log}"
    )
    assert state.is_file() and state.stat().st_size > 0, (
        f"state file must remain after second start: {state}"
    )
    state_meta_after_second = (state.stat().st_mtime_ns, state.stat().st_size)
    state_bytes_after_second = state.read_bytes()
    assert (
        state_meta_after_second != state_meta_before_second
        or state_bytes_after_second != state_bytes_before_second
    ), (
        "second package start must leave a re-save trace on the state file "
        "(mtime/size or content) proving resume+persist_snapshot ran; "
        f"meta before={state_meta_before_second} after={state_meta_after_second}; "
        f"bytes unchanged={state_bytes_after_second == state_bytes_before_second}\n"
        f"output:\n{second_log}"
    )
    snapshot_after_second = _bridge_snapshot_from_state(src_dir, state)
    assert snapshot_after_second.get("calendar") == calendar_after_advance, (
        "second package start on the same HOME must resume the same party "
        f"(calendar {calendar_after_advance!r}), not seed-0 anew; "
        f"got {snapshot_after_second.get('calendar')!r}"
    )

    after = _porcelain()
    assert after == before, (
        "package e2e must not dirty git status --porcelain.\n"
        f"--- before ---\n{before}--- after ---\n{after}"
    )


def test_exported_package_without_bridge_sources_leaves_no_fake_party_state(tmp_path):
    """Brak src/ w pakiecie: start bez zawieszki i bez udawanego pliku stanu.

    Realistic defect: binarium startuje, most pada po cichu, a pusty / śmieciowy
    plik stanu udaje udaną partię; albo proces wisi na OS.execute. Kontrakt:
    odróżnialna porażka — brak wznawialnego pliku stanu, proces kończy się w
    timeoutcie bramki.
    """
    assert PACKAGE_SCRIPT.is_file(), "scripts/package.sh must exist"

    dest = tmp_path / "dist-no-src"
    pack = _run_package(dest)
    pack_log = f"{pack.stdout}\n{pack.stderr}"
    if pack.returncode != 0:
        templates_missing = (
            "export template" in pack_log.lower()
            or "szablon" in pack_log.lower()
        )
        hint = (
            "Brak szablonów eksportu Godot 4.2.2 — zainstaluj paczkę pod "
            "~/.local/share/godot/export_templates/4.2.2.stable/ "
            "(linux_release.x86_64). "
            if templates_missing
            else ""
        )
        raise AssertionError(
            f"{hint}need a built package to strip src/; rc={pack.returncode}\n{pack_log}"
        )

    binary = _find_game_binary(dest)
    src_dir = binary.parent / "src"
    assert src_dir.is_dir(), "precondition: package includes src/ before we remove it"
    shutil.rmtree(src_dir)
    assert not src_dir.exists()

    home = tmp_path / "player-home-no-src"
    home.mkdir()
    state = _state_path(home)

    run = _run_exported_binary(binary, home=home, timeout=90.0)
    run_log = f"{run.stdout}\n{run.stderr}"
    # Koniec bez zawieszki (timeout rzuciłby TimeoutExpired). Kod wyjścia może
    # być 0 — ważne, że nie ma wznawialnej partii w userdata.
    assert not state.exists() or state.stat().st_size == 0, (
        "without package src/, start must not leave a resumable party state file "
        f"at {state}; size="
        f"{state.stat().st_size if state.exists() else 'missing'}\n"
        f"output:\n{run_log}"
    )
