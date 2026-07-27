from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]

# Stale Godot/test paths that still place probes under production scripts/.
_STALE_SCRIPT_PROBE_PATH = re.compile(
    r"res://scripts/[\w./-]*_probe\.gd|game/scripts/[\w./-]*_probe\.gd"
)
_CONTRACT_SUFFIXES = {".py", ".gd", ".md", ".tscn", ".cfg", ".txt"}


def test_godot_bootstrap_exposes_the_configured_main_control_scene_without_tbb_copies():
    game = ROOT / "game"
    project = game / "project.godot"
    scene = game / "scenes" / "main.tscn"
    script = game / "scripts" / "main.gd"

    assert project.is_file()
    assert 'run/main_scene="res://scenes/main.tscn"' in project.read_text()

    assert scene.is_file()
    scene_text = scene.read_text()
    assert 'type="Control"' in scene_text
    assert 'path="res://scripts/main.gd"' in scene_text

    assert script.is_file()
    assert not any(
        path.name == "tbb" or path.name.startswith("tbb.")
        for path in game.rglob("*")
    )
    # Text-only: binary assets under game/assets/*.png must not be decoded as UTF-8.
    assert not any(
        re.search(
            r"^\s*(?:from|import)\s+tbb(?:\.|\s|$)",
            path.read_text(encoding="utf-8"),
            re.MULTILINE,
        )
        for path in game.rglob("*")
        if path.is_file() and path.suffix in _CONTRACT_SUFFIXES
    )


def test_godot_client_scripts_exclude_test_probes_and_stale_probe_paths():
    """Production client scripts/ must not host or be addressed as probe home.

    Realistic defect this catches: *_probe.gd scaffolding still mixed into
    game/scripts/ (or callers still use res://scripts/*_probe.gd), so Linux
    packaging and reading the client cannot tell game code from test harness.
    Existing Godot tests currently require the old paths and would stay green.
    """
    game = ROOT / "game"
    scripts = game / "scripts"
    leftover = sorted(path.name for path in scripts.glob("*_probe.gd"))
    assert leftover == [], (
        "test probes must live under game/tests/, not game/scripts/: "
        + ", ".join(leftover)
    )

    for path in scripts.glob("*.gd"):
        text = path.read_text(encoding="utf-8")
        assert "res://tests/" not in text, (
            f"{path.relative_to(ROOT)} must not depend on game/tests/"
        )

    offenders: list[str] = []
    scan_roots = (ROOT / "tests", game, ROOT / "docs")
    for root in scan_roots:
        if not root.is_dir():
            continue
        for path in root.rglob("*"):
            if not path.is_file() or path.suffix not in _CONTRACT_SUFFIXES:
                continue
            if "__pycache__" in path.parts:
                continue
            text = path.read_text(encoding="utf-8", errors="replace")
            if _STALE_SCRIPT_PROBE_PATH.search(text):
                offenders.append(str(path.relative_to(ROOT)))
    # Root markdown (BACKLOG, README, …) can still cite stale probe paths;
    # they sit outside the directory scan above.
    for path in sorted(ROOT.glob("*.md")):
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        if _STALE_SCRIPT_PROBE_PATH.search(text):
            offenders.append(str(path.relative_to(ROOT)))
    assert offenders == [], (
        "stale res://scripts/*_probe.gd or game/scripts/*_probe.gd paths remain in: "
        + ", ".join(offenders)
    )
