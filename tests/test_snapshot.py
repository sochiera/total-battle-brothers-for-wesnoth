"""Tests for the tbbbridge state snapshots (G63.1a / G63.1b)."""

import copy
import json

import tbbui.unitstrength
from tbb import BRUISE, BARRACKS, FARM, MARKET, Resources, Settlement, Unit
from tbb.duchy import Duchy
from tbb.game import GameState
from tbb.party import Party
from tbb.turn import Calendar
from tbb.world import Region, WorldMap
from tbbbridge.snapshot import map_state, party_state, settlement_state
from tbbui.layout import layout_world


def _sample_settlement() -> Settlement:
    """A settlement exercising every snapshot field with distinct values."""
    garrison = (Unit(), Unit())
    return Settlement(
        name="Riverford",
        population=10,
        occupied=0,
        active_buildings=(FARM, MARKET, BARRACKS),
        storage=Resources(wheat=7, gold=3),
        capacity=12,
        garrison=garrison,
        owner_id="north",
    )


def test_settlement_state_returns_pure_json_serializable_dict_with_contract_keys_and_values():
    expected_keys = [
        "name",
        "owner",
        "wheat",
        "gold",
        "population",
        "free",
        "garrison",
        "buildings",
        "wheat_production",
        "gold_production",
        "wheat_consumption",
    ]
    settlement = _sample_settlement()
    before = copy.deepcopy(settlement)

    state = settlement_state(settlement)

    # Contract: exact key set in the prescribed order.
    assert list(state.keys()) == expected_keys
    # Contract: value sources from the settlement's public API.
    assert state["name"] == settlement.name
    assert state["owner"] == settlement.owner_id
    assert state["wheat"] == settlement.storage.wheat
    assert state["gold"] == settlement.storage.gold
    assert state["population"] == settlement.population
    assert state["free"] == settlement.free
    assert state["garrison"] == len(settlement.garrison)
    assert state["buildings"] == [b.name for b in settlement.active_buildings]
    assert state["wheat_production"] == settlement.production.wheat
    assert state["gold_production"] == settlement.production.gold
    assert state["wheat_consumption"] == settlement.consumption.wheat
    # Contract: result must be json-serializable.
    assert json.dumps(state, sort_keys=True) is not None
    # Contract: the settlement must not be mutated by the call.
    assert settlement == before


def test_settlement_state_owner_none_is_preserved_and_json_serializable():
    settlement = Settlement("Wild", population=1, owner_id=None)
    state = settlement_state(settlement)
    assert state["owner"] is None
    # None must round-trip through json (as null) without raising.
    json.dumps(state)


def _sample_party() -> Party:
    """A party with a hero, subordinates, a wounded member, and a real owner."""
    hero = Unit(training=2, equipment=1, experience=1)
    healthy = Unit(training=1, equipment=0, experience=1)
    wounded = Unit(training=0, equipment=1, experience=0, wounds=(BRUISE,))
    return Party(hero=hero, units=(healthy, wounded), owner_id="north")


def test_party_state_returns_pure_json_serializable_dict_with_contract_keys_and_values():
    expected_keys = ["owner", "size", "hp", "attack", "defense", "wounded"]
    party = _sample_party()
    before = copy.deepcopy(party)

    state = party_state(party)

    # Contract: exact key set in the prescribed order.
    assert list(state.keys()) == expected_keys
    # Contract: value sources from the party's public API and unitstrength.
    roster = (party.hero, *party.units)
    hp, attack, defense = tbbui.unitstrength.combat_totals(roster)
    assert state["owner"] == party.owner_id
    assert state["size"] == len(party.units)
    assert state["hp"] == hp
    assert state["attack"] == attack
    assert state["defense"] == defense
    assert state["wounded"] == tbbui.unitstrength.wounded_count(roster)
    # Contract: result must be json-serializable.
    json.dumps(state)
    # Contract: the party must not be mutated by the call (byte-for-byte equal).
    assert party == before


def test_party_state_owner_none_is_preserved_and_json_serializable():
    party = Party(Unit(), owner_id=None)
    state = party_state(party)
    assert state["owner"] is None
    # None must round-trip through json (as null) without raising.
    json.dumps(state)


def _map_world() -> WorldMap:
    """A world exercising settlement-only, party-only, empty and contested
    (both settlement + party) regions across a linear graph."""
    north = Region("Northkeep")
    wild = Region("Wilds")
    empty = Region("Empty")
    contested = Region("Contested")
    settlement = Settlement(
        name="Northkeep",
        population=4,
        owner_id="north",
        storage=Resources(wheat=1, gold=1),
        garrison=(Unit(),),
        active_buildings=(FARM,),
    )
    contested_settlement = Settlement(
        name="Contested",
        population=2,
        owner_id="crown",
        storage=Resources(wheat=0, gold=0),
        garrison=(),
        active_buildings=(),
    )
    party = Party(Unit(), owner_id="rebels")
    rebel_party = Party(Unit(training=1), owner_id="rebels")
    return WorldMap(
        regions=(north, wild, empty, contested),
        connections=((north, wild), (wild, empty), (empty, contested)),
        settlements={north: settlement, contested: contested_settlement},
        parties={wild: party, contested: rebel_party},
    )


def test_map_state_returns_pure_json_serializable_dict_with_contract_keys_and_values():
    from tbbbridge.snapshot import map_state

    world = _map_world()
    before = world

    state = map_state(world)

    # Contract: top-level keys exactly in order regions, connections.
    assert list(state.keys()) == ["regions", "connections"]

    positions = layout_world(world)
    north, wild, empty, contested = world.regions

    # Contract: regions list mirrors world.regions order; each entry has the
    # prescribed key order and values sourced from region / layout / snapshots.
    assert [r["name"] for r in state["regions"]] == [r.name for r in world.regions]
    assert list(state["regions"][0].keys()) == [
        "name",
        "col",
        "row",
        "owner",
        "settlement",
        "party",
    ]

    north_entry = state["regions"][0]
    assert north_entry["name"] == north.name
    assert (north_entry["col"], north_entry["row"]) == positions[north]
    # owner falls back to the settlement owner when a settlement is present.
    assert north_entry["owner"] == "north"
    assert north_entry["settlement"] == settlement_state(world.settlement_at(north))
    assert north_entry["party"] is None

    wild_entry = state["regions"][1]
    # No settlement -> owner falls back to the party owner.
    assert wild_entry["owner"] == "rebels"
    assert wild_entry["settlement"] is None
    assert wild_entry["party"] == party_state(world.party_at(wild))

    empty_entry = state["regions"][2]
    # Neither settlement nor party -> owner is None.
    assert empty_entry["owner"] is None
    assert empty_entry["settlement"] is None
    assert empty_entry["party"] is None

    contested_entry = state["regions"][3]
    # Both present -> settlement owner wins over party owner.
    assert contested_entry["owner"] == "crown"
    assert contested_entry["settlement"] == settlement_state(
        world.settlement_at(contested)
    )
    assert contested_entry["party"] == party_state(world.party_at(contested))

    # Contract: connections mirror world.connections order using region names.
    assert state["connections"] == [
        {"from": "Northkeep", "to": "Wilds"},
        {"from": "Wilds", "to": "Empty"},
        {"from": "Empty", "to": "Contested"},
    ]

    # Contract: the whole result is json-serializable and world is not mutated.
    json.dumps(state)
    assert world is before


def _duchy_settlement(owner: str, name: str) -> Settlement:
    """A minimal settlement owned by the given duchy, for duchy/state fixtures."""
    return Settlement(name=name, population=1, owner_id=owner)


def _duchy_party(owner: str) -> Party:
    """A minimal one-unit party owned by the given duchy."""
    return Party(hero=Unit(), units=(), owner_id=owner)


def _game_world() -> WorldMap:
    """A small two-region world carrying a player settlement for the map root."""
    home = Region("Home")
    border = Region("Border")
    settlement = Settlement(
        name="Home Keep", population=3, owner_id="player",
        storage=Resources(wheat=2, gold=2), garrison=(Unit(),),
    )
    return WorldMap(
        regions=(home, border),
        connections=((home, border),),
        settlements={home: settlement},
    )


def _rich_player_duchy() -> Duchy:
    """A player duchy exercising every projected duchy field distinctively."""
    hero = Unit(equipment=1)
    heir = Unit(training=1)
    return Duchy(
        duchy_id="player",
        hero=hero,
        morale=4,
        heir=heir,
        settlements=(_duchy_settlement("player", "Home Keep"),
                     _duchy_settlement("player", "Outpost")),
        parties=(_duchy_party("player"),),
    )


def _ai_duchy(*, alive: bool) -> Duchy:
    """An AI duchy; alive keeps a hero, otherwise it is defeated."""
    if alive:
        return Duchy(duchy_id="ai", hero=Unit(), settlements=())
    return Duchy(duchy_id="ai", hero=None, settlements=())


def _defeated_player_duchy() -> Duchy:
    return Duchy(duchy_id="player", hero=None, settlements=())


def test_game_state_composes_calendar_duchies_map_and_result_per_contract():
    from tbbbridge.snapshot import game_state

    world = _game_world()
    calendar = Calendar(year=2, month=7)

    # --- Scenario 1: victory (player is the sole contender). ---
    player = _rich_player_duchy()
    ai = _ai_duchy(alive=False)
    game = GameState((player, ai))

    # Capture pre-call scalars/lengths to detect mutation without deepcopy.
    caps = {
        "calendar": (calendar.year, calendar.month),
        "player": {
            "morale": player.morale,
            "has_heir": player.heir is not None,
            "settlements": len(player.settlements),
            "parties": len(player.parties),
        },
        "game": len(game.duchies),
    }

    state = game_state(world, game, calendar, player_duchy_id="player")

    # Contract: top-level keys exactly in order calendar, duchies, map, result.
    assert list(state.keys()) == ["calendar", "duchies", "map", "result"]

    # Contract: calendar sub-dict with exactly year, month sourced from input.
    assert list(state["calendar"].keys()) == ["year", "month"]
    assert state["calendar"] == {"year": calendar.year, "month": calendar.month}

    # Contract: map is exactly map_state(world) (reuse, no reimplementation).
    assert state["map"] == map_state(world)

    # Contract: duchies mirror game.duchies order; each entry has the
    # prescribed key order and values sourced from the duchy's public API.
    assert [d["id"] for d in state["duchies"]] == [d.duchy_id for d in game.duchies]
    assert list(state["duchies"][0].keys()) == [
        "id", "morale", "settlements", "parties",
        "has_hero", "has_heir", "is_defeated",
    ]
    player_entry = state["duchies"][0]
    assert player_entry["id"] == player.duchy_id
    assert player_entry["morale"] == player.morale
    assert player_entry["settlements"] == len(player.settlements)
    assert player_entry["parties"] == len(player.parties)
    assert player_entry["has_hero"] == player.has_hero
    assert player_entry["has_heir"] == (player.heir is not None)
    assert player_entry["is_defeated"] == player.is_defeated
    ai_entry = state["duchies"][1]
    assert ai_entry["is_defeated"] is True
    assert ai_entry["has_hero"] is False
    assert ai_entry["has_heir"] is False

    # Contract: result has exactly is_over, winner, player_result in order.
    assert list(state["result"].keys()) == ["is_over", "winner", "player_result"]
    assert state["result"]["is_over"] is game.is_over
    assert state["result"]["winner"] == game.winner.duchy_id
    assert state["result"]["player_result"] == "victory"

    # Contract: the whole snapshot is json-serializable.
    json.dumps(state)

    # Contract: no mutation of world/game/calendar (compare fields, no deepcopy).
    assert (calendar.year, calendar.month) == caps["calendar"]
    assert player.morale == caps["player"]["morale"]
    assert (player.heir is not None) == caps["player"]["has_heir"]
    assert len(player.settlements) == caps["player"]["settlements"]
    assert len(player.parties) == caps["player"]["parties"]
    assert len(game.duchies) == caps["game"]

    # --- Scenario 2: defeat (player defeated, AI is the winner). ---
    game_defeat = GameState((_defeated_player_duchy(), _ai_duchy(alive=True)))
    state_defeat = game_state(world, game_defeat, calendar,
                              player_duchy_id="player")
    assert state_defeat["result"]["is_over"] is True
    assert state_defeat["result"]["winner"] == "ai"
    assert state_defeat["result"]["player_result"] == "defeat"

    # --- Scenario 3: draw (both defeated -> no winner, game over). ---
    game_draw = GameState((_defeated_player_duchy(), _ai_duchy(alive=False)))
    state_draw = game_state(world, game_draw, calendar,
                            player_duchy_id="player")
    assert state_draw["result"]["is_over"] is True
    assert state_draw["result"]["winner"] is None
    assert state_draw["result"]["player_result"] == "draw"

    # --- Scenario 4: ongoing (both alive, no winner yet). ---
    game_ongoing = GameState((
        Duchy(duchy_id="player", hero=Unit(),
              settlements=(_duchy_settlement("player", "Home"),)),
        _ai_duchy(alive=True),
    ))
    state_ongoing = game_state(world, game_ongoing, calendar,
                               player_duchy_id="player")
    assert state_ongoing["result"]["is_over"] is False
    assert state_ongoing["result"]["winner"] is None
    assert state_ongoing["result"]["player_result"] == "ongoing"

    # --- Scenario 5: player_duchy_id None -> player_result None. ---
    state_none = game_state(world, game_ongoing, calendar, player_duchy_id=None)
    assert state_none["result"]["player_result"] is None
    json.dumps(state_none)


def test_main_writes_snapshot_to_explicit_path_creating_parent_directory_and_returns_zero(
    tmp_path,
):
    """G63.2b-1: tbbbridge.__main__.main([path]) rozgrywa headless + zapisuje snapshot.

    Kontrakt: main(argv=[path]) zwraca 0, tworzy katalog nadrzędny path,
    zapisuje plik parsujący się json.loads, klucze najwyższego poziomu to
    dokładnie ["calendar", "duchies", "map", "result"], a
    result["player_result"] należy do {"ongoing", "victory", "defeat", "draw"}.
    """
    from tbbbridge.__main__ import main

    out_path = tmp_path / "nested" / "state.json"

    rc = main([str(out_path)])

    assert rc == 0
    assert out_path.exists()
    snapshot = json.loads(out_path.read_text(encoding="utf-8"))
    assert list(snapshot.keys()) == ["calendar", "duchies", "map", "result"]
    assert snapshot["result"]["player_result"] in {
        "ongoing",
        "victory",
        "defeat",
        "draw",
    }


def test_save_state_writes_deterministic_byte_identical_file_round_tripping_game_state_without_mutating_inputs(
    tmp_path,
):
    """G63.2a: save_state zapisuje deterministyczny JSON do pliku.

    Kontrakt: plik = json.dumps(game_state(...), indent=2, ensure_ascii=False)
    zakończony pojedynczym "\\n", kodowanie UTF-8; path przyjmuje str lub
    os.PathLike; dwa wywołania dają bajt-w-bajt identyczny plik; odczytany
    tekst parsuje się json.loads do game_state(...); bez mutacji wejść i bez
    tworzenia katalogów.
    """
    from tbbbridge.snapshot import game_state, save_state

    world = _game_world()
    calendar = Calendar(year=2, month=7)
    game = GameState((_rich_player_duchy(), _ai_duchy(alive=False)))

    # Snapshot wejść do detekcji mutacji (bez deepcopy — porównujemy pola).
    caps = {
        "calendar": (calendar.year, calendar.month),
        "game_duchies": len(game.duchies),
    }

    expected_json = json.dumps(
        game_state(world, game, calendar, player_duchy_id="player"),
        indent=2,
        ensure_ascii=False,
    )
    expected_bytes = (expected_json + "\n").encode("utf-8")

    # --- ścieżka str ---
    out_str_path = str(tmp_path / "via_str.json")
    save_state(world, game, calendar, out_str_path, player_duchy_id="player")
    from pathlib import Path

    assert Path(out_str_path).read_bytes() == expected_bytes

    # --- ścieżka os.PathLike ---
    out_pl = tmp_path / "via_pathlike.json"
    save_state(world, game, calendar, out_pl, player_duchy_id="player")
    assert out_pl.read_bytes() == expected_bytes

    # --- determinizm: drugi zapis bajt-w-bajt identyczny ---
    out_again = tmp_path / "again.json"
    save_state(world, game, calendar, out_again, player_duchy_id="player")
    assert out_again.read_bytes() == Path(out_str_path).read_bytes()

    # --- round-trip: odczytany tekst parsuje się do game_state(...) ---
    parsed = json.loads(Path(out_str_path).read_text(encoding="utf-8"))
    assert parsed == game_state(world, game, calendar, player_duchy_id="player")

    # --- brak mutacji wejść ---
    assert (calendar.year, calendar.month) == caps["calendar"]
    assert len(game.duchies) == caps["game_duchies"]

    # --- brak tworzenia katalogów: zapis do nieistniejącego podkatalogu
    # zawodzi (save_state zakłada istniejący katalog docelowy). ---
    missing = tmp_path / "no_such_dir" / "snap.json"
    try:
        save_state(world, game, calendar, missing, player_duchy_id="player")
    except (FileNotFoundError, NotADirectoryError, OSError):
        pass
    else:
        raise AssertionError(
            "save_state powinien wymagać istniejącego katalogu docelowego"
        )
    assert not missing.parent.exists()


def test_main_without_positional_argument_writes_default_out_state_json(
    monkeypatch, tmp_path
):
    """G63.2b-2: main([]) / main() / main(None) → domyślna ścieżka out/state.json.

    Kontrakt: przy braku argumentu pozycyjnego main zapisuje snapshot do domyślnej
    ścieżki ``out/state.json`` względem katalogu bieżącego, tworząc katalog
    ``out/`` gdy go brak; zwraca ``0``. Test przez ``monkeypatch.chdir(tmp_path)``,
    sprawdza istnienie i parsowalność ``tmp_path / "out" / "state.json"``,
    bez podprocesu. Warianty: ``main([])``, ``main()`` (domyślny argv=None →
    ``sys.argv[1:]``) oraz ``main(None)``.
    """
    from tbbbridge.__main__ import main

    monkeypatch.chdir(tmp_path)
    # Brak katalogu out/ przed wywołaniem.
    assert not (tmp_path / "out").exists()

    rc = main([])

    out_path = tmp_path / "out" / "state.json"
    assert rc == 0
    assert out_path.exists()
    snapshot = json.loads(out_path.read_text(encoding="utf-8"))
    assert list(snapshot.keys()) == ["calendar", "duchies", "map", "result"]

    # Wariant main() (argv=None → sys.argv[1:]; tu puste) — osobny katalog roboczy.
    other = tmp_path / "via_default_call"
    other.mkdir()
    monkeypatch.chdir(other)
    monkeypatch.setattr("sys.argv", ["tbbbridge"])  # sys.argv[1:] == []

    rc_default = main()

    out_default = other / "out" / "state.json"
    assert rc_default == 0
    assert out_default.exists()
    json.loads(out_default.read_text(encoding="utf-8"))

    # Wariant main(None) — argv None traktowane jak brak argumentu.
    other2 = tmp_path / "via_none"
    other2.mkdir()
    monkeypatch.chdir(other2)

    rc_none = main(None)

    out_none = other2 / "out" / "state.json"
    assert rc_none == 0
    assert out_none.exists()
    json.loads(out_none.read_text(encoding="utf-8"))


def test_main_two_runs_to_different_paths_produce_byte_identical_json(tmp_path):
    """G63.2b-3: dwa uruchomienia ``main([...])`` dają bajt-w-bajt identyczny plik.

    Kontrakt: ``tbbbridge.__main__.main([...])`` wywołane dwukrotnie (bez podprocesu)
    do dwóch różnych ścieżek w ``tmp_path`` zapisuje pliki, których ``read_bytes()``
    są równe; obie ścieżki parsują się ``json.loads``. Wynika to z deterministycznego
    ``run_headless_game(Rng(73))`` + deterministycznego ``save_state`` (G63.2a).
    """
    from tbbbridge.__main__ import main

    path_a = tmp_path / "a" / "state.json"
    path_b = tmp_path / "b" / "state.json"

    rc_a = main([str(path_a)])
    rc_b = main([str(path_b)])

    assert rc_a == 0
    assert rc_b == 0
    assert path_a.exists()
    assert path_b.exists()

    # Obie ścieżki parsują się json.loads.
    snap_a = json.loads(path_a.read_text(encoding="utf-8"))
    snap_b = json.loads(path_b.read_text(encoding="utf-8"))
    assert list(snap_a.keys()) == ["calendar", "duchies", "map", "result"]
    assert list(snap_b.keys()) == ["calendar", "duchies", "map", "result"]

    # Bajt-w-bajt identyczne (determinizm CLI).
    assert path_a.read_bytes() == path_b.read_bytes()


def test_battle_state_returns_pure_json_serializable_dict_with_contract_keys_values_and_ordering():
    """G64.1a: tbbbridge.snapshot.battle_state(battle) -> dict.

    Kontrakt: słownik z kluczami dokładnie ["hexes", "result"]; hexes to lista
    po zajętych heksach battle.units, posortowana rosnąco po (hex.q, hex.r);
    każdy element ma klucze dokładnie ["q", "r", "terrain", "side", "hp",
    "stunned"] z wartościami q=hex.q, r=hex.r,
    terrain=battle.battlefield.terrain_at(hex).name, side=battle.side_at(hex).value,
    hp=battle.current_hp_at(hex), stunned=bool(battle.units[hex].stunned);
    result=battle.result().value gdy rozstrzygnięta, w przeciwnym razie None.
    Funkcja czysta, deterministyczna, bez mutacji; wynik przechodzi json.dumps.
    """
    from tbb.battle import BattleResult, BattleSide, HexBattle
    from tbb.battlefield import Battlefield
    from tbb.hex import Hex
    from tbb.terrain import FOREST, PLAINS
    from tbb.unit import Unit
    from tbbbridge.snapshot import battle_state

    def _battle(both_sides_alive: bool) -> HexBattle:
        attacker = Unit(training=2)  # hp = 12, distinct values
        defender = Unit(training=1, equipment=1)  # hp = 11
        stunned_defender = Unit(training=0, equipment=0, stunned=True)  # hp = 10
        battlefield = Battlefield({
            Hex(1, -1): FOREST,
            Hex(0, 0): PLAINS,
            Hex(-1, 2): FOREST,
        })
        battle = HexBattle(battlefield)
        # Deploy in non-sorted order to exercise the (q, r) sort.
        battle = battle.deploy(defender, Hex(0, 0), BattleSide.DEFENDER)
        battle = battle.deploy(attacker, Hex(1, -1), BattleSide.ATTACKER)
        battle = battle.deploy(
            stunned_defender, Hex(-1, 2), BattleSide.DEFENDER
        )
        if not both_sides_alive:
            # Run auto-resolve deterministically to reach a resolved state.
            # This covers the win/draw path without relying on internal
            # resolve_defeat ordering details.
            from tbb.rng import Rng

            rng = Rng(73)
            battle = battle.auto_resolve(move_points=1, rng=rng)
            assert battle.result() is not None
        return battle

    # --- Scenario A: ongoing battle -> result is None. ---
    battle = _battle(both_sides_alive=True)
    before = battle  # HexBattle is frozen; reference equality == no mutation.

    state = battle_state(battle)

    # Contract: top-level keys exactly ["hexes", "result"] in order.
    assert list(state.keys()) == ["hexes", "result"]

    # Contract: hexes sorted ascending by (q, r); deployed in order was
    # (0,0), (1,-1), (-1,2) -> sorted: (-1,2), (0,0), (1,-1).
    assert [h["q"] for h in state["hexes"]] == [-1, 0, 1]
    assert [h["r"] for h in state["hexes"]] == [2, 0, -1]

    # Contract: each hex entry has exactly the prescribed key order.
    for hex_entry in state["hexes"]:
        assert list(hex_entry.keys()) == ["q", "r", "terrain", "side", "hp", "stunned"]

    # Contract: value sources from battle's public API.
    expected_hexes = sorted(battle.units.keys(), key=lambda h: (h.q, h.r))
    for entry, hex_pos in zip(state["hexes"], expected_hexes):
        unit = battle.units[hex_pos]
        assert entry["q"] == hex_pos.q
        assert entry["r"] == hex_pos.r
        assert entry["terrain"] == battle.battlefield.terrain_at(hex_pos).name
        assert entry["side"] == battle.side_at(hex_pos).value
        assert entry["hp"] == battle.current_hp_at(hex_pos)
        assert entry["stunned"] is bool(unit.stunned)
        # stunned must be a real bool (not truthy int/etc.) for JSON fidelity.
        assert isinstance(entry["stunned"], bool)

    # Spot-check distinct values: attacker at (1,-1) is Tactics-trained on
    # Forest with full hp 12, side "attacker", not stunned.
    attacker_entry = state["hexes"][2]
    assert attacker_entry == {
        "q": 1, "r": -1, "terrain": "Forest", "side": "attacker",
        "hp": 12, "stunned": False,
    }
    # Stunned defender at (-1,2): stunned True.
    stunned_entry = state["hexes"][0]
    assert stunned_entry["stunned"] is True
    assert stunned_entry["side"] == "defender"

    # Contract: result is None while both sides are active.
    assert battle.result() is None
    assert state["result"] is None

    # Contract: whole result is json-serializable (test calls json.dumps).
    json.dumps(state)

    # Contract: no mutation of battle (frozen dataclass; same identity/equality).
    assert battle is before

    # --- Scenario B: resolved battle -> result is battle.result().value. ---
    resolved = _battle(both_sides_alive=False)
    state_resolved = battle_state(resolved)
    expected_result = resolved.result()
    assert expected_result is not None
    assert state_resolved["result"] == expected_result.value
    assert state_resolved["result"] in {
        BattleResult.ATTACKER_WIN.value,
        BattleResult.DEFENDER_WIN.value,
        BattleResult.DRAW.value,
    }
    # Still json-serializable and top-level keys unchanged.
    assert list(state_resolved.keys()) == ["hexes", "result"]
    json.dumps(state_resolved)


def test_python_m_tbbbridge_shim_propagates_rc_and_explicit_arg_writes_named_file_not_default(
    tmp_path,
):
    """G63.2b-2: ``python -m tbbbridge [path]`` uruchamia ``main`` i propaguje rc.

    Kontrakt: moduł kończy się blokiem
    ``if __name__ == "__main__": raise SystemExit(main())``, dzięki czemu
    realny podproces ``python -m tbbbridge <path>`` woła ``main`` i kończy
    kodem wyjścia ``0``; jawny ``argv[0]`` zapisuje snapshot do wskazanego
    pliku, a domyślna ``out/state.json`` **nie** powstaje w cwd podprocesu
    (brak regresji względem 306). Wariant bez argumentu zapisuje do
    domyślnej ``out/state.json`` względem cwd podprocesu.
    """
    import os
    import subprocess
    import sys
    from pathlib import Path

    src_dir = str(Path(__file__).resolve().parent.parent / "src")
    env = {**os.environ, "PYTHONPATH": src_dir}

    # --- Jawny argv[0]: snapshot do wskazanego pliku, bez domyślnej ścieżki. ---
    workdir_explicit = tmp_path / "explicit"
    workdir_explicit.mkdir()
    named_path = workdir_explicit / "snap" / "state.json"

    proc_explicit = subprocess.run(
        [sys.executable, "-m", "tbbbridge", str(named_path)],
        cwd=workdir_explicit,
        env=env,
        capture_output=True,
        text=True,
    )

    assert proc_explicit.returncode == 0, (
        f"python -m tbbbridge <path> powinien zwrócić 0; stderr={proc_explicit.stderr!r}"
    )
    assert named_path.exists(), "jawny argv[0] musi zapisać snapshot do wskazanego pliku"
    snapshot = json.loads(named_path.read_text(encoding="utf-8"))
    assert list(snapshot.keys()) == ["calendar", "duchies", "map", "result"]
    # Brak regresji vs 306: domyślna ścieżka NIE powstaje w cwd podprocesu.
    assert not (workdir_explicit / "out" / "state.json").exists()

    # --- Bez argumentu: snapshot do domyślnej out/state.json względem cwd. ---
    workdir_default = tmp_path / "default"
    workdir_default.mkdir()

    proc_default = subprocess.run(
        [sys.executable, "-m", "tbbbridge"],
        cwd=workdir_default,
        env=env,
        capture_output=True,
        text=True,
    )

    assert proc_default.returncode == 0, (
        f"python -m tbbbridge (bez arg) powinien zwrócić 0; stderr={proc_default.stderr!r}"
    )
    out_default = workdir_default / "out" / "state.json"
    assert out_default.exists(), "bez argumentu snapshot idzie do out/state.json"
    json.loads(out_default.read_text(encoding="utf-8"))


def test_game_state_with_battle_embeds_battle_state_and_none_preserves_prior_output():
    """G64.1b: game_state(..., battle=None) osadza battle_state.

    Kontrakt:
    - przy ``battle is not None`` wynik ma klucze dokładnie
      ``["calendar", "duchies", "map", "result", "battle"]``, gdzie
      ``state["battle"] == battle_state(battle)``;
    - przy ``battle is None`` (domyślnie) wynik jest bajt-w-bajt identyczny z
      wywołaniem bez parametru (klucze
      ``["calendar", "duchies", "map", "result"]``,
      ``json.dumps`` równy staremu dla tego samego wejścia);
    - funkcja pozostaje czysta, deterministyczna, bez mutacji wejść; wynik
      przechodzi przez ``json.dumps``.
    """
    from tbb.battle import BattleSide, HexBattle
    from tbb.battlefield import Battlefield
    from tbb.hex import Hex
    from tbb.terrain import FOREST, PLAINS
    from tbb.unit import Unit
    from tbbbridge.snapshot import battle_state, game_state

    world = _game_world()
    calendar = Calendar(year=2, month=7)
    game = GameState((_rich_player_duchy(), _ai_duchy(alive=False)))

    # Build a real ongoing HexBattle (both sides active) as a fixture input.
    attacker = Unit(training=2)
    defender = Unit(training=1, equipment=1)
    battlefield = Battlefield({Hex(1, -1): FOREST, Hex(0, 0): PLAINS})
    battle = HexBattle(battlefield)
    battle = battle.deploy(defender, Hex(0, 0), BattleSide.DEFENDER)
    battle = battle.deploy(attacker, Hex(1, -1), BattleSide.ATTACKER)
    assert battle.result() is None  # ongoing

    battle_before = battle  # frozen dataclass; identity equality ↔ no mutation

    # --- Scenario 1: battle is not None -> last key "battle" == battle_state. ---
    state = game_state(
        world, game, calendar, player_duchy_id="player", battle=battle
    )
    # Contract: top-level keys exactly the prescribed order, "battle" last.
    assert list(state.keys()) == [
        "calendar", "duchies", "map", "result", "battle",
    ]
    # Contract: embedded battle equals battle_state(battle) (reuse, not reimplement).
    assert state["battle"] == battle_state(battle)
    # Contract: the first four keys/values are unchanged vs the no-battle call.
    base = game_state(world, game, calendar, player_duchy_id="player")
    assert state["calendar"] == base["calendar"]
    assert state["duchies"] == base["duchies"]
    assert state["map"] == base["map"]
    assert state["result"] == base["result"]
    # Contract: whole result is json-serializable.
    json.dumps(state)
    # Contract: no mutation of battle (frozen dataclass; identity equality).
    assert battle is battle_before

    # --- Scenario 2: battle is None -> byte-for-byte identical to pre-task. ---
    state_none_explicit = game_state(
        world, game, calendar, player_duchy_id="player", battle=None
    )
    assert list(state_none_explicit.keys()) == [
        "calendar", "duchies", "map", "result",
    ]
    assert state_none_explicit == base
    assert json.dumps(state_none_explicit, sort_keys=True) == json.dumps(
        base, sort_keys=True
    )

    # --- Scenario 3: default (no battle kwarg) == battle=None (no regression). ---
    state_default = game_state(
        world, game, calendar, player_duchy_id="player"
    )
    assert list(state_default.keys()) == [
        "calendar", "duchies", "map", "result",
    ]
    assert json.dumps(state_default, sort_keys=True) == json.dumps(
        base, sort_keys=True
    )
