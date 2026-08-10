"""Uchwyt sesji gry dla mostu poleceń Godot↔rdzeń."""

from dataclasses import dataclass, field, replace
from types import MappingProxyType
from typing import Mapping

import tbb.ai as ai
from tbb.battle import BattleSide, HexBattle
from tbb.driver import resolve_hero_survival, run_headless_game
from tbb.duchy import Duchy
from tbb.game import create_headless_game, GameState
from tbb.hex import Hex
from tbb.rng import Rng
from tbb.turn import Calendar
from tbb.world import Region, WorldMap

from tbbbridge.snapshot import game_state


_ORDER_TRANSITIONS = {
    "develop": ai.develop_duchy_settlement,
    "recruit": ai.recruit_duchy_unit,
    "muster": ai.muster_duchy_party,
    "reinforce": ai.reinforce_duchy_party,
    "move": None,  # handled specially because of the required target
    "march": None,  # handled specially because of optional target
}
_ECONOMIC_ORDERS = ("develop", "recruit", "muster")
_BATTLE_ORDERS = ("assault", "engage")
_MISSING_TARGET = object()


@dataclass(frozen=True)
class PendingBattle:
    """Bitwa gracza pauzująca w sesji przed rozstrzygnięciem (G119.1b).

    Pola:
      battle            -> HexBattle w toku (od rozstawienia po kolejne rundy)
      source            -> region wyjściowy atakującego
      target            -> region celu (równy ``source`` przy assault-murze)
      kind              -> "party" (engage), "settlement" (assault z sąsiedniego
                           regionu) albo "settlement_at" (assault w miejscu)
      attacker_owner_id -> właściciel atakującego oddziału
      defender_owner_id -> właściciel broniącej partii/osady
      attack_targets    -> jednorazowe intencje celu dla następnej rundy
    """

    battle: HexBattle
    source: Region
    target: Region
    kind: str
    attacker_owner_id: str
    defender_owner_id: str
    attack_targets: Mapping[Hex, Hex] = field(default_factory=dict)


def _find_region_by_name(world: WorldMap, name: object) -> object | None:
    """Return the Region from ``world.regions`` whose name equals ``name``.

    ``None`` when ``name`` is missing, empty, or does not match any region.
    """
    if not isinstance(name, str) or not name:
        return None
    for region in world.regions:
        if region.name == name:
            return region
    return None


def _apply_march_order(world: WorldMap, duchy: Duchy, target_name: str | None) -> WorldMap:
    """Apply the player ``march`` order.

    An explicit, resolvable ``target_name`` routes to
    ``ai.march_duchy_party_to``; anything else falls back to the automatic
    ``ai.march_duchy_party``.
    """
    target = _find_region_by_name(world, target_name)
    if target is not None:
        return ai.march_duchy_party_to(world, duchy, target)
    return ai.march_duchy_party(world, duchy)


def _apply_move_order(world: WorldMap, duchy: Duchy, target_name: str | None) -> WorldMap:
    """Apply one safe player step to an explicitly named region.

    An absent or unknown target is a no-op; unlike ``march``, ``move`` never
    falls back to an automatic destination.
    """
    target = _find_region_by_name(world, target_name)
    if target is None:
        return world
    return ai.move_duchy_party_to_adjacent(world, duchy, target)


def _apply_economic_order(
    world: WorldMap, duchy: Duchy, target_name: object, transition
) -> WorldMap:
    """Apply an economic order, preserving fallback only for a missing target."""
    if target_name is _MISSING_TARGET:
        return transition(world, duchy)
    target = _find_region_by_name(world, target_name)
    if target is None:
        return world
    return transition(world, duchy, target)


def _morale_by_owner(game: GameState) -> dict[str, int]:
    """Build owner_id → morale from the current game duchies."""
    return {d.duchy_id: d.morale for d in game.duchies}


def _pending_battle_morale(session: "Session", pending: PendingBattle) -> tuple[int, int]:
    """Return attacker and defender morale for one pending-battle step."""
    morale = _morale_by_owner(session.game)
    return (
        morale.get(pending.attacker_owner_id, 0),
        morale.get(pending.defender_owner_id, 0),
    )


def _pending_battle_context(
    world: WorldMap, started: tuple[HexBattle, Region, Region], kind: str
) -> PendingBattle:
    """Build the paused-battle context from a started battle."""
    battle, source, target = started
    defender_owner_id = (
        world.party_at(target).owner_id
        if kind == "party"
        else world.settlement_at(target).owner_id
    )
    battle_kind = (
        "settlement_at" if kind == "settlement" and source == target else kind
    )
    return PendingBattle(
        battle=battle,
        source=source,
        target=target,
        kind=battle_kind,
        attacker_owner_id=world.party_at(source).owner_id,
        defender_owner_id=defender_owner_id,
    )


def _parse_battle_hex(value: object) -> Hex | None:
    """Return a public battle hex, or ``None`` for malformed input."""
    if not isinstance(value, dict):
        return None
    q, r = value.get("q"), value.get("r")
    if not isinstance(q, int) or isinstance(q, bool):
        return None
    if not isinstance(r, int) or isinstance(r, bool):
        return None
    return Hex(q, r)


def _battle_target_reason(session: "Session", command: dict) -> str | None:
    """Return a user-facing refusal reason for a battle-target command."""
    pending = session.pending_battle
    if pending is None:
        return "brak bitwy w toku"

    attacker = _parse_battle_hex(command.get("attacker"))
    if attacker is None:
        return "nieprawidłowy heks atakującego"
    target = _parse_battle_hex(command.get("target"))
    if target is None:
        return "nieprawidłowy heks celu"

    unit = pending.battle.unit_at(attacker)
    if (
        unit is None
        or pending.battle.side_at(attacker) is not BattleSide.ATTACKER
        or pending.battle.current_hp_at(attacker) == 0
        or unit.stunned
    ):
        return "brak aktywnej jednostki atakującej"

    target_unit = pending.battle.unit_at(target)
    if (
        target_unit is None
        or pending.battle.side_at(target) is not BattleSide.DEFENDER
        or pending.battle.current_hp_at(target) == 0
        or target_unit.stunned
    ):
        return "cel nie jest aktywnym wrogiem"
    return None


def _merge_battle_target(
    pending: PendingBattle, attacker: Hex, target: Hex
) -> PendingBattle:
    """Add one target while preserving intents for other attackers."""
    attack_targets = dict(pending.attack_targets)
    attack_targets[attacker] = target
    return replace(
        pending,
        attack_targets=MappingProxyType(attack_targets),
    )


def _set_battle_target(session: "Session", command: dict) -> "Session":
    """Record one valid target without advancing or mutating the battle."""
    if _battle_target_reason(session, command) is not None:
        return session
    pending = session.pending_battle
    attacker = _parse_battle_hex(command.get("attacker"))
    target = _parse_battle_hex(command.get("target"))
    # Validation above guarantees all three values are present.
    return session._derive(
        session.world,
        session.game,
        session.calendar,
        pending_battle=_merge_battle_target(pending, attacker, target),
    )


def _apply_pending_battle_result(session: Session, resolved: HexBattle) -> Session:
    """Apply a resolved paused battle to the world with the existing rules.

    Uses the same ``apply_*_battle_result`` transition the former
    auto-resolution used, then the shared hero-survival and game-sync step.
    """
    pending = session.pending_battle
    if pending.kind == "party":
        new_world = session.world.apply_party_battle_result(
            pending.source, pending.target, resolved.result(), battle=resolved
        )
    elif pending.kind == "settlement":
        new_world = session.world.apply_settlement_battle_result(
            pending.source, pending.target, resolved.result(), battle=resolved
        )
    else:
        new_world = session.world.apply_settlement_battle_result_at(
            pending.source, resolved.result(), battle=resolved
        )
    player_duchy = _resolve_player_duchy(session)
    return _after_player_world_change(
        session, player_duchy, new_world, last_battle=resolved
    )


class Session:
    """Uchwyt sesji trzymający stan gry i RNG współdzielony z driverem.

    Pola są publiczne do odczytu:
      world            -> WorldMap
      game             -> GameState
      calendar         -> Calendar
      rng              -> Rng
      player_duchy_id  -> str | None
      seed             -> int
      last_battle      -> HexBattle | None
      pending_battle   -> PendingBattle | None
    """

    def __init__(
        self,
        world: WorldMap,
        game: GameState,
        calendar: Calendar,
        rng: Rng,
        player_duchy_id: str | None,
        seed: int,
        last_battle: HexBattle | None = None,
        pending_battle: PendingBattle | None = None,
    ) -> None:
        self.world = world
        self.game = game
        self.calendar = calendar
        self.rng = rng
        self.player_duchy_id = player_duchy_id
        self.seed = seed
        self.last_battle = last_battle
        self.pending_battle = pending_battle

    def snapshot(self) -> dict:
        """Zwróć json-serializowalny snapshot stanu sesji.

        Nie mutuje sesji. Deleguje do `tbbbridge.snapshot.game_state`.
        Bitwa pauzująca (`pending_battle`) ma pierwszeństwo przed
        `last_battle` — obie nigdy nie są ustawione naraz.
        """
        pending = self.pending_battle
        battle = pending.battle if pending is not None else self.last_battle
        return game_state(
            self.world,
            self.game,
            self.calendar,
            self.player_duchy_id,
            battle=battle,
            attack_targets=pending.attack_targets if pending is not None else None,
        )

    def _derive(
        self,
        world: WorldMap,
        game: GameState,
        calendar: Calendar,
        last_battle: HexBattle | None = None,
        pending_battle: PendingBattle | None = None,
    ) -> "Session":
        """Return a new Session sharing RNG, player id and seed.

        ``last_battle`` and ``pending_battle`` default to ``None`` so
        transitions that do not carry them explicitly reset both fields.
        """
        return Session(
            world=world,
            game=game,
            calendar=calendar,
            rng=self.rng,
            player_duchy_id=self.player_duchy_id,
            seed=self.seed,
            last_battle=last_battle,
            pending_battle=pending_battle,
        )

    def next_turn(self) -> "Session":
        """Zwróć nową sesję po dokładnie jednej turze headless.

        AI gra za wszystkie księstwa poza ``player_duchy_id``; RNG jest
        współdzielony przez referencję i posuwany wewnątrz drivera.
        Gdy gra jest już zakończona, zwracana jest sesja z tymi samymi
        obiektami ``world``/``game``/``calendar`` (no-op).
        """
        if self.game.is_over:
            return self._derive(self.world, self.game, self.calendar)
        new_world, new_game, new_calendar = run_headless_game(
            self.world,
            self.game,
            self.rng,
            max_turns=1,
            calendar=self.calendar,
            player_duchy_id=self.player_duchy_id,
        )
        return self._derive(new_world, new_game, new_calendar)


def new_session(seed: int = 73, player_duchy_id: str | None = "player") -> Session:
    """Utwórz nową sesję ze świeżą grą headless."""
    world, game = create_headless_game()
    return Session(
        world=world,
        game=game,
        calendar=Calendar(),
        rng=Rng(seed),
        player_duchy_id=player_duchy_id,
        seed=seed,
    )


def _resolve_player_duchy(session: Session) -> Duchy | None:
    """Return the player duchy when a player order is legal, else ``None``.

    ``None`` when the game is over, there is no ``player_duchy_id``, or that
    duchy is absent from ``session.game.duchies``.
    """
    if session.game.is_over or session.player_duchy_id is None:
        return None
    return next(
        (
            d
            for d in session.game.duchies
            if d.duchy_id == session.player_duchy_id
        ),
        None,
    )


def _replace_duchy(game: GameState, replacement: Duchy) -> GameState:
    """Return a game with the matching duchy replaced in place."""
    return GameState(
        replacement if duchy.duchy_id == replacement.duchy_id else duchy
        for duchy in game.duchies
    )


def _after_player_world_change(
    session: Session,
    player_duchy: Duchy,
    new_world: WorldMap,
    *,
    last_battle: HexBattle | None = None,
) -> Session:
    """Apply hero survival, duchy replacement, and world sync after a player order.

    Called from both _apply_order and _apply_pending_battle_result after the
    world transition is complete.  Resolves hero survival, replaces the player
    duchy in the game state, syncs the game state to the new world, and derives
    a new session with the updated state.

    ``last_battle`` defaults to ``None`` so transitions that do not carry an
    explicit battle reset the field.
    """
    resolved = resolve_hero_survival(player_duchy, session.world, new_world)
    new_game = _replace_duchy(session.game, resolved).sync_from_world(new_world)
    return session._derive(new_world, new_game, session.calendar, last_battle=last_battle)


def _apply_order(session: Session, transition) -> Session:
    """Apply a no-battle player order transition and return a new Session.

    The transition receives ``(world, player_duchy)`` and returns a new
    ``WorldMap``.  ``resolve_hero_survival`` is applied to the player duchy
    (``player_duchy``, ``session.world``, ``new_world``), the resolved duchy
    replaces the player duchy in ``session.game`` via ``_replace_duchy``, and
    the resulting ``GameState`` is ``sync_from_world`` of the new map.  When
    the order is illegal (game over, no player id, or missing duchy), the
    input world/game/calendar are returned unchanged.

    Calendar, RNG, seed and ``player_duchy_id`` are preserved; the RNG is not
    advanced.  The input session is never mutated.  Any previous ``last_battle``
    is reset to ``None``.
    """
    player_duchy = _resolve_player_duchy(session)
    if player_duchy is None:
        return session._derive(session.world, session.game, session.calendar)
    new_world = transition(session.world, player_duchy)
    return _after_player_world_change(session, player_duchy, new_world)


def _apply_battle_pause_order(
    session: Session,
    target_name: str | None,
    *,
    to_paused,
    auto_paused,
    kind: str,
) -> Session:
    """Pause a player battle order's started battle in the session (G119.1b).

    ``to_paused(world, duchy, region)`` is used when ``target_name`` resolves
    to a Region; otherwise ``auto_paused(world, duchy)`` is used.  Both return
    ``(world, (battle, source, target) | None)``.  A started battle becomes
    ``pending_battle`` without touching the world, game, calendar or RNG and
    without consuming the party's monthly action; no-op paths (and the
    illegal-player guard) return an equivalent unchanged session with no
    battle.  The input session is never mutated.
    """
    player_duchy = _resolve_player_duchy(session)
    if player_duchy is None:
        return session._derive(session.world, session.game, session.calendar)
    target = _find_region_by_name(session.world, target_name)
    if target is not None:
        _, started = to_paused(session.world, player_duchy, target)
    else:
        _, started = auto_paused(session.world, player_duchy)
    if started is None:
        return session._derive(session.world, session.game, session.calendar)
    pending = _pending_battle_context(session.world, started, kind)
    return session._derive(
        session.world,
        session.game,
        session.calendar,
        pending_battle=pending,
    )


def _advance_pending_battle(session: Session) -> Session:
    """Play exactly one round of the paused player battle (G119.1b).

    When no battle is pending the input session is returned unchanged.  The
    round is ``resolve_round(1, session.rng, …)`` with the morale of each
    side's owner read from ``session.game``; the world, game and calendar are
    untouched while the battle stays unresolved.  A round that resolves the
    battle applies its result to the world with the existing rules
    (``_apply_pending_battle_result``) and clears the pause.  The input
    session is never mutated.
    """
    pending = session.pending_battle
    if pending is None:
        return session
    attacker_morale, defender_morale = _pending_battle_morale(session, pending)
    advanced = pending.battle.resolve_round(
        1,
        session.rng,
        attacker_morale=attacker_morale,
        defender_morale=defender_morale,
        attack_targets=pending.attack_targets or None,
    )
    if advanced.result() is None:
        return session._derive(
            session.world,
            session.game,
            session.calendar,
            pending_battle=replace(
                pending, battle=advanced, attack_targets=MappingProxyType({})
            ),
        )
    return _apply_pending_battle_result(session, advanced)


def _auto_resolve_pending_battle(session: Session) -> Session:
    """Resolve the remaining rounds of the paused player battle (G119.1b).

    When no battle is pending the input session is returned unchanged.  The
    pending one-shot ``attack_targets`` are consumed by an initial
    ``resolve_round(1, session.rng, …)``; any remaining rounds then use
    ``auto_resolve(1, session.rng, …)`` from that board.  Both steps use the
    morale of each side's owner read from ``session.game``; the world, game
    and calendar are untouched until resolution.  The resolved battle applies
    its result to the world with the existing rules
    (``_apply_pending_battle_result``) and clears the pause.  If the battle
    remains pending, the consumed target map is cleared.  The input session is
    never mutated.
    """
    pending = session.pending_battle
    if pending is None:
        return session
    attacker_morale, defender_morale = _pending_battle_morale(session, pending)
    resolved = pending.battle
    if pending.attack_targets:
        resolved = resolved.resolve_round(
            1,
            session.rng,
            attacker_morale=attacker_morale,
            defender_morale=defender_morale,
            attack_targets=pending.attack_targets,
        )
    if resolved.result() is None:
        resolved = resolved.auto_resolve(
            1,
            session.rng,
            attacker_morale=attacker_morale,
            defender_morale=defender_morale,
        )
    if resolved.result() is None:
        return session._derive(
            session.world,
            session.game,
            session.calendar,
            pending_battle=replace(
                pending, battle=resolved, attack_targets=MappingProxyType({})
            ),
        )
    return _apply_pending_battle_result(session, resolved)


def apply_command(session: Session, command: dict) -> Session:
    """Dyspozytor poleceń sterujących mostu Godot↔rdzeń.

    Rozpoznawane ``command["type"]``:
      * ``"next_turn"`` — deleguje do ``session.next_turn()``; podczas bitwy
        gracza w toku (``pending_battle``) zwraca wejściową sesję bez zmian.
      * ``"new_game"`` — zwraca świeżą sesję przez ``new_session``;
        domyślny seed pochodzi z ``session.seed``, można nadpisać kluczem
        ``"seed"`` w komendzie. Zachowany jest ``session.player_duchy_id``.
      * ``"order"`` — wydaje rozkaz dla księstwa gracza; rozpoznawane
        ``command["order"]`` to ``"develop"``, ``"recruit"``, ``"muster"``,
        ``"reinforce"``, ``"move"``, ``"march"``, ``"assault"`` oraz
        ``"engage"``. Nieznana nazwa rozkazu podnosi ``ValueError``.
        Podczas bitwy gracza w toku każdy rozkaz zwraca wejściową sesję bez
        zmian (świat, kalendarz i RNG nietknięte). ``"assault"``/``"engage"``,
        które zaczynają bitwę, pauzują ją w ``pending_battle`` zamiast
        rozstrzygać (G119.1b).
      * ``"battle_advance"`` — rozgrywa dokładnie jedną rundę pauzującej
        bitwy gracza; bez bitwy w toku zwraca wejściową sesję bez zmian.
      * ``"battle_target"`` — zapisuje cel aktywnej jednostki atakującej
        w pauzującej bitwie; nie rozgrywa rundy.
      * ``"battle_auto"`` — rozstrzyga pozostałe rundy pauzującej bitwy
        gracza od bieżącej planszy; bez bitwy w toku zwraca wejściową sesję
        bez zmian.

    Brak klucza ``type`` lub nieznana wartość podnoszą ``ValueError``.
    Wejściowa sesja nigdy nie jest mutowana.
    """
    command_type = command.get("type") if isinstance(command, dict) else None
    if command_type == "next_turn":
        if session.pending_battle is not None:
            return session
        return session.next_turn()
    if command_type == "snapshot":
        return session
    if command_type == "battle_advance":
        return _advance_pending_battle(session)
    if command_type == "battle_auto":
        return _auto_resolve_pending_battle(session)
    if command_type == "battle_target":
        return _set_battle_target(session, command)

    if command_type == "new_game":
        if set(command.keys()) - {"type", "seed"}:
            raise ValueError(
                f"new_game command accepts only 'seed' key, got extra keys: "
                f"{sorted(set(command.keys()) - {'type', 'seed'})}"
            )
        seed = command.get("seed", session.seed)
        return new_session(
            seed=seed,
            player_duchy_id=session.player_duchy_id,
        )
    if command_type == "order":
        order = command.get("order")
        if order not in (*_ORDER_TRANSITIONS, *_BATTLE_ORDERS):
            raise ValueError(f"Unknown order: {order!r}")
        if session.pending_battle is not None:
            return session
        if order == "move":
            return _apply_order(
                session,
                lambda world, duchy: _apply_move_order(
                    world, duchy, command.get("target")
                ),
            )
        if order == "march":
            return _apply_order(
                session, lambda world, duchy: _apply_march_order(world, duchy, command.get("target"))
            )
        if order == "assault":
            return _apply_battle_pause_order(
                session,
                command.get("target"),
                to_paused=ai.assault_duchy_party_to_paused,
                auto_paused=ai.assault_duchy_party_paused,
                kind="settlement",
            )
        if order == "engage":
            return _apply_battle_pause_order(
                session,
                command.get("target"),
                to_paused=ai.engage_duchy_party_to_paused,
                auto_paused=ai.engage_duchy_party_paused,
                kind="party",
            )
        if order in _ECONOMIC_ORDERS:
            return _apply_order(
                session,
                lambda world, duchy: _apply_economic_order(
                    world,
                    duchy,
                    command.get("target", _MISSING_TARGET),
                    _ORDER_TRANSITIONS[order],
                ),
            )
        return _apply_order(session, _ORDER_TRANSITIONS[order])
    raise ValueError(f"Unknown command type: {command_type!r}")
