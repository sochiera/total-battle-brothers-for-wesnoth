"""Uchwyt sesji gry dla mostu poleceń Godot↔rdzeń."""

import tbb.ai as ai
from tbb.battle import HexBattle
from tbb.driver import run_headless_game
from tbb.duchy import Duchy
from tbb.game import create_headless_game, GameState
from tbb.rng import Rng
from tbb.turn import Calendar
from tbb.world import WorldMap

from tbbbridge.snapshot import game_state


_ORDER_TRANSITIONS = {
    "develop": ai.develop_duchy_settlement,
    "recruit": ai.recruit_duchy_unit,
    "muster": ai.muster_duchy_party,
    "march": None,  # handled specially because of optional target
}


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


def _morale_by_owner(game: GameState) -> dict[str, int]:
    """Build owner_id → morale from the current game duchies."""
    return {d.duchy_id: d.morale for d in game.duchies}


def _apply_targeted_battle_order(
    world: WorldMap,
    duchy: Duchy,
    rng: Rng,
    target_name: str | None,
    game: GameState,
    *,
    to_recorded,
    auto_recorded,
) -> tuple[WorldMap, HexBattle | None]:
    """Apply a player battle order with an optional explicit target.

    ``to_recorded(world, duchy, region, rng, morale_by_owner=m)`` is used when
    ``target_name`` resolves to a Region; otherwise ``auto_recorded(world,
    duchy, rng, morale_by_owner=m)`` is used.  Both must return ``(new_world,
    battle | None)``.  The shared RNG is advanced only when a battle is
    actually resolved.
    """
    morale = _morale_by_owner(game)
    target = _find_region_by_name(world, target_name)
    if target is not None:
        return to_recorded(world, duchy, target, rng, morale_by_owner=morale)
    return auto_recorded(world, duchy, rng, morale_by_owner=morale)


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
    ) -> None:
        self.world = world
        self.game = game
        self.calendar = calendar
        self.rng = rng
        self.player_duchy_id = player_duchy_id
        self.seed = seed
        self.last_battle = last_battle

    def snapshot(self) -> dict:
        """Zwróć json-serializowalny snapshot stanu sesji.

        Nie mutuje sesji. Deleguje do `tbbbridge.snapshot.game_state`.
        """
        return game_state(
            self.world,
            self.game,
            self.calendar,
            self.player_duchy_id,
            battle=self.last_battle,
        )

    def _derive(
        self,
        world: WorldMap,
        game: GameState,
        calendar: Calendar,
        last_battle: HexBattle | None = None,
    ) -> "Session":
        """Return a new Session sharing RNG, player id and seed.

        ``last_battle`` defaults to ``None`` so transitions that do not carry
        an explicit battle reset the field.
        """
        return Session(
            world=world,
            game=game,
            calendar=calendar,
            rng=self.rng,
            player_duchy_id=self.player_duchy_id,
            seed=self.seed,
            last_battle=last_battle,
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


def _apply_order(session: Session, transition) -> Session:
    """Apply a no-battle player order transition and return a new Session.

    The transition receives ``(world, player_duchy)`` and returns a new
    ``WorldMap``.  The resulting ``GameState`` is ``sync_from_world`` of the
    new map.  When the order is illegal (game over, no player id, or missing
    duchy), the input world/game/calendar are returned unchanged.

    Calendar, RNG, seed and ``player_duchy_id`` are preserved; the RNG is not
    advanced.  The input session is never mutated.  Any previous ``last_battle``
    is reset to ``None``.
    """
    player_duchy = _resolve_player_duchy(session)
    if player_duchy is None:
        return session._derive(session.world, session.game, session.calendar)
    new_world = transition(session.world, player_duchy)
    new_game = session.game.sync_from_world(new_world)
    return session._derive(new_world, new_game, session.calendar)


def _apply_battle_order(
    session: Session,
    transition,
) -> Session:
    """Apply a battle player order transition and return a new Session.

    The transition receives ``(world, player_duchy, rng, game)`` and returns
    ``(new_world, battle | None)``.  The resulting ``GameState`` is
    ``sync_from_world`` of the new map and ``last_battle`` is set to the
    returned battle (or ``None`` when the order was a no-op).  When the order
    is illegal, the input world/game/calendar are returned unchanged with
    ``last_battle is None``.

    Calendar, RNG, seed and ``player_duchy_id`` are preserved.  The input
    session is never mutated.
    """
    player_duchy = _resolve_player_duchy(session)
    if player_duchy is None:
        return session._derive(session.world, session.game, session.calendar)
    new_world, battle = transition(session.world, player_duchy, session.rng, session.game)
    new_game = session.game.sync_from_world(new_world)
    return session._derive(new_world, new_game, session.calendar, last_battle=battle)


def apply_command(session: Session, command: dict) -> Session:
    """Dyspozytor poleceń sterujących mostu Godot↔rdzeń.

    Rozpoznawane ``command["type"]``:
      * ``"next_turn"`` — deleguje do ``session.next_turn()``.
      * ``"new_game"`` — zwraca świeżą sesję przez ``new_session``;
        domyślny seed pochodzi z ``session.seed``, można nadpisać kluczem
        ``"seed"`` w komendzie. Zachowany jest ``session.player_duchy_id``.
      * ``"order"`` — wydaje rozkaz dla księstwa gracza; rozpoznawane
        ``command["order"]`` to ``"develop"``, ``"recruit"``, ``"muster"``,
        ``"march"``, ``"assault"`` oraz ``"engage"``. Nieznana nazwa rozkazu
        podnosi ``ValueError``.

    Brak klucza ``type`` lub nieznana wartość podnoszą ``ValueError``.
    Wejściowa sesja nigdy nie jest mutowana.
    """
    command_type = command.get("type") if isinstance(command, dict) else None
    if command_type == "next_turn":
        return session.next_turn()
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
        if order == "march":
            return _apply_order(
                session, lambda world, duchy: _apply_march_order(world, duchy, command.get("target"))
            )
        if order == "assault":
            return _apply_battle_order(
                session,
                lambda world, duchy, rng, game: _apply_targeted_battle_order(
                    world,
                    duchy,
                    rng,
                    command.get("target"),
                    game,
                    to_recorded=ai.assault_duchy_party_to_recorded,
                    auto_recorded=ai.assault_duchy_party_recorded,
                ),
            )
        if order == "engage":
            return _apply_battle_order(
                session,
                lambda world, duchy, rng, game: _apply_targeted_battle_order(
                    world,
                    duchy,
                    rng,
                    command.get("target"),
                    game,
                    to_recorded=ai.engage_duchy_party_to_recorded,
                    auto_recorded=ai.engage_duchy_party_recorded,
                ),
            )
        if order not in _ORDER_TRANSITIONS:
            raise ValueError(f"Unknown order: {order!r}")
        return _apply_order(session, _ORDER_TRANSITIONS[order])
    raise ValueError(f"Unknown command type: {command_type!r}")
