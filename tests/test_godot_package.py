"""G88.1c: jedno polecenie buduje kompletny katalog pakietu (binarium + .pck + src/).

Publiczny kontrakt (task-494):
- ``scripts/package.sh <katalog-docelowy>`` — jedno wykonywalne polecenie;
  ścieżka docelowa jest argumentem (domyślnie nic nie ląduje w repo).
- Po sukcesie (exit 0) katalog docelowy zawiera: wykonywalne binarium gry
  (size>0, bit +x), towarzyszący ``.pck`` (size>0) oraz katalog źródeł mostu
  ``src/`` obok binarium — pierwszy kandydat ``BridgeConfig`` z G88.1b.
- Skopiowane źródła są samowystarczalne: ``PYTHONPATH=<pakiet>/src``
  ``python -m tbbbridge serve <seed>`` + linia ``{"type":"snapshot"}`` na stdin
  daje odpowiedź z ``ok: true`` i kluczem ``snapshot`` (bez drzewa repo).
- Niepowodzenie budowy → niezerowy exit, czytelny komunikat i brak „udawanego"
  pakietu (binarium + .pck + src/ jako komplet).
- Budowa nie brudzi ``git status --porcelain``.

Uwaga o Godocie 4.2.2: sam ``--export-release`` bywa exit 0 bez artefaktów —
sukces pakietu rozstrzygają pliki i funkcjonalność mostu, nie returncode Godota.
"""

from __future__ import annotations

import json
import os
import stat
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKAGE_SCRIPT = ROOT / "scripts" / "package.sh"
# Publiczna nazwa artefaktu z package.sh / export Linux (G88.1a).
_EXPECTED_BINARY_NAME = "TotalBattleBrothers.x86_64"
_EXPECTED_PCK_NAME = "TotalBattleBrothers.pck"


def _porcelain() -> str:
    return subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout


def _run_package(
    dest: Path, *,env: dict[str, str] | None = None
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["bash", str(PACKAGE_SCRIPT), str(dest)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=300,
        check=False,
        env=env,
    )


def _find_game_binary(package_dir: Path) -> Path:
    """Znajdź wykonywalne binarium gry w katalogu pakietu (nie katalog, nie .sh)."""
    candidates = [
        p
        for p in package_dir.iterdir()
        if p.is_file()
        and not p.name.endswith(".pck")
        and (p.stat().st_mode & stat.S_IXUSR)
        and p.stat().st_size > 0
    ]
    # Prefer typical Godot Linux export name when several executables exist.
    for preferred in candidates:
        if "TotalBattleBrothers" in preferred.name or preferred.name.endswith(
            ".x86_64"
        ):
            return preferred
    assert candidates, (
        f"package dir must contain an executable game binary under {package_dir}; "
        f"found: {sorted(p.name for p in package_dir.iterdir())}"
    )
    return candidates[0]


def _sibling_pck(binary: Path) -> Path:
    """Godot 4.2.2: sibling <stem>.pck (TotalBattleBrothers.x86_64 → .pck)."""
    pck = binary.with_suffix(".pck")
    if pck.is_file():
        return pck
    alt = binary.parent / (binary.name + ".pck")
    return alt


def _looks_like_complete_package(dest: Path) -> bool:
    """Komplet G88.1c: binarium +x size>0, sibling .pck size>0, src/ obok."""
    if not dest.is_dir():
        return False
    try:
        binary = _find_game_binary(dest)
    except AssertionError:
        return False
    pck = _sibling_pck(binary)
    return (
        pck.is_file()
        and pck.stat().st_size > 0
        and (binary.parent / "src").is_dir()
    )


def test_package_script_builds_complete_dir_with_src_beside_binary(tmp_path):
    """Polecenie pakietu kładzie binarium, .pck i src/ obok siebie — most działa.

    Realistic defect: G88.1a dowodzi samego eksportu (binarium+.pck), G88.1b
    uczy BridgeConfig szukać ``src/`` obok binarium, ale brak kroku, który ten
    katalog tam kładzie. Wyeksportowana gra nie ma czym uruchomić mostu.
    Istniejące bramki nie wołają żadnego polecenia pakietu ani nie sprawdzają
    samowystarczalności skopiowanych źródeł poza drzewem repo.
    """
    assert PACKAGE_SCRIPT.is_file(), (
        "scripts/package.sh must exist as the single package-build command "
        "(target dir is argv; artifacts must not land in the repo by default)"
    )
    mode = PACKAGE_SCRIPT.stat().st_mode
    assert mode & stat.S_IXUSR, (
        f"scripts/package.sh must be executable (+x), mode={oct(mode)}"
    )

    before = _porcelain()
    dest = tmp_path / "dist-package"
    result = _run_package(dest)
    log = f"{result.stdout}\n{result.stderr}"
    assert result.returncode == 0, (
        f"scripts/package.sh {dest} must exit 0 on success; "
        f"rc={result.returncode} output:\n{log}"
    )
    assert dest.is_dir(), f"package destination must be a directory: {dest}"

    binary = _find_game_binary(dest)
    pck = _sibling_pck(binary)
    assert pck.is_file() and pck.stat().st_size > 0, (
        f"package must include non-empty .pck beside binary; "
        f"looked for {pck}, contents: {sorted(p.name for p in dest.iterdir())}\n"
        f"output:\n{log}"
    )

    # BridgeConfig first candidate: <executable_dir>/src
    src_dir = binary.parent / "src"
    assert src_dir.is_dir(), (
        f"package must place bridge sources at {src_dir} "
        f"(BridgeConfig candidate beside the game binary); "
        f"contents: {sorted(p.name for p in dest.iterdir())}"
    )

    # Functional completeness: serve snapshot using only packaged sources.
    # cwd outside the package and outside the repo tree; PYTHONPATH = package src.
    work = tmp_path / "unrelated-cwd"
    work.mkdir()
    env = {**os.environ, "PYTHONPATH": str(src_dir)}
    serve = subprocess.run(
        [sys.executable, "-m", "tbbbridge", "serve", "7"],
        input='{"type":"snapshot"}\n',
        cwd=work,
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    assert serve.returncode == 0, (
        f"bridge from package sources must exit 0; stderr={serve.stderr!r} "
        f"stdout={serve.stdout!r}"
    )
    lines = [ln for ln in serve.stdout.splitlines() if ln.strip()]
    assert lines, f"expected JSON snapshot line, got empty stdout={serve.stdout!r}"
    payload = json.loads(lines[0])
    assert payload.get("ok") is True, payload
    assert isinstance(payload.get("snapshot"), dict), payload

    after = _porcelain()
    assert after == before, (
        "git status --porcelain must be unchanged after package build "
        "(artifacts stay outside the repo).\n"
        f"--- before ---\n{before}--- after ---\n{after}"
    )


def test_package_script_failed_export_exits_nonzero_without_fake_package(tmp_path):
    """Nieudany eksport → exit != 0, komunikat, brak udawanego kompletu pakietu.

    Realistic defect: Godot 4.2.2 bywa exit 0 bez artefaktów. Skrypt akceptujący
    **stare** binarium/.pck w katalogu docelowym (z poprzedniej próby) i doklejający
    świeże ``src/`` kończy się exit 0 z „udawanym" pakietem. Kryterium 4: niezerowy
    exit gdy eksport nic nie wyprodukował, czytelny błąd, brak kompletu
    binarium+.pck+src.
    """
    assert PACKAGE_SCRIPT.is_file(), "scripts/package.sh must exist"

    fake_bin = tmp_path / "fake-bin"
    fake_bin.mkdir()
    fake_godot = fake_bin / "godot"
    # Symuluj cichy fail Godota: exit 0, zero nowych artefaktów.
    fake_godot.write_text(
        "#!/usr/bin/env bash\n"
        "exit 0\n",
        encoding="utf-8",
    )
    fake_godot.chmod(0o755)

    dest = tmp_path / "dist-fail"
    dest.mkdir()
    # Stale z poprzedniej próby — nie wolno uznać ich za sukces eksportu.
    leftover_src = dest / "src"
    leftover_src.mkdir()
    (leftover_src / "marker").write_text("stale", encoding="utf-8")
    stale_bin = dest / _EXPECTED_BINARY_NAME
    stale_bin.write_bytes(b"stale-binary-not-from-export")
    stale_bin.chmod(0o755)
    (dest / _EXPECTED_PCK_NAME).write_bytes(b"stale-pck")

    env = {
        **os.environ,
        "PATH": f"{fake_bin}{os.pathsep}{os.environ.get('PATH', '')}",
    }
    result = _run_package(dest, env=env)
    log = f"{result.stdout}\n{result.stderr}"
    assert result.returncode != 0, (
        "failed package build must exit non-zero (must not treat stale "
        "binary/.pck in dest as a successful export); "
        f"rc={result.returncode} output:\n{log}"
    )
    assert "BŁĄD" in result.stderr or "błąd" in result.stderr.lower(), (
        f"failed package build must print a readable error; stderr:\n{result.stderr}"
    )
    assert not _looks_like_complete_package(dest), (
        f"failed build must not leave a complete-looking package under {dest}; "
        f"contents: {sorted(p.name for p in dest.iterdir()) if dest.is_dir() else dest}"
    )
    # Pre-clean + fail_export: znane artefakty z dest nie mogą zostać po awarii
    # (stare pliki z poprzedniej próby też muszą zniknąć — inaczej fałszywy sukces).
    assert not (dest / _EXPECTED_BINARY_NAME).exists(), (
        f"failed build must not leave package binary {dest / _EXPECTED_BINARY_NAME}"
    )
    assert not (dest / _EXPECTED_PCK_NAME).exists(), (
        f"failed build must not leave package .pck {dest / _EXPECTED_PCK_NAME}"
    )
    assert not (dest / "src").is_dir(), (
        f"failed build must not leave package src/ under {dest}"
    )


def test_package_script_rejects_symlink_dest_resolving_into_repo(tmp_path):
    """Symlink spoza drzewa → worktree musi być odrzucony (kryterium 5).

    Realistic defect: strażnik porównuje logiczne ``pwd`` (bez ``-P``). Wtedy
    ``/tmp/out`` → ``$ROOT/docs`` omija ``case`` i eksport zapisuje artefakty
    w repo (dirty porcelain). Oczekiwanie: resolve DEST/ROOT przez ``pwd -P``,
    exit != 0 z komunikatem o dest poza repo — **zanim** ruszy godot.
    """
    assert PACKAGE_SCRIPT.is_file(), "scripts/package.sh must exist"

    # Cel logicznie poza repo, fizycznie wewnątrz (docs/ jest w worktree).
    link = tmp_path / "out-into-repo"
    link.symlink_to(ROOT / "docs")

    fake_bin = tmp_path / "fake-bin"
    fake_bin.mkdir()
    fake_godot = fake_bin / "godot"
    # Gdy strażnik zawiedzie, godot nie powinien być wołany — a jeśli będzie,
    # zero artefaktów (unikamy brudzenia docs/ w teście).
    fake_godot.write_text("#!/usr/bin/env bash\nexit 0\n", encoding="utf-8")
    fake_godot.chmod(0o755)

    before = _porcelain()
    env = {
        **os.environ,
        "PATH": f"{fake_bin}{os.pathsep}{os.environ.get('PATH', '')}",
    }
    result = _run_package(link, env=env)
    log = f"{result.stdout}\n{result.stderr}"
    assert result.returncode != 0, (
        "package.sh must reject dest that resolves into the repo via symlink; "
        f"rc={result.returncode} output:\n{log}"
    )
    err = result.stderr.lower()
    assert "poza repo" in err or "poza" in err, (
        "rejection must mention dest outside repo (guard), not a later export "
        f"failure; stderr:\n{result.stderr}"
    )
    # Nie wolno dojść do ścieżki eksportu (to objaw ominięcia strażnika).
    assert "eksport" not in err and "export" not in err, (
        "symlink-into-repo dest must die at path guard before export; "
        f"stderr:\n{result.stderr}"
    )
    after = _porcelain()
    assert after == before, (
        "rejecting in-repo dest must not dirty git status --porcelain.\n"
        f"--- before ---\n{before}--- after ---\n{after}"
    )
