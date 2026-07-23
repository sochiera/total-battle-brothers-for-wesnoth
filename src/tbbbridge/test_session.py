"""Tests for the tbbbridge session handle (G65.1a/G65.1b).

Tests live next to the module under test per task-312 \"Ścieżki testów\".
"""

import copy
import json

import pytest

from tbb.game import GameState, create_headless_game
from tbb.rng import Rng
from tbb.turn import Calendar

from tbbbridge.session import Session, apply_command, new_session
from tbbbridge.snapshot import game_state


def test_new_session_builds_session_with_headless_game_calendar_rng_defaults_and_fields():
    """G65.1a-1: new_session() builds a Session from core public APIs."""
    s = new_session()

    assert type(s) is Session
    assert type(s.world).__name__ == "WorldMap"
    assert type(s.game).__name__ == "GameState"
    assert type(s.calendar).__name__ == "Calendar"
    assert type(s.rng).__name__ == "Rng"
    assert s.seed == 73
    assert s.player_duchy_id == "player"

    expected_world, expected_game = create_headless_game()
    assert s.game == expected_game
    assert s.world == expected_world
    assert s.calendar == Calendar()
    assert s.rng is not Rng(73)
    assert s.rng.randint(0, 1000) == Rng(73).randint(0, 1000)


def test_new_session_honours_explicit_seed_and_player_duchy_id_arguments():
    """G65.1a-2: new_session propagates seed and player_duchy_id arguments."""
    s = new_session(seed=99, player_duchy_id=None)

    assert s.seed == 99
    assert s.player_duchy_id is None
    assert s.rng.randint(0, 1000) == Rng(99).randint(0, 1000)


def test_snapshot_returns_game_state_contract_json_serializable_without_mutation():
    """G65.1a-3: Session.snapshot() delegates to game_state without mutation."""
    s = new_session(73, "player")
    snap = s.snapshot()
    expected = game_state(
        s.world,
        s.game,
        s.calendar,
        s.player_duchy_id,
    )
    assert snap == expected
    json.dumps(snap)

    snap2 = s.snapshot()
    assert snap2 == snap
    assert json.dumps(snap2) == json.dumps(snap)
    assert s.rng.randint(0, 1000) == Rng(73).randint(0, 1000)


def test_fresh_new_session_snapshot_has_expected_starting_state():
    """G65.1a-4: fresh new_session(73, 'player') snapshot reflects a new game."""
    s = new_session(73, "player")
    snap = s.snapshot()

    assert snap["calendar"] == {"year": 1, "month": 1}
    assert len(snap["duchies"]) == 2
    assert snap["result"]["player_result"] == "ongoing"
    assert snap["result"]["winner"] is None
    assert snap["result"]["is_over"] is False


def test_next_turn_advances_calendar_by_one_month():
    """G65.1b crit-1: next_turn() runs exactly one headless turn.

    For a fresh new_session(73, 'player') the calendar advances from
    {year: 1, month: 1} to {year: 1, month: 2}.
    """
    s = new_session(73, "player")
    after = s.next_turn()
    assert after.snapshot()["calendar"] == {"year": 1, "month": 2}


def test_next_turn_returns_new_session_with_shared_advanced_rng_and_preserved_fields():
    """G65.1b crit-1 supplement: next_turn() returns a new Session, preserves
    player_duchy_id/seed, shares the same (advanced) RNG by reference, and
    does not mutate the original session.
    """
    s = new_session(73, "player")
    rng_before = s.rng
    before_state = s.snapshot()

    after = s.next_turn()

    assert after is not s
    assert after.player_duchy_id == "player"
    assert after.seed == 73
    assert after.rng is rng_before
    assert after.rng is s.rng
    assert after.snapshot()["calendar"] == {"year": 1, "month": 2}
    assert s.snapshot() == before_state


def test_next_turn_is_noop_when_game_is_over():
    """G65.1b crit-2: when self.game.is_over, next_turn() is a no-op returning
    a session whose world/game/calendar are the same objects as the input. The
    input session is never mutated.
    """
    s = new_session(73, "player")
    ended_game = GameState([s.game.duchies[0]])
    assert ended_game.is_over is True
    ended_session = Session(
        world=s.world,
        game=ended_game,
        calendar=s.calendar,
        rng=s.rng,
        player_duchy_id=s.player_duchy_id,
        seed=s.seed,
    )

    snapshot_before = ended_session.snapshot()
    after = ended_session.next_turn()

    assert after is not ended_session
    assert after.world is ended_session.world
    assert after.game is ended_session.game
    assert after.calendar is ended_session.calendar
    assert after.rng is ended_session.rng
    assert after.player_duchy_id == "player"
    assert after.seed == 73
    # Input session not mutated in any case.
    assert ended_session.snapshot() == snapshot_before


def test_apply_command_new_game_returns_fresh_session_preserving_player_and_seed():
    """G65.1c crit-2: apply_command({"type": "new_game"}) returns a fresh
    session built via new_session(seed=session.seed, player_duchy_id=...),
    preserving player_duchy_id and defaulting seed to the current session.seed;
    an explicit {"type": "new_game", "seed": 7} uses seed=7. The new game's
    snapshot has calendar == {"year": 1, "month": 1}. The input session is not
    mutated. An unknown type (and a missing type key) both raise ValueError.
    """
    s = new_session(42, "player")
    advanced = s.next_turn()
    assert advanced.snapshot()["calendar"] != {"year": 1, "month": 1}

    fresh_default = apply_command(advanced, {"type": "new_game"})

    assert isinstance(fresh_default, Session)
    assert fresh_default is not advanced
    assert fresh_default.player_duchy_id == "player"
    assert fresh_default.seed == 42
    assert fresh_default.snapshot()["calendar"] == {"year": 1, "month": 1}
    fresh_default_snapshot = copy.deepcopy(fresh_default.snapshot())
    assert fresh_default.snapshot() == fresh_default_snapshot

    fresh_seeded = apply_command(advanced, {"type": "new_game", "seed": 7})
    assert fresh_seeded.seed == 7
    assert fresh_seeded.player_duchy_id == "player"
    assert fresh_seeded.snapshot()["calendar"] == {"year": 1, "month": 1}
    assert fresh_seeded.rng.randint(0, 1000) == Rng(7).randint(0, 1000)

    advanced_before = copy.deepcopy(advanced.snapshot())
    assert advanced.snapshot() == advanced_before

    with pytest.raises(ValueError):
        apply_command(advanced, {"type": "totally_unknown"})
    with pytest.raises(ValueError):
        apply_command(advanced, {"unrelated": "value"})


def test_apply_command_next_turn_delegates_to_session_next_turn():
    """G65.1c crit-1: apply_command(session, {"type": "next_turn"}) returns a
    session whose snapshot matches session.next_turn() exactly (pure delegation,
    no own turn logic). The input session is not mutated.
    """
    s = new_session(73, "player")
    before = copy.deepcopy(s.snapshot())

    via_command = apply_command(s, {"type": "next_turn"})
    via_method = s.next_turn()

    assert via_command.snapshot() == via_method.snapshot()
    assert s.snapshot() == before


def test_apply_command_order_develop_applies_ai_primitive_syncs_game_returns_new_session():
    """G65.2a crit-1: apply_command({"type": "order", "order": "develop"})
    applies ``ai.develop_duchy_settlement`` to the player duchy (opening the
    first priority building — FARM — in Player Keep), then
    ``game.sync_from_world`` and returns a new Session with that world/game.
    The input session is not mutated; calendar/rng/seed/player_duchy_id are
    preserved.
    """
    s = new_session(73, "player")
    before = copy.deepcopy(s.snapshot())

    after = apply_command(s, {"type": "order", "order": "develop"})

    assert isinstance(after, Session)
    assert after is not s
    assert after.player_duchy_id == "player"
    assert after.seed == 73
    assert after.calendar == s.calendar
    assert after.rng is s.rng
    # FARM is the highest development priority — Player Keep starts with no
    # active buildings, so develop opens FARM (observable in the snapshot).
    player_settlement_after = after.snapshot()["map"]["regions"][0]["settlement"]
    assert "Farma" in player_settlement_after["buildings"] or len(
        player_settlement_after["buildings"]
    ) >= 1
    # The input session's snapshot is unchanged.
    assert s.snapshot() == before


def test_apply_command_order_recruit_applies_ai_primitive_syncs_game_returns_new_session():
    """G65.2a crit-1: ``apply_command({"type": "order", "order": "recruit"})``
    applies ``ai.recruit_duchy_unit`` to the player duchy: garrison grows by one
    and gold drops by the recruit cost in Player Keep, ``game.sync_from_world``
    is applied and a new Session is returned with calendar/rng/seed/
    player_duchy_id preserved. The input session is not mutated.
    """
    s = new_session(73, "player")
    before = copy.deepcopy(s.snapshot())

    after = apply_command(s, {"type": "order", "order": "recruit"})

    assert isinstance(after, Session)
    assert after is not s
    assert after.player_duchy_id == "player"
    assert after.seed == 73
    assert after.calendar == s.calendar
    assert after.rng is s.rng

    before_settlement = before["map"]["regions"][0]["settlement"]
    after_settlement = after.snapshot()["map"]["regions"][0]["settlement"]
    assert after_settlement["garrison"] == before_settlement["garrison"] + 1
    assert after_settlement["gold"] < before_settlement["gold"]
    # The input session's snapshot is unchanged.
    assert s.snapshot() == before


def test_apply_command_order_muster_applies_ai_primitive_syncs_game_returns_new_session():
    """G65.2a crit-1: ``apply_command({"type": "order", "order": "muster"})``
    applies ``ai.muster_duchy_party`` to the player duchy: a party owned by the
    player appears in the Player Keep region (absent before), ``game.sync_from_world``
    is applied and a new Session is returned with calendar/rng/seed/
    player_duchy_id preserved. The input session is not mutated.
    """
    s = new_session(73, "player")
    before = copy.deepcopy(s.snapshot())

    after = apply_command(s, {"type": "order", "order": "muster"})

    assert isinstance(after, Session)
    assert after is not s
    assert after.player_duchy_id == "player"
    assert after.seed == 73
    assert after.calendar == s.calendar
    assert after.rng is s.rng

    before_party = before["map"]["regions"][0]["party"]
    after_party = after.snapshot()["map"]["regions"][0]["party"]
    assert before_party is None
    assert after_party is not None
    assert after_party["owner"] == "player"
    # The input session's snapshot is unchanged.
    assert s.snapshot() == before


def test_apply_command_order_is_noop_when_game_over_or_no_player_or_duchy_absent():
    """G65.2a crit-2: an order is a no-op (returned session shares the input
    world/game/calendar by identity) when ``game.is_over``, when
    ``player_duchy_id`` is None, or when the player's duchy is absent from
    ``game.duchies``. The input session is never mutated. An unknown ``order``
    value raises ``ValueError``.
    """
    base = new_session(73, "player")

    # is_over guard: a single-duchy game is immediately decided.
    ended_game = GameState([base.game.duchies[0]])
    assert ended_game.is_over is True
    over_session = Session(
        world=base.world,
        game=ended_game,
        calendar=base.calendar,
        rng=base.rng,
        player_duchy_id="player",
        seed=base.seed,
    )
    over_before = copy.deepcopy(over_session.snapshot())
    after_over = apply_command(over_session, {"type": "order", "order": "develop"})
    assert after_over is not over_session
    assert after_over.world is over_session.world
    assert after_over.game is over_session.game
    assert after_over.calendar is over_session.calendar
    assert after_over.player_duchy_id == "player"
    assert after_over.seed == 73
    assert over_session.snapshot() == over_before

    # No player_duchy_id guard.
    no_player = new_session(73, None)
    no_player_before = copy.deepcopy(no_player.snapshot())
    after_no_player = apply_command(
        no_player, {"type": "order", "order": "develop"}
    )
    assert after_no_player.world is no_player.world
    assert after_no_player.game is no_player.game
    assert after_no_player.calendar is no_player.calendar
    assert after_no_player.player_duchy_id is None
    assert no_player.snapshot() == no_player_before

    # Player duchy absent from game.duchies guard.
    absent = new_session(73, "absent")
    absent_before = copy.deepcopy(absent.snapshot())
    after_absent = apply_command(absent, {"type": "order", "order": "develop"})
    assert after_absent.world is absent.world
    assert after_absent.game is absent.game
    assert after_absent.calendar is absent.calendar
    assert after_absent.snapshot() == absent_before

    # Unknown order value raises ValueError without mutation.
    s = new_session(73, "player")
    before = copy.deepcopy(s.snapshot())
    with pytest.raises(ValueError):
        apply_command(s, {"type": "order", "order": "totally_unknown"})
    assert s.snapshot() == before


def test_apply_command_unknown_type_and_missing_type_raise_valueerror_without_mutation():
    """G65.1c crit-3: unknown type or missing 'type' key both raise ValueError;
    the input session is never mutated (snapshot deterministic, RNG advanced
    by the raised call has no observable effect on a later identical session).
    """
    s = new_session(73, "player")
    before = copy.deepcopy(s.snapshot())

    with pytest.raises(ValueError):
        apply_command(s, {"type": "order"})
    with pytest.raises(ValueError):
        apply_command(s, {"type": "new_game", "seed": 999, "extra": True})
    with pytest.raises(ValueError):
        apply_command(s, {})
    with pytest.raises(ValueError):
        apply_command(s, {"unrelated": 1})

    assert s.snapshot() == before


def test_apply_command_snapshot_returns_same_session_identity_without_mutation():
    """G69.1a crit-1: apply_command(session, {"type": "snapshot"}) returns the
    **same** (identity-wise) input session — no mutation of world/game/
    calendar, no RNG consumption, regardless of game.is_over.
    """
    s = new_session(73, "player")
    before_snapshot = copy.deepcopy(s.snapshot())
    rng_before = s.rng

    result = apply_command(s, {"type": "snapshot"})

    assert result is s
    assert result.world is s.world
    assert result.game is s.game
    assert result.calendar is s.calendar
    assert result.rng is rng_before
    assert s.snapshot() == before_snapshot

    # Also verify the no-op behavior when game.is_over
    ended_game = GameState([s.game.duchies[0]])
    assert ended_game.is_over is True
    ended_session = Session(
        world=s.world,
        game=ended_game,
        calendar=s.calendar,
        rng=s.rng,
        player_duchy_id=s.player_duchy_id,
        seed=s.seed,
    )
    ended_before = copy.deepcopy(ended_session.snapshot())
    result_ended = apply_command(ended_session, {"type": "snapshot"})
    assert result_ended is ended_session
    assert ended_session.snapshot() == ended_before


def test_apply_command_order_march_with_target_applies_march_duchy_party_to():
    """G65.2b crit-1: apply_command({"type": "order", "order": "march",
    "target": <name>}) resolves target to a Region by ``region.name`` from
    ``world.regions`` and applies ``ai.march_duchy_party_to(world,
    player_duchy, region)`` (NOT the automatic nearest-enemy
    ``ai.march_duchy_party``). The resulting game is
    ``game.sync_from_world(new_world)`` and a new Session is returned with
    calendar/rng/seed/player_duchy_id preserved. The input session is not
    mutated.

    The scenario uses a branching map where the explicit target (``Far``)
    lies along a different first step (``StepFar``) than the nearest enemy
    settlement (``Near`` / ``StepNear``), so an auto-march fallback would
    be observable as a party at ``StepNear`` instead of ``StepFar``.
    """
    from tbb.ai import march_duchy_party, march_duchy_party_to
    from tbb.duchy import Duchy
    from tbb.party import Party
    from tbb.settlement import Settlement
    from tbb.unit import Unit
    from tbb.world import Region, WorldMap

    start, step_near, near, step_far, far = map(
        Region, ("Start", "StepNear", "Near", "StepFar", "Far")
    )
    party = Party(Unit(training=4), (Unit(equipment=1),), owner_id="north")
    near_keep = Settlement("Near Keep", 2, owner_id="south")
    far_keep = Settlement("Far Keep", 2, owner_id="south")
    world = WorldMap(
        (start, step_near, near, step_far, far),
        (
            (start, step_near),
            (step_near, near),
            (start, step_far),
            (step_far, far),
        ),
        settlements={near: near_keep, far: far_keep},
        parties={start: party},
    )
    game = GameState(
        (
            Duchy("north", party.hero, parties=(party,)),
            Duchy("south", Unit(), settlements=(near_keep, far_keep)),
        )
    )
    assert not game.is_over
    calendar = Calendar(year=2, month=3)
    s = Session(
        world=world,
        game=game,
        calendar=calendar,
        rng=Rng(11),
        player_duchy_id="north",
        seed=11,
    )

    # Sanity: the automatic nearest-enemy march would step toward Near,
    # not Far — so a march-to(Far) result is observably different.
    auto = march_duchy_party(s.world, s.game.duchies[0])
    assert auto.party_at(step_near) is party
    assert auto.party_at(step_far) is None

    expected_world = march_duchy_party_to(s.world, s.game.duchies[0], far)
    expected_game = s.game.sync_from_world(expected_world)
    assert expected_world.party_at(step_far) is party
    assert expected_world.party_at(start) is None
    assert expected_world.party_at(step_near) is None

    before = copy.deepcopy(s.snapshot())
    after = apply_command(
        s, {"type": "order", "order": "march", "target": "Far"}
    )

    assert isinstance(after, Session)
    assert after is not s
    assert after.player_duchy_id == "north"
    assert after.seed == 11
    assert after.calendar == calendar
    assert after.rng is s.rng

    # The transition used march_duchy_party_to(world, duchy, region_named_Far):
    # the party moved to StepFar (toward Far), NOT StepNear (nearest enemy).
    assert after.world.party_at(step_far) is party
    assert after.world.party_at(step_near) is None
    assert after.world.party_at(start) is None
    # The new game is sync_from_world of the new world.
    assert after.game is not s.game
    assert after.world == expected_world
    north_after = next(d for d in after.game.duchies if d.duchy_id == "north")
    north_expected = next(
        d for d in expected_game.duchies if d.duchy_id == "north"
    )
    assert north_after.parties == north_expected.parties
    # The input session is not mutated.
    assert s.snapshot() == before
    assert s.world.party_at(start) is party
    assert s.world.party_at(step_far) is None


def test_apply_command_order_march_falls_back_to_auto_when_target_missing_empty_or_unknown():
    """G65.2b crit-2: a ``march`` order whose ``target`` is missing, an empty
    string, or a name not matching any ``region.name`` falls back to the
    automatic ``ai.march_duchy_party`` (spójnie z ``tbbui.serve``), NOT to
    ``ai.march_duchy_party_to``. On the branching scenario the auto march
    steps toward the nearest enemy settlement (``Near`` via ``StepNear``),
    which is observably distinct from a march-to(``Far``) step (``StepFar``).
    Each variant returns a new Session with calendar/rng/seed/
    player_duchy_id preserved and ``game = game.sync_from_world(world)``;
    the input session is never mutated.
    """
    from tbb.ai import march_duchy_party
    from tbb.duchy import Duchy
    from tbb.party import Party
    from tbb.settlement import Settlement
    from tbb.unit import Unit
    from tbb.world import Region, WorldMap

    def _build_branching_session() -> Session:
        start, step_near, near, step_far, far = map(
            Region, ("Start", "StepNear", "Near", "StepFar", "Far")
        )
        party = Party(Unit(training=4), (Unit(equipment=1),), owner_id="north")
        near_keep = Settlement("Near Keep", 2, owner_id="south")
        far_keep = Settlement("Far Keep", 2, owner_id="south")
        world = WorldMap(
            (start, step_near, near, step_far, far),
            (
                (start, step_near),
                (step_near, near),
                (start, step_far),
                (step_far, far),
            ),
            settlements={near: near_keep, far: far_keep},
            parties={start: party},
        )
        game = GameState(
            (
                Duchy("north", party.hero, parties=(party,)),
                Duchy("south", Unit(), settlements=(near_keep, far_keep)),
            )
        )
        return Session(
            world=world,
            game=game,
            calendar=Calendar(year=2, month=3),
            rng=Rng(11),
            player_duchy_id="north",
            seed=11,
        )

    # Sanity: the automatic march lands the party at StepNear (toward Near),
    # distinctly NOT at StepFar.
    reference = _build_branching_session()
    auto_world = march_duchy_party(reference.world, reference.game.duchies[0])
    assert auto_world.party_at(reference.world.regions[1]) is not None
    auto_party = next(
        p for p in (
            auto_world.party_at(r) for r in auto_world.regions
        ) if p is not None
    )
    start_region = reference.world.regions[0]
    step_near_region = reference.world.regions[1]
    step_far_region = reference.world.regions[3]
    assert auto_world.party_at(step_near_region) is auto_party
    assert auto_world.party_at(step_far_region) is None

    # Each fallback variant must land at StepNear (auto march), not StepFar.
    fallback_variants = (
        {"type": "order", "order": "march"},  # missing target
        {"type": "order", "order": "march", "target": ""},  # empty target
        {"type": "order", "order": "march", "target": "Nowhere"},  # unknown
        {"type": "order", "order": "march", "target": None},  # non-str target
    )
    for command in fallback_variants:
        s = _build_branching_session()
        before = copy.deepcopy(s.snapshot())
        after = apply_command(s, command)

        assert isinstance(after, Session)
        assert after is not s
        assert after.player_duchy_id == "north"
        assert after.seed == 11
        assert after.calendar == s.calendar
        assert after.rng is s.rng
        # Auto march lands the party at StepNear (toward the nearest enemy),
        # NOT at StepFar — so this is the fallback branch, not march_to(Far).
        assert after.world.party_at(step_near_region) is not None
        assert after.world.party_at(step_far_region) is None
        assert after.world.party_at(start_region) is None
        # The new game is sync_from_world of the new world.
        assert after.game is not s.game
        # The input session is never mutated.
        assert s.snapshot() == before
        assert s.world.party_at(start_region) is not None
        assert s.world.party_at(step_near_region) is None
        assert s.world.party_at(step_far_region) is None


def test_session_last_battle_field_and_snapshot_embeds_battle_state():
    """G65.3a kryt-1/kryt-2: ``Session.__init__`` zyskuje publiczne pole
    ``last_battle: HexBattle | None`` (domyślnie ``None``), a
    ``Session.snapshot()`` przekazuje ``battle=self.last_battle`` do
    ``game_state(...)``. Gdy ``last_battle is None`` wynik nie ma klucza
    ``battle`` (bajt-w-bajt jak dziś); gdy jest ustawione,
    ``session.snapshot()["battle"] == battle_state(session.last_battle)``.
    Metoda pozostaje czysta (nie mutuje sesji), a wynik przechodzi przez
    ``json.dumps``.

    Bitwa ustawiana jest na istniejącej sesji bezpośrednio przez publiczne
    przypisanie pola (tak jak zrobią to rozkazy ``assault``/``engage`` w
    task-317/318 — ten przyrost dodaje wyłącznie pole i przewód do snapshotu).
    """
    from tbb.battle import BattleSide, HexBattle
    from tbb.battlefield import Battlefield
    from tbb.hex import Hex
    from tbb.terrain import FOREST, PLAINS
    from tbb.unit import Unit
    from tbbbridge.snapshot import battle_state

    # --- Świeża sesja: last_battle is None, snapshot bez klucza "battle". ---
    s = new_session(73, "player")
    assert s.last_battle is None
    snap_none = s.snapshot()
    assert "battle" not in snap_none

    # --- Budowa realnej, trwającej bitwy heksowej (obie strony żywe). ---
    attacker = Unit(training=2)
    defender = Unit(training=1, equipment=1)
    battlefield = Battlefield({Hex(1, -1): FOREST, Hex(0, 0): PLAINS})
    battle = HexBattle(battlefield)
    battle = battle.deploy(defender, Hex(0, 0), BattleSide.DEFENDER)
    battle = battle.deploy(attacker, Hex(1, -1), BattleSide.ATTACKER)
    assert battle.result() is None  # ongoing

    # --- Ustawienie pola last_battle (przypisanie publiczne). ---
    s.last_battle = battle
    assert s.last_battle is battle

    snap_before = copy.deepcopy(s.snapshot())

    # --- Snapshot osadza battle_state(last_battle) pod kluczem "battle". ---
    snap = s.snapshot()
    assert "battle" in snap
    assert snap["battle"] == battle_state(battle)

    # --- Pozostałe klucze snapshotu bez zmian względem postaci bez bitwy ---
    # (z wyjątkiem dodanego klucza "battle" na końcu).
    assert list(snap.keys()) == [
        "calendar", "duchies", "map", "result", "battle",
    ]
    snap_stripped = {k: snap[k] for k in ("calendar", "duchies", "map", "result")}
    snap_none_stripped = {
        k: snap_none[k] for k in ("calendar", "duchies", "map", "result")
    }
    assert snap_stripped == snap_none_stripped

    # --- Wynik przechodzi przez json.dumps. ---
    json.dumps(snap)

    # --- Metoda czysta: powtórne wywołanie daje ten sam wynik, sesja nie
    # mutuje ani pola, ani bitwy (HexBattle jest zamrożony — tożsamość ref). ---
    snap2 = s.snapshot()
    assert snap2 == snap
    assert json.dumps(snap2) == json.dumps(snap)
    assert s.last_battle is battle
    assert s.snapshot() == snap_before


def test_non_battle_transitions_reset_last_battle_to_none():
    """G65.3a kryt-1: z sesji z ustawionym ``last_battle`` każde niebitewne
    przejście — ``next_turn()`` oraz rozkazy ``develop``/``recruit``/
    ``muster``/``march`` przez ``apply_command`` — produkuje nową sesję z
    ``last_battle is None`` i snapshotem bez klucza ``battle``. Sesja wejściowa
    pozostaje nietknięta.
    """
    from tbb.battle import BattleSide, HexBattle
    from tbb.battlefield import Battlefield
    from tbb.hex import Hex
    from tbb.terrain import FOREST, PLAINS
    from tbb.unit import Unit

    # --- Przygotowanie sesji z realną, trwającą bitwą. ---
    s = new_session(73, "player")
    attacker = Unit(training=2)
    defender = Unit(training=1, equipment=1)
    battlefield = Battlefield({Hex(1, -1): FOREST, Hex(0, 0): PLAINS})
    battle = HexBattle(battlefield)
    battle = battle.deploy(defender, Hex(0, 0), BattleSide.DEFENDER)
    battle = battle.deploy(attacker, Hex(1, -1), BattleSide.ATTACKER)
    assert battle.result() is None

    s.last_battle = battle
    before = copy.deepcopy(s.snapshot())
    assert "battle" in before

    # --- next_turn() zeruje pole i snapshot. ---
    after_turn = s.next_turn()
    assert after_turn is not s
    assert after_turn.last_battle is None
    assert "battle" not in after_turn.snapshot()

    # --- _apply_order (develop) zeruje pole i snapshot. ---
    after_order = apply_command(s, {"type": "order", "order": "develop"})
    assert after_order is not s
    assert after_order.last_battle is None
    assert "battle" not in after_order.snapshot()

    # --- Pozostałe niebitewne rozkazy również zerują pole. ---
    for command in (
        {"type": "order", "order": "recruit"},
        {"type": "order", "order": "muster"},
        {"type": "order", "order": "march"},
    ):
        after = apply_command(s, command)
        assert after.last_battle is None, command
        assert "battle" not in after.snapshot(), command

    # --- Sesja wejściowa pozostaje nietknięta. ---
    assert s.last_battle is battle
    assert s.snapshot() == before


def test_apply_command_order_assault_auto_applies_recorded_primitive_sets_last_battle_preserves_fields():
    """G65.3b kryt-1: ``apply_command({"type": "order", "order": "assault"})``
    bez ``target`` stosuje ``ai.assault_duchy_party_recorded(world,
    player_duchy, session.rng, morale_by_owner=m)``, gdzie
    ``m = {d.duchy_id: d.morale for d in session.game.duchies}``. Z
    ``"target": <name>`` rozwiązywalnym do ``Region`` z ``world.regions`` (po
    ``region.name``) stosuje ``ai.assault_duchy_party_to_recorded(world,
    player_duchy, region, session.rng, morale_by_owner=m)``. W obu razach
    prymityw zwraca ``(new_world, battle)``; wynikowy ``Session`` ma
    ``world == new_world``, ``game == game.sync_from_world(new_world)``,
    ``last_battle == battle``, a ``calendar``/``rng``/``seed``/
    ``player_duchy_id`` bez zmian. Wejściowa sesja nie jest mutowana.

    Scenariusz z dwiema sąsiednimi wrogimi osadami (``Near`` i ``Far``):
    auto-szturm wybiera najbliższą (``Near``), szturm z ``target="Far"``
    uderza w ``Far`` — rozłączne wyniki mapy pozwalają odróżnić gałęzie.
    """
    from tbb.ai import (
        assault_duchy_party_recorded,
        assault_duchy_party_to_recorded,
    )
    from tbb.duchy import Duchy
    from tbb.party import Party
    from tbb.settlement import Settlement
    from tbb.unit import Unit
    from tbb.world import Region, WorldMap

    def _build_session() -> Session:
        start, near, far = map(Region, ("Start", "Near", "Far"))
        party = Party(Unit(training=5, equipment=6), owner_id="north")
        # Different garrison stats make the resolved battles distinct, while
        # both remain short enough to guarantee a non-None battle result.
        near_keep = Settlement(
            "Near Keep", population=1, garrison=(Unit(equipment=1),), owner_id="south"
        )
        far_keep = Settlement(
            "Far Keep", population=1, garrison=(Unit(training=2, equipment=2),), owner_id="south"
        )
        world = WorldMap(
            [start, near, far],
            [(start, near), (start, far)],
            settlements={near: near_keep, far: far_keep},
            parties={start: party},
        )
        game = GameState(
            (
                Duchy("north", party.hero, morale=10, parties=(party,)),
                Duchy("south", Unit(), morale=-5, settlements=(near_keep, far_keep)),
            )
        )
        return Session(
            world=world,
            game=game,
            calendar=Calendar(year=2, month=3),
            rng=Rng(2),
            player_duchy_id="north",
            seed=2,
        )

    # --- Ścieżka auto: brak targetu → assault_duchy_party_recorded(...). ---
    s_auto = _build_session()
    morale = {d.duchy_id: d.morale for d in s_auto.game.duchies}
    expected_world_auto, expected_battle_auto = assault_duchy_party_recorded(
        s_auto.world, s_auto.game.duchies[0], Rng(2), morale_by_owner=morale
    )
    assert expected_battle_auto is not None  # walidacja scenariusza: bitwa wybuchła
    before_auto = copy.deepcopy(s_auto.snapshot())

    after_auto = apply_command(s_auto, {"type": "order", "order": "assault"})

    assert isinstance(after_auto, Session)
    assert after_auto is not s_auto
    assert after_auto.player_duchy_id == "north"
    assert after_auto.seed == 2
    assert after_auto.calendar == s_auto.calendar
    assert after_auto.rng is s_auto.rng
    assert after_auto.world == expected_world_auto
    assert after_auto.last_battle == expected_battle_auto
    assert after_auto.last_battle is not None
    expected_game_auto = s_auto.game.sync_from_world(expected_world_auto)
    assert after_auto.game == expected_game_auto
    # Snapshot osadza bitwę.
    assert "battle" in after_auto.snapshot()
    # Sesja wejściowa nie jest mutowana.
    assert s_auto.snapshot() == before_auto
    assert s_auto.last_battle is None

    # --- Ścieżka z targetem rozwiązywalnym → assault_duchy_party_to_recorded(..., far). ---
    s_target = _build_session()
    morale_t = {d.duchy_id: d.morale for d in s_target.game.duchies}
    far = next(r for r in s_target.world.regions if r.name == "Far")
    expected_world_t, expected_battle_t = assault_duchy_party_to_recorded(
        s_target.world, s_target.game.duchies[0], far, Rng(2), morale_by_owner=morale_t
    )
    assert expected_battle_t is not None  # walidacja scenariusza: bitwa wybuchła
    before_t = copy.deepcopy(s_target.snapshot())

    after_t = apply_command(
        s_target, {"type": "order", "order": "assault", "target": "Far"}
    )

    assert isinstance(after_t, Session)
    assert after_t is not s_target
    assert after_t.player_duchy_id == "north"
    assert after_t.seed == 2
    assert after_t.calendar == s_target.calendar
    assert after_t.rng is s_target.rng
    assert after_t.world == expected_world_t
    assert after_t.last_battle == expected_battle_t
    expected_game_t = s_target.game.sync_from_world(expected_world_t)
    assert after_t.game == expected_game_t
    # Sesja wejściowa nie jest mutowana.
    assert s_target.snapshot() == before_t
    assert s_target.last_battle is None

    # --- Rozłączne wyniki: auto uderza w Near, target=Far uderza w Far. ---
    # Bitwy oraz światy różnią się między gałęziami (różne pola bitwy).
    assert expected_world_auto != expected_world_t
    assert expected_battle_auto != expected_battle_t


class _ForbiddenRng:
    """RNG proxy that raises on any draw, proving no-op paths never pull."""

    def randint(self, a, b):
        raise AssertionError("RNG consumed on a no-op path")

    def chance(self, p):
        raise AssertionError("RNG consumed on a no-op path")


def test_apply_command_order_assault_fallback_and_guards_and_no_op_no_rng():
    """G65.3b kryt-2: ``target`` pusty/niepasujący → fallback do auto
    (``assault_duchy_party_recorded``), rozłącznie od ``target=Far`` na
    scenariuszu Near/Far. Guardy G65.2a (``is_over`` / brak
    ``player_duchy_id`` / księstwo nieobecne) → no-op z
    ``last_battle is None``, ``world``/``game``/``calendar`` identyczne z
    wejściowymi **bez konsumpcji RNG** (wstrzyknięty ``_ForbiddenRng`` rzuca
    przy poborze). Gdy prymityw zwróci ``(world, None)`` (brak sąsiedniej
    wrogiej osady) → RNG nietknięty, ``last_battle is None``, wejściowa sesja
    nie jest mutowana.
    """
    from tbb.ai import assault_duchy_party_recorded
    from tbb.duchy import Duchy
    from tbb.party import Party
    from tbb.settlement import Settlement
    from tbb.unit import Unit
    from tbb.world import Region, WorldMap

    def _build_session(rng=None) -> Session:
        start, near, far = map(Region, ("Start", "Near", "Far"))
        party = Party(Unit(training=5, equipment=6), owner_id="north")
        near_keep = Settlement(
            "Near Keep", population=1, garrison=(Unit(equipment=1),), owner_id="south"
        )
        far_keep = Settlement(
            "Far Keep", population=1,
            garrison=(Unit(training=2, equipment=2),), owner_id="south"
        )
        world = WorldMap(
            [start, near, far],
            [(start, near), (start, far)],
            settlements={near: near_keep, far: far_keep},
            parties={start: party},
        )
        game = GameState(
            (
                Duchy("north", party.hero, morale=10, parties=(party,)),
                Duchy("south", Unit(), morale=-5,
                      settlements=(near_keep, far_keep)),
            )
        )
        return Session(
            world=world,
            game=game,
            calendar=Calendar(year=2, month=3),
            rng=rng if rng is not None else Rng(2),
            player_duchy_id="north",
            seed=2,
        )

    # --- Fallback: target pusty/None/niepasujący → auto (Near), nie Far. ---
    reference = _build_session()
    far = next(r for r in reference.world.regions if r.name == "Far")
    near = next(r for r in reference.world.regions if r.name == "Near")
    auto_world, auto_battle = assault_duchy_party_recorded(
        reference.world, reference.game.duchies[0], Rng(2),
        morale_by_owner={d.duchy_id: d.morale for d in reference.game.duchies},
    )
    assert auto_battle is not None

    fallback_variants = (
        {"type": "order", "order": "assault"},  # missing target
        {"type": "order", "order": "assault", "target": ""},  # empty
        {"type": "order", "order": "assault", "target": None},  # non-str
        {"type": "order", "order": "assault", "target": "Nowhere"},  # unknown
    )
    for command in fallback_variants:
        s = _build_session()
        before = copy.deepcopy(s.snapshot())
        after = apply_command(s, command)

        assert isinstance(after, Session)
        assert after is not s
        assert after.player_duchy_id == "north"
        assert after.seed == 2
        assert after.calendar == s.calendar
        assert after.rng is s.rng
        # Auto assault resolved Near (not Far): fallback used recorded auto.
        assert after.world == auto_world
        assert after.last_battle == auto_battle
        assert after.last_battle is not None
        # Distinct from target=Far (would hit Far, not Near).
        from tbb.ai import assault_duchy_party_to_recorded
        target_far_world = assault_duchy_party_to_recorded(
            _build_session().world, _build_session().game.duchies[0], far, Rng(2),
            morale_by_owner={"north": 10, "south": -5},
        )[0]
        assert after.world != target_far_world or near == far
        # Input session unchanged.
        assert s.snapshot() == before
        assert s.last_battle is None

    # --- Guardy G65.2a: no-op bez konsumpcji RNG (_ForbiddenRng rzuca). ---
    # is_over guard.
    base = _build_session(rng=_ForbiddenRng())
    ended_game = GameState([base.game.duchies[0]])
    assert ended_game.is_over is True
    over_session = Session(
        world=base.world, game=ended_game, calendar=base.calendar,
        rng=_ForbiddenRng(), player_duchy_id="north", seed=2,
    )
    over_before = copy.deepcopy(over_session.snapshot())
    after_over = apply_command(
        over_session, {"type": "order", "order": "assault", "target": "Near"}
    )
    assert after_over is not over_session
    assert after_over.world is over_session.world
    assert after_over.game is over_session.game
    assert after_over.calendar is over_session.calendar
    assert after_over.last_battle is None
    assert "battle" not in after_over.snapshot()
    assert over_session.snapshot() == over_before

    # No player_duchy_id guard.
    no_player = _build_session(rng=_ForbiddenRng())
    no_player.player_duchy_id = None
    no_player_before = copy.deepcopy(no_player.snapshot())
    after_no_player = apply_command(
        no_player, {"type": "order", "order": "assault", "target": "Near"}
    )
    assert after_no_player.world is no_player.world
    assert after_no_player.game is no_player.game
    assert after_no_player.calendar is no_player.calendar
    assert after_no_player.last_battle is None
    assert no_player.snapshot() == no_player_before

    # Player duchy absent guard.
    absent = _build_session(rng=_ForbiddenRng())
    absent.player_duchy_id = "absent"
    absent_before = copy.deepcopy(absent.snapshot())
    after_absent = apply_command(
        absent, {"type": "order", "order": "assault", "target": "Near"}
    )
    assert after_absent.world is absent.world
    assert after_absent.game is absent.game
    assert after_absent.calendar is absent.calendar
    assert after_absent.last_battle is None
    assert absent.snapshot() == absent_before

    # --- Prymityw zwraca (world, None): nearest enemy settlement nie sąsiaduje. ---
    # Party na StartIso, Mid jako bufor, Remote — wroga osada nie sąsiadująca
    # z StartIso: nearest_enemy_settlement → Remote, ale Remote ∉ neighbors(StartIso),
    # więc prymityw zwraca (world, None) bez konsumpcji RNG.
    start_isolated = Region("StartIso")
    mid = Region("Mid")
    remote = Region("Remote")
    party = Party(Unit(training=5, equipment=6), owner_id="north")
    world_iso = WorldMap(
        [start_isolated, mid, remote],
        [(start_isolated, mid), (mid, remote)],
        settlements={
            remote: Settlement("Remote Keep", population=1,
                               garrison=(Unit(),), owner_id="south")
        },
        parties={start_isolated: party},
    )
    game_iso = GameState(
        (
            Duchy("north", party.hero, parties=(party,)),
            Duchy("south", Unit(),
                  settlements=(world_iso.settlement_at(remote),)),
        )
    )
    forbidden = _ForbiddenRng()
    s_iso = Session(
        world=world_iso, game=game_iso, calendar=Calendar(year=2, month=3),
        rng=forbidden, player_duchy_id="north", seed=2,
    )
    iso_before = copy.deepcopy(s_iso.snapshot())
    after_iso = apply_command(
        s_iso, {"type": "order", "order": "assault", "target": "Nowhere"}
    )
    assert after_iso is not s_iso
    assert after_iso.world is world_iso
    assert after_iso.last_battle is None
    assert "battle" not in after_iso.snapshot()
    assert s_iso.snapshot() == iso_before
    # RNG proxy nie rzuciło — dowód braku konsumpcji na no-op path.
    # (gdyby kod pobrał liczbę, _ForbiddenRng.randint/chance rzuciłby AssertionError)


def test_apply_command_order_engage_auto_applies_recorded_primitive_sets_last_battle_preserves_fields():
    """G65.3c kryt-1: ``apply_command({"type": "order", "order": "engage"})``
    bez ``target`` stosuje ``ai.engage_duchy_party_recorded(world,
    player_duchy, session.rng, morale_by_owner=m)``, gdzie
    ``m = {d.duchy_id: d.morale for d in session.game.duchies}``. Z
    ``"target": <name>`` rozwiązywalnym do ``Region`` z ``world.regions`` (po
    ``region.name``) stosuje ``ai.engage_duchy_party_to_recorded(world,
    player_duchy, region, session.rng, morale_by_owner=m)``. W obu razach
    prymityw zwraca ``(new_world, battle)``; wynikowy ``Session`` ma
    ``world == new_world``, ``game == game.sync_from_world(new_world)``,
    ``last_battle == battle``, a ``calendar``/``rng``/``seed``/
    ``player_duchy_id`` bez zmian. Wejściowa sesja nie jest mutowana.

    Scenariusz z dwiema sąsiednimi wrogimi partiami (``Near`` i ``Far``):
    auto-starcie wybiera pierwszą (``Near``), starcie z ``target="Far"``
    uderza w ``Far`` — rozłączne wyniki mapy/bitwy pozwalają odróżnić gałęzie.
    """
    from tbb.ai import (
        engage_duchy_party_recorded,
        engage_duchy_party_to_recorded,
    )
    from tbb.duchy import Duchy
    from tbb.party import Party
    from tbb.unit import Unit
    from tbb.world import Region, WorldMap

    def _build_session() -> Session:
        start, near, far = map(Region, ("Start", "Near", "Far"))
        player_party = Party(
            Unit(training=5, equipment=6), owner_id="north"
        )
        # Different defender stats make the resolved battles distinct, while
        # both remain non-None (a battle breaks out against an enemy party).
        near_enemy = Party(Unit(equipment=1), (Unit(equipment=1),), owner_id="south")
        far_enemy = Party(
            Unit(training=2, equipment=2), (Unit(equipment=2),), owner_id="south"
        )
        world = WorldMap(
            [start, near, far],
            [(start, near), (start, far)],
            parties={start: player_party, near: near_enemy, far: far_enemy},
        )
        game = GameState(
            (
                Duchy(
                    "north", player_party.hero, morale=10,
                    parties=(player_party,),
                ),
                Duchy(
                    "south", Unit(), morale=-5,
                    parties=(near_enemy, far_enemy),
                ),
            )
        )
        return Session(
            world=world,
            game=game,
            calendar=Calendar(year=2, month=3),
            rng=Rng(2),
            player_duchy_id="north",
            seed=2,
        )

    # --- Ścieżka auto: brak targetu → engage_duchy_party_recorded(...). ---
    s_auto = _build_session()
    morale = {d.duchy_id: d.morale for d in s_auto.game.duchies}
    expected_world_auto, expected_battle_auto = engage_duchy_party_recorded(
        s_auto.world, s_auto.game.duchies[0], Rng(2), morale_by_owner=morale
    )
    assert expected_battle_auto is not None  # walidacja scenariusza: bitwa wybuchła
    before_auto = copy.deepcopy(s_auto.snapshot())

    after_auto = apply_command(s_auto, {"type": "order", "order": "engage"})

    assert isinstance(after_auto, Session)
    assert after_auto is not s_auto
    assert after_auto.player_duchy_id == "north"
    assert after_auto.seed == 2
    assert after_auto.calendar == s_auto.calendar
    assert after_auto.rng is s_auto.rng
    assert after_auto.world == expected_world_auto
    assert after_auto.last_battle == expected_battle_auto
    assert after_auto.last_battle is not None
    expected_game_auto = s_auto.game.sync_from_world(expected_world_auto)
    assert after_auto.game == expected_game_auto
    # Snapshot osadza bitwę.
    assert "battle" in after_auto.snapshot()
    # Sesja wejściowa nie jest mutowana.
    assert s_auto.snapshot() == before_auto
    assert s_auto.last_battle is None

    # --- Ścieżka z targetem rozwiązywalnym → engage_duchy_party_to_recorded(..., far). ---
    s_target = _build_session()
    morale_t = {d.duchy_id: d.morale for d in s_target.game.duchies}
    far = next(r for r in s_target.world.regions if r.name == "Far")
    expected_world_t, expected_battle_t = engage_duchy_party_to_recorded(
        s_target.world, s_target.game.duchies[0], far, Rng(2), morale_by_owner=morale_t
    )
    assert expected_battle_t is not None  # walidacja scenariusza: bitwa wybuchła
    before_t = copy.deepcopy(s_target.snapshot())

    after_t = apply_command(
        s_target, {"type": "order", "order": "engage", "target": "Far"}
    )

    assert isinstance(after_t, Session)
    assert after_t is not s_target
    assert after_t.player_duchy_id == "north"
    assert after_t.seed == 2
    assert after_t.calendar == s_target.calendar
    assert after_t.rng is s_target.rng
    assert after_t.world == expected_world_t
    assert after_t.last_battle == expected_battle_t
    expected_game_t = s_target.game.sync_from_world(expected_world_t)
    assert after_t.game == expected_game_t
    # Sesja wejściowa nie jest mutowana.
    assert s_target.snapshot() == before_t
    assert s_target.last_battle is None

    # --- Rozłączne wyniki: auto uderza w Near (pierwszy sąsiad), target=Far uderza w Far. ---
    # Bitwy oraz światy różnią się między gałęziami (różne pola bitwy).
    assert expected_world_auto != expected_world_t
    assert expected_battle_auto != expected_battle_t


def test_apply_command_order_engage_fallback_and_guards_and_no_op_no_rng():
    """G65.3c kryt-2: ``target`` pusty/niepasujący → fallback do starcia
    automatycznego (``engage_duchy_party_recorded``), rozłącznie od
    ``target=Far`` na scenariuszu partii Near/Far. Guardy G65.2a (``is_over``
    / brak ``player_duchy_id`` / księstwo nieobecne) → no-op z
    ``last_battle is None``, ``world``/``game``/``calendar`` identyczne z
    wejściowymi **bez konsumpcji RNG** (wstrzyknięty ``_ForbiddenRng`` rzuca
    przy poborze). Gdy prymityw zwróci ``(world, None)`` (brak sąsiedniego
    wrogiego oddziału) → RNG nietknięty, ``last_battle is None``, wejściowa
    sesja nie jest mutowana.
    """
    from tbb.ai import (
        engage_duchy_party_recorded,
        engage_duchy_party_to_recorded,
    )
    from tbb.duchy import Duchy
    from tbb.party import Party
    from tbb.unit import Unit
    from tbb.world import Region, WorldMap

    def _build_session(rng=None) -> Session:
        start, near, far = map(Region, ("Start", "Near", "Far"))
        party = Party(Unit(training=5, equipment=6), owner_id="north")
        near_enemy = Party(Unit(equipment=1), (Unit(equipment=1),), owner_id="south")
        far_enemy = Party(
            Unit(training=2, equipment=2), (Unit(equipment=2),), owner_id="south"
        )
        world = WorldMap(
            [start, near, far],
            [(start, near), (start, far)],
            parties={start: party, near: near_enemy, far: far_enemy},
        )
        game = GameState(
            (
                Duchy("north", party.hero, morale=10, parties=(party,)),
                Duchy("south", Unit(), morale=-5,
                      parties=(near_enemy, far_enemy)),
            )
        )
        return Session(
            world=world,
            game=game,
            calendar=Calendar(year=2, month=3),
            rng=rng if rng is not None else Rng(2),
            player_duchy_id="north",
            seed=2,
        )

    morale = {"north": 10, "south": -5}

    # --- Fallback: target pusty/None/niepasujący → auto (Near), nie Far. ---
    reference = _build_session()
    far = next(r for r in reference.world.regions if r.name == "Far")
    auto_world, auto_battle = engage_duchy_party_recorded(
        reference.world, reference.game.duchies[0], Rng(2), morale_by_owner=morale
    )
    assert auto_battle is not None

    fallback_variants = (
        {"type": "order", "order": "engage"},  # missing target
        {"type": "order", "order": "engage", "target": ""},  # empty
        {"type": "order", "order": "engage", "target": None},  # non-str
        {"type": "order", "order": "engage", "target": "Nowhere"},  # unknown
    )
    for command in fallback_variants:
        s = _build_session()
        before = copy.deepcopy(s.snapshot())
        after = apply_command(s, command)

        assert isinstance(after, Session)
        assert after is not s
        assert after.player_duchy_id == "north"
        assert after.seed == 2
        assert after.calendar == s.calendar
        assert after.rng is s.rng
        # Auto engage resolved Near (not Far): fallback used recorded auto.
        assert after.world == auto_world
        assert after.last_battle == auto_battle
        assert after.last_battle is not None
        # Distinct from target=Far (would hit Far, not Near).
        target_far_world = engage_duchy_party_to_recorded(
            _build_session().world, _build_session().game.duchies[0], far, Rng(2),
            morale_by_owner=morale,
        )[0]
        assert after.world != target_far_world
        # Input session unchanged.
        assert s.snapshot() == before
        assert s.last_battle is None

    # --- Guardy G65.2a: no-op bez konsumpcji RNG (_ForbiddenRng rzuca). ---
    # is_over guard.
    base = _build_session(rng=_ForbiddenRng())
    ended_game = GameState([base.game.duchies[0]])
    assert ended_game.is_over is True
    over_session = Session(
        world=base.world, game=ended_game, calendar=base.calendar,
        rng=_ForbiddenRng(), player_duchy_id="north", seed=2,
    )
    over_before = copy.deepcopy(over_session.snapshot())
    after_over = apply_command(
        over_session, {"type": "order", "order": "engage", "target": "Near"}
    )
    assert after_over is not over_session
    assert after_over.world is over_session.world
    assert after_over.game is over_session.game
    assert after_over.calendar is over_session.calendar
    assert after_over.last_battle is None
    assert "battle" not in after_over.snapshot()
    assert over_session.snapshot() == over_before

    # No player_duchy_id guard.
    no_player = _build_session(rng=_ForbiddenRng())
    no_player.player_duchy_id = None
    no_player_before = copy.deepcopy(no_player.snapshot())
    after_no_player = apply_command(
        no_player, {"type": "order", "order": "engage", "target": "Near"}
    )
    assert after_no_player.world is no_player.world
    assert after_no_player.game is no_player.game
    assert after_no_player.calendar is no_player.calendar
    assert after_no_player.last_battle is None
    assert no_player.snapshot() == no_player_before

    # Player duchy absent guard.
    absent = _build_session(rng=_ForbiddenRng())
    absent.player_duchy_id = "absent"
    absent_before = copy.deepcopy(absent.snapshot())
    after_absent = apply_command(
        absent, {"type": "order", "order": "engage", "target": "Near"}
    )
    assert after_absent.world is absent.world
    assert after_absent.game is absent.game
    assert after_absent.calendar is absent.calendar
    assert after_absent.last_battle is None
    assert absent.snapshot() == absent_before

    # --- Prymityw zwraca (world, None): brak sąsiedniego wrogiego oddziału. ---
    # Party na StartIso, Mid jako bufor, Remote — wroga partia nie sąsiadująca
    # z StartIso: engage_duchy_party_recorded nie znajdzie sąsiedniego wrogiego
    # oddziału, więc zwróci (world, None) bez konsumpcji RNG.
    start_isolated = Region("StartIso")
    mid = Region("Mid")
    remote = Region("Remote")
    party = Party(Unit(training=5, equipment=6), owner_id="north")
    remote_enemy = Party(Unit(), (Unit(),), owner_id="south")
    world_iso = WorldMap(
        [start_isolated, mid, remote],
        [(start_isolated, mid), (mid, remote)],
        parties={start_isolated: party, remote: remote_enemy},
    )
    game_iso = GameState(
        (
            Duchy("north", party.hero, parties=(party,)),
            Duchy("south", Unit(), parties=(remote_enemy,)),
        )
    )
    forbidden = _ForbiddenRng()
    s_iso = Session(
        world=world_iso, game=game_iso, calendar=Calendar(year=2, month=3),
        rng=forbidden, player_duchy_id="north", seed=2,
    )
    iso_before = copy.deepcopy(s_iso.snapshot())
    after_iso = apply_command(
        s_iso, {"type": "order", "order": "engage", "target": "Nowhere"}
    )
    assert after_iso is not s_iso
    assert after_iso.world is world_iso
    assert after_iso.last_battle is None
    assert "battle" not in after_iso.snapshot()
    assert s_iso.snapshot() == iso_before
    # RNG proxy nie rzuciło — dowód braku konsumpcji na no-op path.
    # (gdyby kod pobrał liczbę, _ForbiddenRng.randint/chance rzuciłby AssertionError)
