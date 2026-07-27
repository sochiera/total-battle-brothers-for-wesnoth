"""R82.1b: generated out/ artifacts stay outside git.

Default CLI paths (tbbbridge → out/state.json, tbbui → out/game.html) remain
the contract; regenerating them must not pollute the working tree.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Default CLI outputs plus the former tracked ref copy (not a fixture).
_OUT_ARTIFACT_PATHS = (
    "out/state.json",
    "out/game.html",
    "out/state.json.ref",
)


def test_git_does_not_track_any_file_under_out():
    """``git ls-files out/`` is empty — no generated artifact in the index."""
    result = subprocess.run(
        ["git", "ls-files", "out/"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    tracked = [line for line in result.stdout.splitlines() if line.strip()]
    assert tracked == [], f"out/ must not be tracked, found: {tracked}"


def test_default_out_artifact_paths_are_gitignored():
    """Default tool outputs under out/ match .gitignore (tree stays clean)."""
    for relative in _OUT_ARTIFACT_PATHS:
        result = subprocess.run(
            ["git", "check-ignore", "-q", "--", relative],
            cwd=ROOT,
        )
        assert result.returncode == 0, (
            f"{relative} must be ignored by git so regenerating CLI defaults "
            "does not dirty the working tree"
        )
