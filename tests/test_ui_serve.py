"""HTTP preview server adapter: make_server + handle_request (V13.5b)."""

from __future__ import annotations

import http.server

from tbb.duchy import Duchy
from tbb.game import GameState
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
