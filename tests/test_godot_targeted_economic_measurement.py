"""G116.1f live-bridge measurement for targeted economic orders."""

from __future__ import annotations

import json
import shlex
from pathlib import Path

from godot_runner import run_godot_script


ROOT = Path(__file__).resolve().parents[1]
GAME = ROOT / "game"
PROBE = "res://tests/targeted_economic_measurement_probe.gd"
PREFIX = "TARGETED_ECONOMIC_MEASUREMENT "
SEED = 73


def _run_probe(command_prefix: str, state_path: Path, request_path: Path) -> dict:
    result = run_godot_script(
        GAME,
        PROBE,
        command_prefix,
        str(state_path),
        str(request_path),
        str(SEED),
        timeout=45,
    )
    assert result.returncode == 0, result.stderr
    assert "SCRIPT ERROR" not in result.stderr, result.stderr
    lines = [line for line in result.stdout.splitlines() if line.startswith(PREFIX)]
    assert len(lines) == 1, result.stdout
    return json.loads(lines[0][len(PREFIX) :])


def test_targeted_economic_orders_diverge_and_survive_live_bridge_resume(tmp_path):
    """G116.1f AC1-3: target routing, foreign no-op and persistence are live.

    Realistic defect missed by the existing contextual-button gate: both orders
    can report ``changed:true`` while persistence or a resumed bridge process
    applies them to the first eligible settlement. Comparing both settlements
    in two fresh runs makes the selected-only effect observable rather than
    trusting the order result or a single panel.
    """
    command_prefix = f"PYTHONPATH={shlex.quote(str(ROOT / 'src'))} python3 -m tbbbridge"
    payload = _run_probe(
        command_prefix,
        tmp_path / "targeted-economic-session.json",
        tmp_path / "bridge-request.jsonl",
    )

    initial = {
        "player lands": {"population": 5, "free": 4, "garrison": 1},
        "player outpost": {"population": 5, "free": 4, "garrison": 1},
    }
    lands_after = {
        "player lands": {"population": 5, "free": 2, "garrison": 3},
        "player outpost": initial["player outpost"],
    }
    outpost_after = {
        "player lands": initial["player lands"],
        "player outpost": {"population": 5, "free": 2, "garrison": 3},
    }

    # AC1: the same sequence diverges by target, and only the selected
    # settlement changes in each fresh live-bridge run.
    assert payload["first"]["target"] == "player lands"
    assert payload["first"]["first_result"] == {
        "order": "recruit",
        "changed": True,
    }
    assert payload["first"]["second_result"] == {
        "order": "recruit",
        "changed": True,
    }
    assert payload["first"]["after"] == lands_after

    assert payload["second"]["target"] == "player outpost"
    assert payload["second"]["first_result"] == {
        "order": "recruit",
        "changed": True,
    }
    assert payload["second"]["second_result"] == {
        "order": "recruit",
        "changed": True,
    }
    assert payload["second"]["after"] == outpost_after
    assert payload["first"]["after"] != payload["second"]["after"]

    # AC2: a real region without a player settlement is an acknowledged no-op
    # with its own reason, and neither player settlement is touched.
    assert payload["foreign"]["target"] == "border"
    assert payload["foreign"]["ok"] is True
    assert payload["foreign"]["result"] == {
        "order": "recruit",
        "changed": False,
        "reason": "brak własnej osady w tym regionie",
    }
    assert payload["foreign"]["after"] == initial

    # AC3: after the persisted order, a new ``serve --resume`` process sees
    # exactly the targeted settlement state, not merely the same status text.
    for scenario, expected in (
        (payload["first"], lands_after),
        (payload["second"], outpost_after),
    ):
        assert "serve --resume" in scenario["resumed_command"]
        assert scenario["resumed"] == expected


def test_live_bridge_remeasures_resolution_and_k115_growth(tmp_path):
    """G116.1f AC4-6: fresh live-bridge regression and K115 measurement.

    Realistic defect missed by the existing gates: core and in-process bridge
    tests can keep the known R1M7/R1M4 outcomes while a persistent save/resume
    path advances a different number of months, or while ``develop`` after
    five persisted turns still reports the old permanent-population reason.
    This gate observes both outcomes and the population trajectory through the
    same live JSON Lines bridge used by the client.
    """
    command_prefix = f"PYTHONPATH={shlex.quote(str(ROOT / 'src'))} python3 -m tbbbridge"
    payload = _run_probe(
        command_prefix,
        tmp_path / "targeted-economic-session.json",
        tmp_path / "bridge-request.jsonl",
    )

    # AC4: both fresh live runs resolve, with the measured months pinned.
    passive = payload["regressions"]["passive"]
    assert passive["turns"] == 6
    assert passive["date"] == {"year": 1, "month": 7}
    assert passive["result"] == "defeat"
    assert "serve --resume" in passive["resumed_command"]

    active = payload["regressions"]["active"]
    assert active["date"] == {"year": 1, "month": 4}
    assert active["result"] == "victory"
    assert [state["order"] for state in active["states"]] == [
        "recruit",
        "muster",
        "march",
        "next_turn",
        "engage",
        "next_turn",
        "assault",
        "next_turn",
        "assault",
    ]
    assert "serve --resume" in active["resumed_command"]

    # AC5: develop x2 drains one real player settlement, five live turns grow
    # it back, and a later economic order changes state.
    growth = payload["growth"]
    assert growth["drained"]["player lands"] == {
        "population": 5,
        "free": 2,
        "garrison": 1,
    }
    assert growth["turns"][-1]["settlements"]["player lands"] == {
        "population": 8,
        "free": 5,
        "garrison": 1,
    }
    outpost_states = [
        turn["settlements"]["player outpost"]
        for turn in growth["turns"]
        if "player outpost" in turn["settlements"]
    ]
    assert outpost_states[0] == {
        "population": 7,
        "free": 6,
        "garrison": 1,
    }
    assert max(state["free"] for state in outpost_states) == 6
    assert "player outpost" not in growth["turns"][-1]["settlements"]
    assert growth["order_result"] == {
        "order": "develop",
        "changed": True,
    }

    # AC6: the measured numbers are part of the K116 public project record.
    backlog = (ROOT / "BACKLOG.md").read_text(encoding="utf-8")
    k116_start = backlog.index("## Kamień milowy 116")
    k116_end = backlog.index("## Dług/refaktor", k116_start)
    k116 = backlog[k116_start:k116_end]
    for marker in (
        "6× `next_turn`",
        "R1M7",
        "R1M4",
        "population=5",
        "free=2",
        "free=4",
        "population=8",
        "free=5",
        "population=7",
        "free=6",
        "changed:true",
    ):
        assert marker in k116, f"K116 must record measured value {marker!r}"
