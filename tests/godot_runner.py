"""Helpers for executing Godot scripts in the test project."""

from pathlib import Path
import subprocess


def run_godot_script(
    project: Path, script: str, *script_args: str
) -> subprocess.CompletedProcess[str]:
    """Run a script with Godot headless and preserve its exit status."""
    return subprocess.run(
        ["godot", "--headless", "--path", str(project), "--script", script, "--", *script_args],
        capture_output=True,
        text=True,
        check=False,
    )
