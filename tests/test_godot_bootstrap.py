from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]


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
    assert not any(
        re.search(r"^\s*(?:from|import)\s+tbb(?:\.|\s|$)", path.read_text(), re.MULTILINE)
        for path in game.rglob("*")
        if path.is_file()
    )
