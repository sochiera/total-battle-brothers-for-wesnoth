"""Interactive preview: request routing + thin http.server adapter (V13.5)."""

from __future__ import annotations

import http.server

from tbb import ai
from tbb.driver import run_headless_game
from tbb.game import GameState
from tbb.rng import Rng
from tbb.turn import Calendar
from tbb.world import WorldMap
from tbbui.gamepage import render_game_page

_TURN_FORM = (
    '<form method="post" action="/turn">'
    '<button type="submit">Next turn</button>'
    "</form>"
)

_RECRUIT_FORM = (
    '<form method="post" action="/order/recruit">'
    '<button type="submit">Recruit</button>'
    "</form>"
)

_MUSTER_FORM = (
    '<form method="post" action="/order/muster">'
    '<button type="submit">Muster</button>'
    "</form>"
)

_DEVELOP_FORM = (
    '<form method="post" action="/order/develop">'
    '<button type="submit">Develop settlement</button>'
    "</form>"
)


class GameApp:
    """In-memory request router over one party snapshot (GET page / POST turn)."""

    def __init__(
        self,
        world: WorldMap,
        game: GameState,
        calendar: Calendar,
        rng: Rng,
        player_duchy_id: str | None = None,
    ) -> None:
        self.world = world
        self.game = game
        self.calendar = calendar
        self.rng = rng
        self.player_duchy_id = player_duchy_id

    def handle(self, method: str, path: str) -> tuple[int, str]:
        """Route one request; return ``(http_status, body)`` without sockets."""
        if method == "GET" and path == "/":
            return 200, self._render()
        if method == "POST" and path == "/turn":
            if not self.game.is_over:
                self.world, self.game, self.calendar = run_headless_game(
                    self.world,
                    self.game,
                    self.rng,
                    max_turns=1,
                    calendar=self.calendar,
                    player_duchy_id=self.player_duchy_id,
                )
            return 200, self._render()
        if method == "POST" and path == "/order/recruit":
            self._apply_player_order(ai.recruit_duchy_unit)
            return 200, self._render()
        if method == "POST" and path == "/order/muster":
            self._apply_player_order(ai.muster_duchy_party)
            return 200, self._render()
        if method == "POST" and path == "/order/develop":
            self._apply_player_order(ai.develop_duchy_settlement)
            return 200, self._render()
        return 404, "Not Found"

    def _apply_player_order(self, transition) -> None:
        """Apply ``transition(world, player_duchy)`` when a player order is legal.

        No-op when the game is over, there is no player duchy id, or that
        duchy is absent from ``game.duchies``. On success replaces ``world``
        and re-syncs ``game`` from the new map.
        """
        if self.game.is_over or self.player_duchy_id is None:
            return
        player_duchy = next(
            (d for d in self.game.duchies if d.duchy_id == self.player_duchy_id),
            None,
        )
        if player_duchy is None:
            return
        self.world = transition(self.world, player_duchy)
        self.game = self.game.sync_from_world(self.world)

    def _render(self) -> str:
        html = render_game_page(self.world, self.game, self.calendar)
        player_value = self.player_duchy_id if self.player_duchy_id is not None else ""
        extras = (
            f'<span data-player="{player_value}"></span>'
            f"{_TURN_FORM}{_RECRUIT_FORM}{_MUSTER_FORM}{_DEVELOP_FORM}"
        )
        if "</body>" in html:
            return html.replace("</body>", f"{extras}</body>", 1)
        return f"{html}{extras}"


def handle_request(app: GameApp, method: str, path: str) -> tuple[int, bytes]:
    """Thin adapter: ``app.handle`` → ``(status, UTF-8 body bytes)`` (no socket)."""
    code, body = app.handle(method, path)
    return code, body.encode("utf-8")


def make_server(
    app: GameApp,
    host: str = "127.0.0.1",
    port: int = 0,
) -> http.server.HTTPServer:
    """Bind ``HTTPServer`` whose GET/POST handlers delegate to ``handle_request``.

    Does not call ``serve_forever``; the caller owns the lifecycle
    (``serve_forever`` / ``server_close``).
    """

    class _Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            self._dispatch("GET")

        def do_POST(self) -> None:
            self._dispatch("POST")

        def _dispatch(self, method: str) -> None:
            path = self.path.split("?", 1)[0]
            code, body = handle_request(app, method, path)
            self.send_response(code)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, format: str, *args: object) -> None:
            # Quiet by default — preview is local and tests bind real ports.
            return

    return http.server.HTTPServer((host, port), _Handler)
