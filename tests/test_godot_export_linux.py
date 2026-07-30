"""G88.1a: bramka toolchainu eksportu — wykonywalny artefakt Linux/X11.

Publiczny kontrakt:
- ``game/export_presets.cfg`` w repo z presetem celu Linux/X11 x86-64.
- ``godot --headless --path game --export-release <preset> <path>`` produkuje
  wykonywalny plik (istnieje, rozmiar > 0, bit ``+x``) oraz towarzyszący ``.pck``.
- Szablony eksportu i artefakty wynikowe pozostają poza gitem.

Uwaga o Godocie 4.2.2: ``--export-release`` potrafi zwrócić exit 0 mimo błędu
(brak ``export_presets.cfg`` albo brak szablonów) — bramka nie ufa returncode
i dowodzi eksportu istnieniem artefaktów.
"""

from __future__ import annotations

import re
import stat
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GAME = ROOT / "game"
PRESETS = GAME / "export_presets.cfg"

# Publiczna nazwa presetu — identyfikuje cel Linux/X11 (kryterium akceptacji).
LINUX_PRESET_NAME = "Linux/X11"

_PLATFORM_RE = re.compile(r'(?m)^\s*platform\s*=\s*"Linux/X11"\s*$')
_ARCH_RE = re.compile(
    r'(?m)^\s*binary_format/architecture\s*=\s*"x86_64"\s*$'
)
_NAME_RE = re.compile(
    rf'(?m)^\s*name\s*=\s*"{re.escape(LINUX_PRESET_NAME)}"\s*$'
)


def _export_release(output_binary: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            "godot",
            "--headless",
            "--path",
            str(GAME),
            "--export-release",
            LINUX_PRESET_NAME,
            str(output_binary),
        ],
        capture_output=True,
        text=True,
        check=False,
        timeout=300,
    )


def _combined(result: subprocess.CompletedProcess[str]) -> str:
    return f"{result.stdout}\n{result.stderr}"


def test_export_presets_cfg_declares_linux_x11_x86_64():
    """Preset Linux/X11 x86-64 musi być wersjonowany w repo.

    Realistic defect: w repo nie ma ``export_presets.cfg`` (stan startowy G88),
    więc jedyny sposób uruchomienia to ``godot --path game`` z konsoli — dokładnie
    to, czego brief zabrania. Istniejące bramki headless tego nie sprawdzają.
    """
    assert PRESETS.is_file(), (
        "game/export_presets.cfg must be committed so headless export has a "
        "Linux/X11 preset without opening the editor GUI"
    )
    text = PRESETS.read_text(encoding="utf-8")
    assert _NAME_RE.search(text), (
        f'export_presets.cfg must declare name="{LINUX_PRESET_NAME}" '
        "(public preset id used by --export-release)"
    )
    assert _PLATFORM_RE.search(text), (
        'export_presets.cfg must set platform="Linux/X11"'
    )
    assert _ARCH_RE.search(text), (
        'export_presets.cfg must set binary_format/architecture="x86_64"'
    )


def test_headless_export_release_produces_executable_and_pck():
    """Headless --export-release musi zostawić binarium +x i .pck poza gitem.

    Realistic defect: Godot 4.2.2 kończy eksport z exit 0 mimo błędu (brak
    presetów / brak szablonów w ~/.local/share/godot/export_templates/4.2.2.stable/),
    więc test patrzący tylko na returncode jest tautologią i „zielony" bez
    artefaktu. Bramka dowodzi eksportu plikami: istnieje, size>0, bit +x, obok .pck.
    """
    assert PRESETS.is_file(), (
        "game/export_presets.cfg missing — cannot exercise --export-release"
    )

    with tempfile.TemporaryDirectory(prefix="tbb-export-") as tmp:
        out_dir = Path(tmp)
        binary = out_dir / "TotalBattleBrothers.x86_64"
        result = _export_release(binary)
        log = _combined(result)

        if not binary.is_file():
            templates_missing = (
                "No export template found" in log
                or "export template" in log.lower()
            )
            hint = (
                "Brak szablonów eksportu Godot 4.2.2 — zainstaluj paczkę pod "
                "~/.local/share/godot/export_templates/4.2.2.stable/ "
                "(linux_release.x86_64). "
                if templates_missing
                else ""
            )
            raise AssertionError(
                f"{hint}"
                f"headless --export-release {LINUX_PRESET_NAME!r} did not create "
                f"executable at {binary}. rc={result.returncode} output:\n{log}"
            )

        size = binary.stat().st_size
        assert size > 0, f"export binary is empty: {binary}"
        mode = binary.stat().st_mode
        assert mode & stat.S_IXUSR, (
            f"export binary must be executable (+x), mode={oct(mode)} path={binary}"
        )

        # Godot 4.2.2 Linux export writes sibling <stem>.pck (not <binary>.pck).
        # e.g. TotalBattleBrothers.x86_64 → TotalBattleBrothers.pck
        pck = binary.with_suffix(".pck")
        if not pck.is_file():
            # Fallback if output path had no multi-part suffix (name.x86_64-free).
            pck = out_dir / (binary.name + ".pck")
        assert pck.is_file(), (
            f"export must also write a .pck beside the binary under {out_dir}; "
            f"found: {sorted(p.name for p in out_dir.iterdir())}\noutput:\n{log}"
        )
        assert pck.stat().st_size > 0, f"export .pck is empty: {pck}"


# Ścieżki zasobów w .pck są zapisane jako surowe bajty ``res://…`` (Godot 4.2.2).
_PCK_TEST_PROBE_MARKER = b"res://tests/"
_PCK_TEXTURE_PATHS = (
    b"res://assets/map_ground_earth.png",
    b"res://assets/map_ground_grass.png",
    b"res://assets/map_ground_stone.png",
    b"res://assets/party_player_unit.png",
    b"res://assets/settlement.png",
    b"res://assets/side_attacker.png",
    b"res://assets/side_defender.png",
    b"res://assets/terrain_forest.png",
    b"res://assets/terrain_hills.png",
    b"res://assets/terrain_plains.png",
)
# Fragmenty logu Godota 4.2.2 przy braku zasobu w pakiecie (nie pełna semantyka sesji).
_MISSING_RESOURCE_MARKERS = (
    "Failed loading resource",
    "Failed to load",
    "Cannot open file",
    "Can't open file",
    "No loader found for resource",
)


def _pck_required_production_paths() -> tuple[bytes, ...]:
    """Scena główna + wszystkie skrypty z game/scripts/ + dziesięć tekstur (AC2)."""
    script_paths = tuple(
        f"res://scripts/{p.name}".encode()
        for p in sorted((GAME / "scripts").glob("*.gd"))
    )
    return (b"res://scenes/main.tscn",) + script_paths + _PCK_TEXTURE_PATHS


def test_export_pck_excludes_test_probes_keeps_production_resources():
    """Wyeksportowany .pck nie niesie sond z res://tests/, zostawia produkcję.

    Realistic defect: preset ma ``export_filter="all_resources"`` i pusty
    ``exclude_filter``, więc Godot pakuje cały ``game/tests/`` (sondy
    ``*_probe.gd``) do artefaktu gracza. G88.1a sprawdza tylko istnienie
    niepustego .pck — nie jego zawartość. Kontrakt G88.1d: zero
    ``res://tests/…`` w .pck, przy zachowaniu sceny, skryptów i dziesięciu tekstur;
    headless start pakietu bez błędu brakującego zasobu (AC3).
    """
    assert PRESETS.is_file(), (
        "game/export_presets.cfg missing — cannot exercise --export-release"
    )
    required = _pck_required_production_paths()
    assert any(p.startswith(b"res://scripts/") for p in required), (
        "game/scripts/ must contribute at least one .gd path to the PCK contract"
    )

    with tempfile.TemporaryDirectory(prefix="tbb-export-pck-") as tmp:
        out_dir = Path(tmp)
        binary = out_dir / "TotalBattleBrothers.x86_64"
        result = _export_release(binary)
        log = _combined(result)

        pck = binary.with_suffix(".pck")
        if not pck.is_file():
            pck = out_dir / (binary.name + ".pck")
        assert pck.is_file() and pck.stat().st_size > 0, (
            f"export must write non-empty .pck to inspect contents; "
            f"found: {sorted(p.name for p in out_dir.iterdir())}\n"
            f"rc={result.returncode} output:\n{log}"
        )

        data = pck.read_bytes()
        assert _PCK_TEST_PROBE_MARKER not in data, (
            "exported .pck must not contain any res://tests/… probe paths "
            "(exclude test probes from the Linux/X11 export preset); "
            "found test-probe marker in package"
        )
        missing = [p.decode() for p in required if p not in data]
        assert not missing, (
            "exported .pck must still carry production resources "
            f"(main scene, all game/scripts/*.gd, ten textures); missing: {missing}"
        )

        # AC3: krótki headless start binarium+.pck — błąd brakującego zasobu
        # nie może przejść na samym skanie bajtów .pck.
        assert binary.is_file() and (binary.stat().st_mode & stat.S_IXUSR), (
            f"export binary must exist and be +x for headless package start: {binary}"
        )
        run = subprocess.run(
            [str(binary), "--headless", "--quit-after", "2"],
            cwd=out_dir,
            capture_output=True,
            text=True,
            check=False,
            timeout=60,
        )
        run_log = f"{run.stdout}\n{run.stderr}"
        hit = [m for m in _MISSING_RESOURCE_MARKERS if m in run_log]
        assert not hit, (
            "headless start of exported package must not report missing resources "
            f"(markers={hit}); rc={run.returncode} output:\n{run_log}"
        )


def test_headless_export_leaves_git_worktree_clean():
    """Eksport do katalogu poza repo nie zmienia ``git status`` (snapshot przed→po).

    Realistic defect: preset ``export_path`` albo uboczny zapis ląduje w drzewie
    roboczym (np. pod ``game/`` / ``build/``) bez reguły gitignore — po bramce
    pojawiają się nowe ścieżki (``.x86_64`` / ``.pck``) i artefakty wpadają do
    commita. Porównujemy snapshot porcelain przed i po: WIP w worktree nie
    blokuje bramki (TDD z nieskomitowanym presetem), liczy się tylko delta.
    """
    assert PRESETS.is_file(), "game/export_presets.cfg missing"

    def _porcelain() -> str:
        return subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        ).stdout

    before = _porcelain()

    with tempfile.TemporaryDirectory(prefix="tbb-export-") as tmp:
        binary = Path(tmp) / "TotalBattleBrothers.x86_64"
        result = _export_release(binary)
        # Nie wymagamy tu sukcesu eksportu ponownie — tylko że próba nie brudzi git.
        # Gdy brak szablonów, Godot i tak nie powinien zapisać nic w repo.
        _ = result

    after = _porcelain()
    assert after == before, (
        "git status --porcelain must be unchanged after headless export "
        "(templates and artifacts stay outside git).\n"
        f"--- before ---\n{before}--- after ---\n{after}"
    )
    # Extra guard with WIP present: no .x86_64 / .pck paths in porcelain output.
    artifact_lines = [
        line
        for line in after.splitlines()
        if line.rstrip().endswith((".x86_64", ".pck"))
    ]
    assert not artifact_lines, (
        "export must not leave .x86_64 / .pck paths visible in git status, "
        f"got:\n" + "\n".join(artifact_lines)
    )
