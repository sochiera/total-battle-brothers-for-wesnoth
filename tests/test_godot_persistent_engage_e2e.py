"""G108.1b e2e: the Engage button resolves and persists a party battle."""

from __future__ import annotations

import json
import shlex
from pathlib import Path

import tbb.ai as ai
from godot_runner import run_godot_script
from tbbbridge.persist import read_session, save_session
from tbbbridge.session import Session, apply_command, new_session
from tbb.world import WorldMap


ROOT = Path(__file__).resolve().parents[1]
GAME = ROOT / "game"
PROBE = "res://tests/persistent_order_process_probe.gd"
PREFIX = "PERSISTENT_ORDER_PROCESS "
SEED = 73
EXHAUSTED_ACTION_STATUS = "Oddział już działał w tym miesiącu — zakończ turę."
NO_TARGET_STATUS = "Rozkaz starcia nie zmienił stanu."
# The OrderStatusSlot minimum height in main.tscn (75 px) is sized for the
# wrapped form of this, the longest status text we currently ship.
BLOCKED_MARCH_STATUS = (
    "Droga zablokowana w regionie Pogranicze: stoi tam wojsko wroga. "
    "Uderz na wojsko wroga."
)


def _run_process(command_prefix: str, state_path: Path, request_path: Path, phase: str) -> dict:
    result = run_godot_script(
        GAME,
        PROBE,
        command_prefix,
        str(state_path),
        str(request_path),
        str(SEED),
        phase,
        timeout=45,
    )
    assert result.returncode == 0, result.stderr
    assert "SCRIPT ERROR" not in result.stderr, result.stderr
    lines = [line for line in result.stdout.splitlines() if line.startswith(PREFIX)]
    assert len(lines) == 1, result.stdout
    return json.loads(lines[0][len(PREFIX) :])


def _adjacent_parties_session() -> Session:
    """Build the seed-73 state with both adjacent parties alive.

    The monthly movement marker is reset through ``next_turn`` before the
    fixture asks the AI to provide the opposing adjacent party. One recruited
    unit keeps the player party alive after the first engage, so the next AI
    turn can provide a fresh adjacent target for the cycle assertion.
    """
    session = new_session(seed=SEED, player_duchy_id="player")
    for command in (
        {"type": "order", "order": "recruit"},
        {"type": "order", "order": "muster"},
        {"type": "order", "order": "march"},
        {"type": "next_turn"},
    ):
        session = apply_command(session, command)

    ai_duchy = next(duchy for duchy in session.game.duchies if duchy.duchy_id == "ai")
    world = ai.muster_duchy_party(session.world, ai_duchy)
    return Session(
        world=world,
        game=session.game.sync_from_world(world),
        calendar=session.calendar,
        rng=session.rng,
        player_duchy_id=session.player_duchy_id,
        seed=session.seed,
        last_battle=session.last_battle,
    )


def _party_without_adjacent_enemy_session() -> Session:
    return apply_command(
        new_session(seed=SEED, player_duchy_id="player"),
        {"type": "order", "order": "muster"},
    )


def _blocked_march_session() -> Session:
    """Build the measured seed-73 state: player at outpost, AI at border.

    The second recruit keeps the player party alive into the Engage phase so
    the resumed process still has a battle target.
    """
    session = new_session(seed=SEED, player_duchy_id="player")
    for command in (
        {"type": "order", "order": "recruit"},
        {"type": "order", "order": "recruit"},
        {"type": "order", "order": "muster"},
        {"type": "order", "order": "march"},
        {"type": "next_turn"},
    ):
        session = apply_command(session, command)
    return session


def _march_then_engage_session() -> Session:
    """Build a player path whose effective march leaves an adjacent AI party."""
    session = new_session(seed=SEED, player_duchy_id="player")
    for command in (
        {"type": "order", "order": "recruit"},
        {"type": "order", "order": "muster"},
    ):
        session = apply_command(session, command)

    ai_duchy = next(duchy for duchy in session.game.duchies if duchy.duchy_id == "ai")
    world = ai.muster_duchy_party(session.world, ai_duchy)
    world = ai.march_duchy_party(world, ai_duchy)
    return Session(
        world=world,
        game=session.game.sync_from_world(world),
        calendar=session.calendar,
        rng=session.rng,
        player_duchy_id=session.player_duchy_id,
        seed=session.seed,
        last_battle=session.last_battle,
    )


def _stale_battle_after_month_reset_session() -> Session:
    """Keep a previous battle visible while the core marker is reset.

    Use the public next-turn command to keep this fixture aligned with the
    session path used by the bridge.  That command clears ``last_battle``, so
    restore the deliberately stale battle only after the turn transition.
    """
    after_battle = apply_command(
        _adjacent_parties_session(),
        {"type": "order", "order": "engage"},
    )
    after_reset = apply_command(after_battle, {"type": "next_turn"})
    # The public next-turn path also runs the AI.  Keep this fixture's original
    # no-current-target precondition by removing only the AI party after that
    # command, then reattach the intentionally stale battle below.
    player_parties = {
        region: party
        for region, party in after_reset.world.parties.items()
        if party.owner_id == after_reset.player_duchy_id
    }
    reset_world = WorldMap(
        after_reset.world.regions,
        after_reset.world.connections,
        after_reset.world.settlements,
        player_parties,
    )
    return Session(
        world=reset_world,
        game=after_reset.game.sync_from_world(reset_world),
        calendar=after_reset.calendar,
        rng=after_reset.rng,
        player_duchy_id=after_reset.player_duchy_id,
        seed=after_reset.seed,
        last_battle=after_battle.last_battle,
    )


def _polish_engage_result(text: str) -> bool:
    lowered = text.casefold()
    return (
        lowered.startswith("starcie:")
        and "straty:" in lowered
        and "wróg:" in lowered
        and any(outcome in lowered for outcome in ("porażka", "zwycięstwo", "remis"))
    )


def _polish_battle_outcome(text: str) -> bool:
    lowered = text.casefold()
    return any(outcome in lowered for outcome in ("porażka", "zwycięstwo", "remis"))


def test_engage_button_resolves_party_battle_and_persists_it_across_processes(tmp_path):
    """A live click must not be a dead control or leave the state before combat.

    Realistic defect: the scene can expose the correctly named Engage button and
    format an ``engage`` result while its pressed signal is never bound. Existing
    assault e2e and order-result tests then stay green, but an adjacent enemy
    party is untouchable and no post-battle state reaches the resumed process.
    """
    state_path = tmp_path / "persistent-engage-session.json"
    request_path = tmp_path / "bridge-request.jsonl"
    command_prefix = f"PYTHONPATH={shlex.quote(str(ROOT / 'src'))} python3 -m tbbbridge"
    before_battle = _adjacent_parties_session()
    save_session(before_battle, state_path)

    battle = _run_process(command_prefix, state_path, request_path, "engage")
    persisted_after_battle = read_session(state_path)
    cycle = _run_process(
        command_prefix, state_path, request_path, "second_engage_next_turn"
    )

    assert battle["session_command"] == f"{command_prefix} serve --resume '{state_path}'"
    assert battle["battle_before_order"]["tile_count"] == 0
    assert battle["controls_before_order"]["party_position"] == (
        "Położenie oddziału: Posterunek gracza"
    )

    # Visible player effect: resolved result and tiles from both sides.
    after = battle["battle"]
    assert _polish_engage_result(battle["controls"]["order_status"])
    assert after["tile_count"] >= 2, after
    assert after["paint_groups"] >= 2, after
    assert _polish_battle_outcome(after["result_text"]), after

    assert persisted_after_battle.world != before_battle.world

    # A new bridge process reads the post-battle file, rather than pre-click state.
    assert cycle["session_command"] == f"{command_prefix} serve --resume '{state_path}'"
    assert cycle["controls_before_order"]["party_position"] == battle["controls"]["party_position"]
    assert cycle["controls_before_order"]["duchy_status"] == battle["controls"]["duchy_status"]
    assert cycle["battle_before_order"]["tile_count"] == after["tile_count"]
    assert cycle["battle_before_order"]["result_text"] == after["result_text"]

    # The live two-process sequence is: same action blocked, next month, then
    # the same action resolves again with a fresh visible battle result.
    sequence = cycle["sequence"]
    assert sequence["blocked"]["order_status"] == EXHAUSTED_ACTION_STATUS
    assert sequence["after_turn"]["date"] != sequence["blocked"]["date"]
    assert _polish_engage_result(sequence["effective"]["order_status"])
    assert cycle["battle"]["tile_count"] >= 2, cycle
    assert _polish_battle_outcome(cycle["battle"]["result_text"]), cycle

    persisted_after_cycle = read_session(state_path)
    assert persisted_after_cycle.calendar != persisted_after_battle.calendar

    # A third process sees the second battle and its consumed monthly action.
    resumed = _run_process(command_prefix, state_path, request_path, "second_engage")
    assert resumed["controls"]["order_status"] == EXHAUSTED_ACTION_STATUS
    assert resumed["battle_before_order"]["tile_count"] == cycle["battle"]["tile_count"]
    assert resumed["battle_before_order"]["result_text"] == cycle["battle"]["result_text"]
    assert resumed["battle"]["tile_count"] == 0
    assert resumed["battle"]["result_text"] == ""
    assert read_session(state_path).world == persisted_after_cycle.world

    # The same no-op is also useful while the player's party is still alive:
    # it proves the missing-target branch, rather than merely the no-party one.
    no_enemy_state_path = tmp_path / "persistent-engage-no-enemy-session.json"
    no_enemy_request_path = tmp_path / "bridge-no-enemy-request.jsonl"
    living_party_without_enemy = _party_without_adjacent_enemy_session()
    save_session(living_party_without_enemy, no_enemy_state_path)
    no_enemy = _run_process(
        command_prefix, no_enemy_state_path, no_enemy_request_path, "engage"
    )

    assert no_enemy["controls_before_order"]["party_position"] != "Położenie oddziału: brak"
    assert no_enemy["controls"]["party_position"] == (
        no_enemy["controls_before_order"]["party_position"]
    )
    assert no_enemy["controls"]["order_status"] == NO_TARGET_STATUS
    assert no_enemy["battle_before_order"]["tile_count"] == 0
    assert no_enemy["battle"]["tile_count"] == 0
    assert read_session(no_enemy_state_path).world == living_party_without_enemy.world


def test_blocked_march_status_and_followup_engage_survive_process_boundary(tmp_path):
    """A live blocked march explains the blocker; the same saved party can fight.

    Realistic defect: the core/protocol/order-result tests can all pass while
    the live MarchButton drops ``blocked_region`` or the resumed scene loses the
    adjacent AI party.  Then the first process shows a generic no-op and the
    second process cannot reach the in-game Engage escape hatch.  A separate
    layout defect can preserve the exact text while a fixed-height status slot
    lets its wrapped glyphs spill into the party-position row; text-only e2e
    assertions do not catch that visual failure.
    """
    state_path = tmp_path / "persistent-blocked-march-session.json"
    request_path = tmp_path / "bridge-request.jsonl"
    command_prefix = f"PYTHONPATH={shlex.quote(str(ROOT / 'src'))} python3 -m tbbbridge"
    prepared = _blocked_march_session()
    save_session(prepared, state_path)

    blocked = _run_process(command_prefix, state_path, request_path, "blocked_march")
    persisted_after_block = read_session(state_path)

    assert blocked["controls_before_order"]["party_position"] == (
        "Położenie oddziału: Posterunek gracza"
    )
    assert blocked["controls"]["order_status"] == BLOCKED_MARCH_STATUS
    status_layout = blocked["controls"]["order_status_layout"]
    assert status_layout["found"] is True, status_layout
    # The label fills the slot via anchors, so only the slot height is a real
    # guard: it must cover the wrapped text of the longest status we ship.
    slot = status_layout["slot"]
    assert slot["h"] >= status_layout["label_minimum_h"], status_layout
    assert blocked["controls"]["party_position"] == (
        blocked["controls_before_order"]["party_position"]
    )
    assert blocked["battle"]["tile_count"] == 0
    assert persisted_after_block.world == prepared.world

    resumed = _run_process(command_prefix, state_path, request_path, "engage")

    assert resumed["controls_before_order"]["party_position"] == (
        blocked["controls"]["party_position"]
    )
    assert resumed["battle_before_order"]["tile_count"] == 0
    assert resumed["controls"]["order_status"].startswith("Starcie: ")
    assert resumed["battle"]["tile_count"] >= 2, resumed
    assert resumed["battle"]["paint_groups"] >= 2, resumed
    assert resumed["battle"]["result_text"].strip() != ""
    assert read_session(state_path).world != persisted_after_block.world


def test_march_then_engage_shows_exhausted_month_status_on_live_bridge(tmp_path):
    """An effective March must block the next same-month Engage visibly.

    Realistic defect: the core marks a successful march as acted for the month,
    but BridgeClient currently records the marker only after a battle snapshot.
    The existing Engage e2e starts after a turn reset, so it cannot catch the
    direct march → engage path and the client falls back to the generic no-op.
    """
    state_path = tmp_path / "persistent-march-engage-session.json"
    request_path = tmp_path / "bridge-request.jsonl"
    command_prefix = f"PYTHONPATH={shlex.quote(str(ROOT / 'src'))} python3 -m tbbbridge"
    save_session(_march_then_engage_session(), state_path)

    result = _run_process(command_prefix, state_path, request_path, "march_then_engage")
    sequence = result["sequence"]

    assert sequence["march"]["order_status"] == "Oddział przemieścił się."
    assert sequence["march"]["party_position"] == "Położenie oddziału: Posterunek gracza"
    assert sequence["engage"]["party_position"] == sequence["march"]["party_position"]
    assert sequence["engage"]["order_status"] == EXHAUSTED_ACTION_STATUS


def test_fresh_bridge_reads_acted_marker_after_persisted_march(tmp_path):
    """A fresh client must read a march marker from the saved snapshot."""
    state_path = tmp_path / "persistent-march-fresh-session.json"
    march_request_path = tmp_path / "march-request.jsonl"
    engage_request_path = tmp_path / "engage-request.jsonl"
    command_prefix = f"PYTHONPATH={shlex.quote(str(ROOT / 'src'))} python3 -m tbbbridge"
    save_session(_march_then_engage_session(), state_path)

    marched = _run_process(
        command_prefix, state_path, march_request_path, "march_only"
    )
    assert marched["sequence"]["march"]["order_status"] == "Oddział przemieścił się."
    assert marched["state_exists"] is True

    resumed = _run_process(
        command_prefix, state_path, engage_request_path, "engage_after_march"
    )

    assert resumed["controls_before_order"]["party_position"] == (
        marched["sequence"]["march"]["party_position"]
    )
    assert resumed["battle_before_order"]["tile_count"] == 0
    assert resumed["controls"]["order_status"] == EXHAUSTED_ACTION_STATUS


def test_fresh_bridge_reads_party_marker_instead_of_stale_previous_month_battle(tmp_path):
    """A stale battle must not make a fresh client invent an exhausted action."""
    state_path = tmp_path / "stale-battle-session.json"
    request_path = tmp_path / "bridge-request.jsonl"
    command_prefix = f"PYTHONPATH={shlex.quote(str(ROOT / 'src'))} python3 -m tbbbridge"
    prepared = _stale_battle_after_month_reset_session()
    save_session(prepared, state_path)

    result = _run_process(
        command_prefix, state_path, request_path, "previous_month_battle"
    )

    assert result["fresh_party_acted_this_month"] is False
    assert result["controls_before_order"]["date"] == "Rok 1, miesiąc 3"
    assert result["controls_before_order"]["party_position"] != "Położenie oddziału: brak"
    assert result["battle_before_order"]["tile_count"] >= 2
    assert result["controls"]["order_status"] == NO_TARGET_STATUS
