"""Interactive preview request routing without a real HTTP socket (V13.5a)."""

from __future__ import annotations

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


class GameApp:
    """In-memory request router over one party snapshot (GET page / POST turn)."""

    def __init__(
        self,
        world: WorldMap,
        game: GameState,
        calendar: Calendar,
        rng: Rng,
    ) -> None:
        self.world = world
        self.game = game
        self.calendar = calendar
        self.rng = rng

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
                )
            return 200, self._render()
        return 404, "Not Found"

    def _render(self) -> str:
        html = render_game_page(self.world, self.game, self.calendar)
        if "</body>" in html:
            return html.replace("</body>", f"{_TURN_FORM}</body>", 1)
        return f"{html}{_TURN_FORM}"
