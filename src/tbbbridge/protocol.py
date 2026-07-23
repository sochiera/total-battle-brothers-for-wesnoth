"""Liniowy protokół JSON dla mostu Godot↔rdzeń (G66.1a)."""

import json

from tbbbridge.persist import read_session, save_session
from tbbbridge.session import Session, apply_command, new_session

_BATTLE_ORDERS = ("assault", "engage")

_BATTLE_OUTCOME = {
    "attacker_win": "zwycięstwo",
    "defender_win": "porażka",
    "draw": "remis",
}


def _validated_path(command: dict, command_name: str) -> tuple[str | None, str | None]:
    """Zwraca ``(path, None)`` gdy ``path`` jest niepustym łańcuchem;
    inaczej ``(None, error_message)``.
    """
    path = command.get("path")
    if isinstance(path, str) and path != "":
        return path, None
    return None, f"{command_name} command requires a non-empty string path"


def command_result(before: Session, after: Session, command: dict) -> dict:
    """Maszynowe podsumowanie skutku komendy (sterującej lub niebitewnej)."""
    command_type = command.get("type")

    if command_type == "next_turn":
        return {
            "kind": "turn",
            "date": {"year": after.calendar.year, "month": after.calendar.month},
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
        if order_name in _BATTLE_ORDERS and after.last_battle is not None:
            report = after.last_battle.report()
            outcome = _BATTLE_OUTCOME.get(report.result.value)
            return {
                "kind": "battle",
                "order": order_name,
                "outcome": outcome,
                "attacker_losses": len(report.attacker.fallen),
                "defender_losses": len(report.defender.fallen),
            }
        return {
            "kind": "order",
            "order": order_name,
            "changed": after.world is not before.world,
        }

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
