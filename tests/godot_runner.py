"""Helpers for executing Godot scripts in the test project."""

from collections.abc import Mapping
from pathlib import Path
import subprocess

# Single test-side contract for ResultLabel copy (G90.2b).
# MUST stay in sync with game/scripts/main.gd `_get_result_text` (and its
# fallback "Wynik: brak"). Tests assert these exact strings against Godot
# output — change copy in both places in the same change, or expect red tests.
# Bridge tokens: tbbbridge.snapshot._player_result (ongoing|victory|defeat|draw).
PLAYER_RESULT_PL = {
    "ongoing": "Wynik: gra trwa",
    "victory": "Wynik: zwycięstwo",
    "defeat": "Wynik: porażka",
    "draw": "Wynik: remis",
}
MISSING_PLAYER_RESULT_PL = "Wynik: brak"

# task-672 battle_pending gates deferred to task-673+674+675: pending_battle
# persistence, battle_advance/battle_auto client support, and live-bridge
# measurement are outside task-672. Single source for the xfail marker reason
# used across the five Godot e2e measurement files; import instead of copying.
DEFERRED_BATTLE_E2E_REASON = (
    "task-672 battle_pending scenario is deferred to task-673+674+675: "
    "pending_battle persistence, battle_advance/battle_auto client support, "
    "and live-bridge measurement are outside this task"
)


def map_player_result(token: str | None) -> str:
    """Map a bridge player_result token (or None/empty) to on-screen Polish text."""
    if token is None or token == "":
        return MISSING_PLAYER_RESULT_PL
    return PLAYER_RESULT_PL.get(token, MISSING_PLAYER_RESULT_PL)


def run_godot_script(
    project: Path,
    script: str,
    *script_args: str,
    timeout: float = 60.0,
    env: Mapping[str, str] | None = None,
    cwd: Path | None = None,
) -> subprocess.CompletedProcess[str]:
    """Run a script headlessly, preserving its exit status within ``timeout``."""
    return subprocess.run(
        ["godot", "--headless", "--path", str(project), "--script", script, "--", *script_args],
        capture_output=True,
        text=True,
        check=False,
        timeout=timeout,
        env=env,
        cwd=cwd,
    )


def import_game_assets(
    project: Path,
    *,
    timeout: float = 120.0,
    env: Mapping[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    """Run headless ``godot --import`` so PNG assets resolve as Texture2D.

    Public shared helper for gates that need the import cache (``game/.godot/``
    stays untracked). Prefer this over private copies in individual test modules.
    """
    return subprocess.run(
        ["godot", "--headless", "--path", str(project), "--import"],
        capture_output=True,
        text=True,
        check=False,
        timeout=timeout,
        env=env,
    )
