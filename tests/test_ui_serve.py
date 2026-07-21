"""HTTP preview server adapter: make_server + handle_request (V13.5b)."""

from __future__ import annotations

import http.client
import http.server
import threading

from tbb.duchy import Duchy
from tbb.game import GameState
from tbb.party import Party
from tbb.rng import Rng
from tbb.settlement import Settlement
from tbb.turn import Calendar
from tbb.unit import Unit
from tbb.world import Region, WorldMap
from tbbui.serve import GameApp


def _ongoing_world_game() -> tuple[WorldMap, GameState]:
    north, south = map(Region, ("North", "South"))
    north_keep = Settlement("North Keep", 2, owner_id="north")
    south_keep = Settlement("South Keep", 2, owner_id="south")
    world = WorldMap(
        (north, south), settlements={north: north_keep, south: south_keep}
    )
    game = GameState(
        (
            Duchy("north", Unit(), settlements=(north_keep,)),
            Duchy("south", Unit(), settlements=(south_keep,)),
        )
    )
    return world, game


def _fresh_app(seed: int = 17) -> GameApp:
    world, game = _ongoing_world_game()
    return GameApp(world, game, Calendar(year=4, month=9), Rng(seed))


def test_make_server_binds_port_and_handle_request_delegates_to_app_handle():
    """make_server binds a real port; handle_request mirrors app.handle as bytes.

    Contract (task-075 / V13.5b):
    - make_server(app, host, port=0) -> HTTPServer with server_address[1] > 0;
      caller closes via server_close() (no serve_forever in tests)
    - handle_request(app, method, path) -> (status: int, body: bytes) by
      delegating to app.handle for GET /, POST /turn, and unknown paths (404)
    - for a fixed seed/setup, (code, body) match app.handle with body as UTF-8
    """
    from tbbui.serve import handle_request, make_server

    app = _fresh_app(seed=17)

    server = make_server(app, host="127.0.0.1", port=0)
    try:
        assert isinstance(server, http.server.HTTPServer)
        host, port = server.server_address[:2]
        assert host in ("127.0.0.1", "0.0.0.0", "::1") or isinstance(host, str)
        assert isinstance(port, int)
        assert port > 0
    finally:
        server.server_close()

    # GET / — compare against a twin app (handle returns str; adapter → bytes).
    get_a = _fresh_app(seed=17)
    get_b = _fresh_app(seed=17)
    code_h, body_h = get_a.handle("GET", "/")
    code_r, body_r = handle_request(get_b, "GET", "/")
    assert code_r == code_h == 200
    assert isinstance(body_r, bytes)
    assert body_r == body_h.encode("utf-8")

    # POST /turn — one strategic month; separate twins so each path runs once.
    post_a = _fresh_app(seed=17)
    post_b = _fresh_app(seed=17)
    code_h, body_h = post_a.handle("POST", "/turn")
    code_r, body_r = handle_request(post_b, "POST", "/turn")
    assert code_r == code_h == 200
    assert isinstance(body_r, bytes)
    assert body_r == body_h.encode("utf-8")

    # Unknown path → 404 from app.handle, body as UTF-8 bytes.
    miss_a = _fresh_app(seed=17)
    miss_b = _fresh_app(seed=17)
    code_h, body_h = miss_a.handle("GET", "/nope")
    code_r, body_r = handle_request(miss_b, "GET", "/nope")
    assert code_r == code_h == 404
    assert isinstance(body_r, bytes)
    assert body_r == body_h.encode("utf-8")


def test_dispatch_passes_full_path_with_query_over_real_socket():
    """_Handler._dispatch forwards self.path (incl. ``?query``) unstripped (K15.1b).

    Contract (task-086): a real POST over the bound socket to
    ``/order/march?target=Far`` must reach ``GameApp.handle`` with the query
    string intact, so the targeted march (``march_duchy_party_to``) applies —
    not the nearest-enemy fallback that a stripped path would trigger.
    """
    from tbbui.serve import make_server

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
    app = GameApp(
        world, game, Calendar(year=2, month=3), Rng(11), player_duchy_id="north"
    )

    server = make_server(app, host="127.0.0.1", port=0)
    thread = threading.Thread(target=server.handle_request)
    thread.start()
    try:
        conn = http.client.HTTPConnection(*server.server_address[:2])
        conn.request("POST", "/order/march?target=Far")
        response = conn.getresponse()
        response.read()
        conn.close()
    finally:
        thread.join()
        server.server_close()

    # Nearest-enemy fallback would have stepped toward Near, not Far — the
    # query only takes effect if _dispatch handed the full path to handle.
    assert app.world.party_at(step_far) is party
    assert app.world.party_at(step_near) is None


def test_tbbui_serve_builds_game_app_with_headless_seed(monkeypatch):
    """python -m tbbui serve constructs GameApp with seed=HEADLESS_SEED (K31.1c).

    Contract (task-159 / K31.1c):
    - ``_run_serve`` / CLI ``python -m tbbui serve`` builds
      ``GameApp(..., player_duchy_id="player", seed=HEADLESS_SEED)``
    - remaining construction (Calendar(), Rng(HEADLESS_SEED), make_server
      lifecycle) is unchanged so POST /new can reset the preview party
    """
    from tbbui.__main__ import HEADLESS_SEED, main

    captured: dict = {}

    class _FakeServer:
        server_address = ("127.0.0.1", 8765)

        def serve_forever(self) -> None:
            raise KeyboardInterrupt

        def server_close(self) -> None:
            captured["closed"] = True

    def fake_make_server(app, host="127.0.0.1", port=0):
        captured["app"] = app
        captured["host"] = host
        captured["port"] = port
        return _FakeServer()

    monkeypatch.setattr("tbbui.__main__.make_server", fake_make_server)

    code = main(["serve"])
    assert code == 0
    app = captured["app"]
    assert isinstance(app, GameApp)
    assert app.player_duchy_id == "player"
    assert app.seed == HEADLESS_SEED
    assert HEADLESS_SEED == 73
    assert captured["closed"] is True
    assert captured["host"] == "127.0.0.1"
