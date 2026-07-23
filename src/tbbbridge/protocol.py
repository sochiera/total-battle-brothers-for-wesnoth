"""Liniowy protokół JSON dla mostu Godot↔rdzeń (G66.1a)."""

import json

from tbbbridge.session import Session, apply_command, new_session


def handle_command_line(session: Session, line: str) -> tuple[Session, dict]:
    """Sparsuj linię-komendę JSON i zwróć (nowa_sesja, odpowiedź).

    - Niepoprawny JSON lub JSON nie będący obiektem →
      ``(session, {"ok": False, "error": <str>})``.
    - Poprawna komenda → delegowane do ``apply_command``; sukces daje
      ``(new_session, {"ok": True, "snapshot": new_session.snapshot()})``.
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

    try:
        next_session = apply_command(session, command)
    except ValueError as exc:
        return session, {"ok": False, "error": str(exc)}

    return next_session, {"ok": True, "snapshot": next_session.snapshot()}


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
