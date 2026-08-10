"""Liniowy protokół JSON dla mostu Godot↔rdzeń (G66.1a)."""

import json

import tbb.ai as ai
from tbb.battle import BattleSide, HexBattle
from tbbbridge.persist import read_session, save_session
from tbbbridge.session import (
    PendingBattle,
    Session,
    _find_region_by_name,
    _resolve_player_duchy,
    _battle_target_reason,
    apply_command,
    new_session,
)
from tbbbridge.snapshot import battle_state

_BATTLE_ORDERS = ("assault", "engage")
_ECONOMIC_ORDERS = ("develop", "recruit", "muster")

_BATTLE_IN_PROGRESS_REASON = "bitwa w toku"
_NO_PENDING_BATTLE_REASON = "brak bitwy w toku"

_BATTLE_OUTCOME = {
    "attacker_win": "zwycięstwo",
    "defender_win": "porażka",
    "draw": "remis",
}


def _battle_summary(battle: HexBattle) -> dict:
    """Maszynowe podsumowanie rozstrzygniętej bitwy (bez nazwy rozkazu)."""
    result = battle.result()
    outcome = (
        _BATTLE_OUTCOME[result.value]
        if result is not None
        else "nierozstrzygnięta"
    )
    return {
        "kind": "battle",
        "outcome": outcome,
        "attacker_losses": len(battle.side_fallen(BattleSide.ATTACKER)),
        "defender_losses": len(battle.side_fallen(BattleSide.DEFENDER)),
    }


def _battle_step_result(command_type: str, before: Session, after: Session) -> dict:
    """Wspólny kształt odpowiedzi ``battle_advance``/``battle_auto``.

    Bitwa nadal w toku odpowiada planszą ``battle_pending``; komenda, która
    domknęła bitwę — podsumowaniem ``{"kind": "battle", …}``; bez bitwy
    w toku obie odpowiadają odmową ``changed: false`` z tym samym powodem.
    """
    if after.pending_battle is not None:
        return _battle_pending_result(after.pending_battle)
    if before.pending_battle is not None and after.last_battle is not None:
        return _battle_summary(after.last_battle)
    return {
        "kind": command_type,
        "changed": False,
        "reason": _NO_PENDING_BATTLE_REASON,
    }


def _battle_pending_result(pending: PendingBattle) -> dict:
    """Odpowiedź ``battle_pending`` z planszą bitwy pauzującej w sesji."""
    return {
        "kind": "battle_pending",
        "battle": battle_state(pending.battle),
    }


def _validated_path(command: dict, command_name: str) -> tuple[str | None, str | None]:
    """Zwraca ``(path, None)`` gdy ``path`` jest niepustym łańcuchem;
    inaczej ``(None, error_message)``.
    """
    path = command.get("path")
    if isinstance(path, str) and path != "":
        return path, None
    return None, f"{command_name} command requires a non-empty string path"


def _blocked_region_name(session: Session, command: dict) -> str | None:
    """Return the region blocking an ineffective player movement order."""
    order_name = command.get("order")
    if order_name not in ("march", "move"):
        return None

    # Mirror the core's _resolve_player_duchy, _duchy_party_position,
    # WorldMap._party_can_act, and _can_enter_adjacent_region guards so a
    # diagnostic never appears for an order the core cannot execute.
    player_duchy = _resolve_player_duchy(session)
    if player_duchy is None:
        return None

    owner_id = player_duchy.duchy_id
    start = ai._duchy_party_position(session.world, owner_id)
    if start is None or not session.world._party_can_act(start):
        return None

    target = _find_region_by_name(session.world, command.get("target"))
    if order_name == "march":
        # A resolved explicit march target is a core no-op when adjacent;
        # only the no-target/automatic march gets a blocking diagnostic.
        if target is not None:
            return None
        target = None
    elif target is None or target not in session.world.neighbors(start):
        return None
    if (
        order_name == "move"
        and ai._can_enter_adjacent_region(session.world, start, target, owner_id)
    ):
        return None

    blocked = ai.blocking_foreign_party_region(
        session.world, start, owner_id, target
    )
    return blocked.name if blocked is not None else None


def _order_refusal_reason(
    session: Session, command: dict, order_name: str
) -> str | None:
    """Return the core or bridge reason for an ineffective player order."""
    target = _find_region_by_name(session.world, command.get("target"))
    if "target" in command and target is None:
        return "nieznany region"

    player_duchy = _resolve_player_duchy(session)
    if player_duchy is None:
        return None
    if order_name in _ECONOMIC_ORDERS:
        return ai.economic_order_reason(
            session.world, player_duchy, order_name, target=target
        )
    if order_name in _BATTLE_ORDERS:
        return ai.military_order_reason(
            session.world, player_duchy, order_name, target=target
        )
    return None


def command_result(before: Session, after: Session, command: dict) -> dict:
    """Maszynowe podsumowanie skutku komendy (sterującej lub niebitewnej).

    Pauza bitewna (G119.1b): rozkaz ``assault``/``engage``, który zaczął
    bitwę, odpowiada ``{"kind": "battle_pending", "battle": battle_state(…)}``
    z planszą w toku; ``battle_advance`` odpowiada tym samym kształtem po
    jednej rundzie, a ``battle_auto`` po rozstrzygnięciu reszty rund — oba
    domykając bitwę odpowiadają kształtem ``{"kind": "battle", …}``
    z rozstrzygnięciem. Bez bitwy w toku obie komendy odpowiadają
    ``changed: false`` z powodem ``"brak bitwy w toku"``. Dopóki bitwa
    gracza jest w toku, każdy inny rozkaz oraz ``next_turn`` odpowiadają
    ``changed: false`` z powodem ``"bitwa w toku"`` (wzorzec K111/K114/K118).
    """
    command_type = command.get("type")

    if command_type == "next_turn":
        result = {
            "kind": "turn",
            "date": {"year": after.calendar.year, "month": after.calendar.month},
        }
        if before.pending_battle is not None:
            result["changed"] = False
            result["reason"] = _BATTLE_IN_PROGRESS_REASON
            return result
        if after.game.is_over:
            result["game_over"] = True
        return result

    if command_type in ("battle_advance", "battle_auto"):
        return _battle_step_result(command_type, before, after)

    if command_type == "battle_target":
        if (
            before.pending_battle is not None
            and after.pending_battle is not before.pending_battle
        ):
            return {"kind": "battle_target", "changed": True}
        return {
            "kind": "battle_target",
            "changed": False,
            "reason": _battle_target_reason(before, command),
        }

    if command_type == "new_game":
        return {"kind": "new_game"}

    if command_type == "snapshot":
        return {"kind": "snapshot"}

    if command_type in ("save", "load"):
        return {
            "kind": command_type,
            "path": command["path"],
        }

    if command_type == "order":
        order_name = command["order"]
        if before.pending_battle is not None:
            return {
                "kind": "order",
                "order": order_name,
                "changed": False,
                "reason": _BATTLE_IN_PROGRESS_REASON,
            }
        if order_name in _BATTLE_ORDERS and after.pending_battle is not None:
            return _battle_pending_result(after.pending_battle)
        result = {
            "kind": "order",
            "order": order_name,
            "changed": after.world is not before.world,
        }
        if (
            not result["changed"]
            and order_name in (_ECONOMIC_ORDERS + _BATTLE_ORDERS)
        ):
            reason = _order_refusal_reason(before, command, order_name)
            if reason is not None:
                result["reason"] = reason
        if not result["changed"]:
            blocked_region = _blocked_region_name(before, command)
            if blocked_region is not None:
                result["blocked_region"] = blocked_region
        if after.game.is_over:
            result["game_over"] = True
        return result

    return {}


def handle_command_line(session: Session, line: str) -> tuple[Session, dict]:
    """Sparsuj linię-komendę JSON i zwróć (nowa_sesja, odpowiedź).

    - Niepoprawny JSON lub JSON nie będący obiektem →
      ``(session, {"ok": False, "error": <str>})``.
    - Poprawna komenda → delegowane do ``apply_command``; sukces daje
      ``(new_session, {"ok": True, "snapshot": new_session.snapshot(),
      "result": command_result(session, new_session, command)})``.
    - ``ValueError`` z ``apply_command`` →
      ``(session, {"ok": False, "error": str(exc)})``.

    Funkcja jest czysta — wejściowa sesja nigdy nie jest mutowana.
    """
    try:
        command = json.loads(line)
    except json.JSONDecodeError as exc:
        return session, {
            "ok": False,
            "error": f"Bad JSON: {exc.msg}",
        }

    if not isinstance(command, dict):
        return session, {
            "ok": False,
            "error": "Command must be a JSON object",
        }

    if command.get("type") == "save":
        path, error = _validated_path(command, "save")
        if error is not None:
            return session, {"ok": False, "error": error}
        try:
            save_session(session, path)
        except OSError as exc:
            return session, {"ok": False, "error": str(exc)}
        return session, {
            "ok": True,
            "snapshot": session.snapshot(),
            "result": command_result(session, session, command),
        }

    if command.get("type") == "load":
        path, error = _validated_path(command, "load")
        if error is not None:
            return session, {"ok": False, "error": error}
        try:
            loaded = read_session(path)
        except (OSError, json.JSONDecodeError) as exc:
            return session, {"ok": False, "error": str(exc)}
        return loaded, {
            "ok": True,
            "snapshot": loaded.snapshot(),
            "result": command_result(session, session, command),
        }

    try:
        next_session = apply_command(session, command)
    except ValueError as exc:
        return session, {"ok": False, "error": str(exc)}

    return next_session, {
        "ok": True,
        "snapshot": next_session.snapshot(),
        "result": command_result(session, next_session, command),
    }


def serve_stream(session: Session, in_stream, out_stream) -> Session:
    """Czytaj linie-komendy z ``in_stream`` i wypisuj linie-odpowiedzi do ``out_stream``.

    - Puste / białoznakowe linie są pomijane.
    - Każda niepusta linia jest przekazywana do :func:`handle_command_line`;
      odpowiedź ``resp`` jest zapisywana jako ``json.dumps(resp) + "\\n"``
      i natychmiast ``flush()``-owana.
    - Po EOF zwracana jest bieżąca (końcowa) sesja.

    Funkcja nie zależy od konkretnej klasy strumienia — wystarcza kaczkowe
    ``.write`` / ``.flush`` po stronie wyjścia oraz iterowalne wejście.
    """
    current = session
    for line in in_stream:
        if not line.strip():
            continue
        current, resp = handle_command_line(current, line)
        out_stream.write(json.dumps(resp) + "\n")
        out_stream.flush()
    return current
