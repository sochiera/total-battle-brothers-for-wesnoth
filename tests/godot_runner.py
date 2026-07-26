"""Helpers for executing Godot scripts in the test project."""

from collections.abc import Mapping
from pathlib import Path
import subprocess


def run_godot_script(
    project: Path,
    script: str,
    *script_args: str,
    timeout: float = 60.0,
    env: Mapping[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    """Run a script headlessly, preserving its exit status within ``timeout``."""
    return subprocess.run(
        ["godot", "--headless", "--path", str(project), "--script", script, "--", *script_args],
        capture_output=True,
        text=True,
        check=False,
        timeout=timeout,
        env=env,
    )
