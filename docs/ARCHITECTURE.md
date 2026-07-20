# ARCHITECTURE — decyzje techniczne

> **Dokument żywy.** Trzyma decyzje o stacku, strukturze katalogów, komendach i
> konwencjach. Zmieniasz strukturę lub sposób uruchamiania — aktualizujesz tu.

## 1. Wybór stacku i uzasadnienie

**Język: Python 3.11+** (środowisko dev: 3.14). **Testy: pytest.**
Rdzeń gry to **czysta biblioteka Pythona** bez zależności od silnika graficznego.

### Dlaczego Python + pytest
- Brief wymaga **rdzenia logiki oddzielonego od prezentacji** i rozwoju w **TDD**.
  Najszybsza pętla test→kod jest w dynamicznym języku z lekkim runnerem.
- MVP to logika turowa (ekonomia, mapa, bitwa heksowa) — **CPU/logika, nie
  grafika**. Nie potrzebujemy silnika, żeby zbudować i przetestować rdzeń.
- Zero-config start: pytest jest już dostępny w środowisku, brak kroku
  kompilacji, brak toolchainu C++.
- Determinizm łatwo osiągalny (wstrzykiwany seedowalny RNG).

### Dlaczego NIE fork Battle for Wesnoth (na start)
Brief mówi, że użycie kodu/zasobów Wesnoth jest **opcjonalne**. Wesnoth to duży
projekt C++/Lua z ciężkim toolchainem i silnym sprzężeniem logiki z prezentacją —
to przeciwieństwo szybkiego, izolowanego rdzenia w TDD. Możemy później
**zapożyczyć dane/projekt** (np. profile terenu, wzory na trafienie) bez brania
całego silnika. Decyzja jest odwracalna: rdzeń jest czysty, więc prezentację
(pygame/tekst/most do innego silnika) można dołożyć nad nim.

### Prezentacja (pakiet `tbbui`, Kamień 13)
Warstwa render/UI jest **poza rdzeniem**. `python -m tbb` nadal uruchamia
deterministyczną partię headless. Obserwowalny UI buduje **osobny pakiet**
`src/tbbui/` konsumujący rdzeń przez publiczne API — rdzeń `tbb` **nigdy** nie
importuje `tbbui`.

**Decyzja stacku (stdlib only):** w środowisku orkiestratora **nie ma** pygame
ani tkinter. Prezentacja jest więc w **czystym stdlib**: deterministyczne
stringi **SVG/HTML** (testowalne pytestem) oraz lokalny podgląd na
`http.server`. Wyświetlaczem jest przeglądarka. Pierwszy przyrost (K13) to tryb
obserwatora; rozkazy gracza z UI to kolejny kamień.

**Layout mapy strategicznej:** `tbbui.layout.layout_world(world) ->
dict[Region, tuple[int, int]]` — czysta, deterministyczna funkcja (bez RNG/IO).
Komponenty grafu w kolejności `world.regions`; w komponencie BFS od pierwszego
regionu; **kolumna** = dystans od korzenia; w warstwie BFS kolejność =
`world.regions`; **wiersz** = pierwszy wolny indeks w kolumnie (liczniki
kolumn globalne między komponentami).

**Szkielet SVG mapy (V13.2a–d):** `tbbui.worldsvg.render_world_svg(world) -> str`
— parsowalny XML z korzeniem `<svg>`; po jednym `<g data-region="…">` na region
(z etykietą tekstową = nazwa). Środki węzłów: stały pitch z komórek
`layout_world` (`x = ORIGIN_X + col * PITCH_X`, `y = ORIGIN_Y + row * PITCH_Y`).
Po jednym `<line data-from data-to>` na połączenie z `world.connections` (kolejność
zachowana; końce w środkach węzłów; linie przed węzłami w DOM). Obsada: w grupie
regionu znacznik z `data-settlement` / `data-party` (= nazwa regionu) i
`data-owner` (`owner_id` lub `""`) przy środku węzła, gdy `settlement_at` /
`party_at` zwraca obsadę. **Paleta właścicieli (V13.2d):**
`tbbui.palette.owner_palette(world) -> dict[str, str]` zbiera odrębne niepuste
`owner_id` w kolejności pierwszego wystąpienia (iteracja `world.regions`; w
regionie osada, potem party) i przypisuje kolory z ustalonej, cyklicznej listy
`OWNER_COLORS`. `render_world_svg` ustawia `fill` znacznika z tej palety; brak
właściciela → `NEUTRAL_OWNER_COLOR`. Czyste, deterministyczne, bez mutacji mapy.

**Geometria heksów bitwy (V13.3a):** `tbbui.hexgeom` — czyste funkcje
pointy-top: `hex_to_pixel(hex, size) -> (x, y)` (axial → piksel środka) oraz
`hex_corners(hex, size) ->` 6 narożników na okręgu o promieniu `size` wokół
środka (kąty `60°·i − 30°`). Stdlib only; fundament pod SVG pola bitwy.

**SVG pola bitwy (V13.3b):** `tbbui.battlesvg.render_battle_svg(battle) -> str`
— parsowalny XML z korzeniem `<svg>`; heksy w osiowej obwiedni zajętych pozycji
(`battle.units`) rozszerzonej o ±1 w `q` i `r`; każdy heks to `<polygon>` z
`data-q`/`data-r`, narożnikami z `hex_corners` i `fill` zależnym od nazwy terenu
(`battlefield.terrain_at`). Po jednym znaczniku na zajęty heks
(`data-side`/`data-hp`/`data-stunned`) w środku z `hex_to_pixel`. Czyste,
deterministyczne, bez mutacji `battle`.

**Strona HTML partii (V13.4a):** `tbbui.gamepage.render_game_page(world, game,
calendar) -> str` — parsowalny HTML z korzeniem `<html>`; osadza kanoniczny
string z `render_world_svg(world)`; element `data-calendar` z `data-year` /
`data-month` z podanego `Calendar`; po jednym elemencie `data-duchy` (=
`duchy_id`) na każde `game.duchies` z `data-morale`, `data-settlements` i
`data-parties` (liczby); element `data-result` = `duchy_id` zwycięzcy /
`draw` / `ongoing` wg `game.is_over` i `game.winner`. Czyste, deterministyczne,
bez mutacji wejść. Serwer podglądu — osobny przyrost (V13.5).

**Snapshot CLI (V13.4b):** `python -m tbbui [ścieżka]` → `tbbui.__main__.main(argv)
-> int`. Rozgrywa deterministyczną partię headless (`create_headless_game` +
`run_headless_game` z ustalonym seedem `73`, jak `python -m tbb`) i zapisuje
`render_game_page` do pliku HTML. Opcjonalny pierwszy argument `argv` to ścieżka
wyjścia (domyślnie `out/game.html`); katalog nadrzędny jest tworzony, gdy nie
istnieje. Zwraca `0`. Dwa uruchomienia z tym samym seedem dają identyczną treść.

**Routing podglądu (V13.5a / K14.1b / K14.2a–b):** `tbbui.serve.GameApp(world, game,
calendar, rng, player_duchy_id=None)` trzyma stan partii w pamięci i udostępnia
czystą metodę `handle(method, path) -> (kod_http, treść)` — bez gniazda HTTP.
`GET /` → `(200, strona)` z `render_game_page` plus znacznik
`data-player` (wartość `player_duchy_id` lub `""` gdy `None`) oraz formularze
`<form method="post" action="/turn">`,
`<form method="post" action="/order/recruit">` i
`<form method="post" action="/order/muster">`. `POST /turn` → jedna tura przez
`run_headless_game(..., max_turns=1, calendar=..., player_duchy_id=...)` i
aktualizacja wewnętrznego stanu (gdy podany `player_duchy_id`, driver pomija
AI tego księstwa — K14.1a); gdy `game.is_over` przed żądaniem, no-op (stan bez
zmian, wciąż `200`). Rozkazy gracza `POST /order/recruit` (K14.2a) i
`POST /order/muster` (K14.2b) idą wspólnym helperem `_apply_player_order(transition)`:
gdy `player_duchy_id` ustawiony, gra nie jest `is_over` i księstwo gracza
istnieje w `game.duchies`, stosuje `transition(world, player_duchy)`
(`ai.recruit_duchy_unit` / `ai.muster_duchy_party`), podmienia `world` i
re-synchronizuje `game = game.sync_from_world(world)`; w przeciwnym razie no-op;
zawsze `(200, strona)`. Inna ścieżka lub metoda → `(404, treść)`. Determinizm: ten
sam seed i sekwencja `handle` → te same treści i stan. `player_duchy_id=None`
zachowuje zachowanie obserwatora AI-vs-AI.

**Serwer podglądu (V13.5b / K14.1b):** cienki adapter nad `GameApp.handle`:
`handle_request(app, method, path) -> (kod, bajty UTF-8)` oraz
`make_server(app, host="127.0.0.1", port=0) -> http.server.HTTPServer`.
Handler GET/POST deleguje do `handle_request`, ustawia status i
`Content-Type: text/html; charset=utf-8`. `make_server` tylko wiąże gniazdo
(port `0` = efemeryczny); nie woła `serve_forever`. CLI:
`python -m tbbui serve [port]` tworzy świeżą deterministyczną partię
(`create_headless_game` + `Rng(73)` + `Calendar()`), `GameApp` z
`player_duchy_id="player"` (single-player) i `make_server`, potem
`serve_forever()`.

## 2. Struktura katalogów
```
game/                     # katalog projektu (repo root dla tej gry)
├── docs/
│   ├── DESIGN.md         # żywy projekt gry (mechanika, wizja)
│   └── ARCHITECTURE.md   # ten plik
├── src/
│   ├── tbb/              # pakiet rdzenia ("Total Battle Brothers")
│   │   ├── __init__.py   # wersja + publiczne API
│   │   ├── __main__.py   # headless entry point (python -m tbb)
│   │   ├── ai.py         # czyste, deterministyczne kwerendy AI strategicznego
│   │   ├── battle.py     # niemutowalny stan bitwy: teren + rozstawienie jednostek
│   │   ├── battlefield.py # rzadka plansza heksowa Hex→Terrain z domyślnym terenem
│   │   ├── building.py   # niemutowalne typy budynków i katalog startowy
│   │   ├── combat.py     # czyste, deterministyczne wyliczenia reguł walki
│   │   ├── driver.py     # headless driver partii: przeżycie bohatera + pętla tur
│   │   ├── duchy.py      # niemutowalne księstwo: identyfikator, bohater i morale
│   │   ├── game.py       # niemutowalny stan końca gry nad zbiorem księstw
│   │   ├── hex.py        # niemutowalne współrzędne heksów axial/cube
│   │   ├── party.py      # niemutowalny bohater i skład armii strategicznej
│   │   ├── terrain.py    # niemutowalne typy terenu i katalog startowy
│   │   ├── turn.py       # kalendarz i niemutowalna maszyna faz strategicznej tury
│   │   ├── progression.py # krzywa skumulowany nakład → poziom filaru
│   │   ├── resources.py  # niemutowalne wartości pszenicy i złota
│   │   ├── settlement.py # niemutowalna osada z pulą populacji
│   │   ├── unit.py       # niemutowalna jednostka i pochodne statystyki bojowe
│   │   ├── wound.py      # niemutowalne rany czasowe/trwałe i katalog startowy
│   │   ├── world.py      # niemutowalny graf regionów i rozmieszczenie osad
│   │   └── rng.py        # seedowalny RNG izolowany od stanu globalnego
│   └── tbbui/            # pakiet prezentacji (stdlib SVG/HTML); tbb go nie importuje
│       ├── __init__.py
│       ├── __main__.py   # CLI: snapshot HTML lub `serve [port]` (python -m tbbui)
│       ├── hexgeom.py    # geometria heksów pointy-top (hex→pixel, narożniki)
│       ├── battlesvg.py  # SVG pola bitwy heksowej (heksy + znaczniki jednostek)
│       ├── layout.py     # deterministyczny layout regionów WorldMap → (col, row)
│       ├── palette.py    # paleta kolorów właścicieli (owner_id → fill)
│       ├── worldsvg.py   # SVG mapy strategicznej (węzły + linie + znaczniki)
│       ├── gamepage.py   # HTML strony partii (mapa + kalendarz + księstwa + wynik)
│       └── serve.py      # GameApp + handle_request + make_server (V13.5)
├── tests/                # testy pytest (mirror struktury src/)
│   ├── test_battle.py
│   ├── test_ai.py
│   ├── test_rng.py
│   ├── test_battlefield.py
│   ├── test_building.py
│   ├── test_combat.py
│   ├── test_driver.py
│   ├── test_duchy.py
│   ├── test_game.py
│   ├── test_hex.py
│   ├── test_party.py
│   ├── test_terrain.py
│   ├── test_turn.py
│   ├── test_progression.py
│   ├── test_resources.py
│   ├── test_settlement.py
│   ├── test_unit.py
│   ├── test_wound.py
│   ├── test_world.py
│   ├── test_layout.py    # layout mapy strategicznej (tbbui)
│   ├── test_palette.py   # paleta kolorów właścicieli (tbbui)
│   ├── test_worldsvg.py  # SVG mapy: węzły + linie + znaczniki (tbbui)
│   ├── test_battlesvg.py # SVG pola bitwy heksowej (tbbui)
│   ├── test_gamepage.py  # HTML strony partii (tbbui)
│   ├── test_ui_main.py   # CLI snapshot partii (python -m tbbui)
│   ├── test_serve.py     # GameApp.handle routing podglądu (tbbui, V13.5a)
│   ├── test_ui_serve.py  # make_server + handle_request (tbbui, V13.5b)
│   └── test_smoke.py
├── scripts/
│   ├── test.sh           # uruchamia pełny pakiet testów
│   ├── build.sh          # no-op dla Pythona (jest, by kontrakt komend był spójny)
│   └── run.sh            # uruchamia headless runner
├── pyproject.toml        # konfiguracja pytest (pythonpath=src) + metadane
├── BACKLOG.md            # kolejka zadań
├── LICENSE
└── .gitignore
```

Konwencja: **każdy moduł w `src/tbb/foo.py` ma test `tests/test_foo.py`.**
Moduły prezentacji: **`src/tbbui/foo.py` → `tests/test_foo.py` albo `tests/test_ui_foo.py`**
(prefiks `test_ui_` opcjonalnie, by sygnalizować warstwę).

## 3. Komendy (kontrakt dla orkiestratora)
Wszystkie to **pojedyncze** komendy bez operatorów powłoki; złożone kroki są
w skryptach `scripts/`.

| cel   | komenda            |
|-------|--------------------|
| test  | `bash scripts/test.sh`  |
| build | `bash scripts/build.sh` (no-op, kończy się 0) |
| run   | `bash scripts/run.sh`   |

- **test.sh** → `python3 -m pytest -q` z katalogu projektu. `pyproject.toml`
  ustawia `pythonpath = ["src"]`, więc `import tbb` działa bez instalacji.
- **build.sh** → brak kompilacji (Python); istnieje dla spójności kontraktu.
- **run.sh** → `python3 -m tbb` (pełna deterministyczna partia headless).

Uruchamiaj z katalogu `game/`.

## 4. Konwencje kodu i testów
- **TDD:** najpierw czerwony test, potem minimalny kod do zieleni, potem refaktor.
- **Determinizm:** żadnego `random` globalnego w rdzeniu — RNG wstrzykiwany
  (`tbb`-owy wrapper z seedem). Testy z ustalonym seedem.
- **Rdzeń czysty:** `tbb` nie importuje `tbbui` ani bibliotek prezentacji/IO w
  ścieżkach logiki. Efekty uboczne (print/plik/sieć) tylko w warstwach
  zewnętrznych (`tbb.__main__`, `tbbui`, skrypty).
- **Typy:** type hints w publicznym API; preferuj `@dataclass` dla encji stanu.
- **Atak dystansowy:** `Unit.ranged_range` ma wartość `0` (brak profilu) albo
  co najmniej `2`; `HexBattle.ranged_attack()` rozstrzyga strzał w tym zasięgu,
  używając wspólnego wzoru trafienia i jednego rzutu wstrzykniętego `Rng`.
- **Rany:** `Wound` jest niemutowalnym modyfikatorem celności i obrony;
  `Unit.wounds` przechowuje niemutowalną krotkę ran, których kary sumują się
  w efektywnych statystykach z podłogą na zero. Miesięczny łańcuch
  `WorldMap.tick_settlements()` kończy `Settlement.tick_healing()`, które
  przesuwa czasowe rany całego garnizonu o jeden miesiąc. Osobne przejście
  `WorldMap.tick_parties()` stosuje `Party.tick_wounds(1)` do każdego party
  w deterministycznej kolejności `world.regions`; graf, osady i regiony bez
  party pozostają bez zmian.
- **Skład party:** `Party` wymaga bohatera `Unit` i kopiuje do krotki maksymalnie
  12 podkomendnych `Unit`; bohater jest osobnym polem i nie wlicza się do limitu.
- **Postęp treningu:** `Unit.train()` reużywa trójkątną krzywą z `progression`;
  autorytatywny poziom pozostaje w `training`, a reszta nakładu przed następnym
  poziomem w `training_progress`.
- **Postęp uzbrojenia:** `Unit.equip()` reużywa tę samą trójkątną krzywą;
  autorytatywny poziom pozostaje w `equipment`, a reszta nakładu przed następnym
  poziomem w `equipment_progress`.
- **Własność strategiczna:** `Party` i `Settlement` mają opcjonalny, niemutowalny
  `owner_id`; kontakt bojowy wymaga niepustych, różnych identyfikatorów obu stron.
- **Kolejność raportu bitwy:** `HexBattle` przechowuje osobny, niemutowalny
  rejestr kolejności rozstawienia aktywnych jednostek. Ruch aktualizuje w nim
  pozycję bez zmiany kolejności, więc kolejność mapy `units` nie wpływa na raport.
- **Małe przejścia stanu:** funkcje przekształcające stan zamiast wielkich metod
  z ukrytymi efektami. `WorldMap.with_settlement` jest wspólnym czystym
  przejściem do wstawiania lub podmiany pojedynczej osady z zachowaniem grafu
  i rozmieszczenia party.
- **Headless driver:** na początku każdej wykonywanej tury `run_headless_game`
  woła `tick_settlements()`, zaraz potem `tick_parties()`, a następnie
  `sync_from_world` — zanim rozpocznie przebieg księstw. Przed każdym
  `take_duchy_turn` buduje `morale_by_owner` z bieżącego `GameState`
  (`{duchy_id: morale}`) i przekazuje do polityki AI. Opcjonalny
  `player_duchy_id` pomija `take_duchy_turn` (oraz następującą sukcesję
  bohatera z akcji) dla wskazanego księstwa; tick ekonomii, `raise_duchy_hero`
  i `designate_duchy_heir` nadal obejmują wszystkie księstwa (K14.1a). Driver
  przewleka niemutowalny `Calendar`, kończy każdą wykonaną turę przez
  `turn.end_turn` i zwraca mapę, stan gry oraz kalendarz; CLI odbiera całą
  trójkę i wypisuje wynik wraz z końcowym rokiem i miesiącem, nie wyliczając
  czasu samodzielnie.
- **Nazwy:** moduł ↔ test 1:1 (patrz wyżej).

## 5. Uruchamianie lokalnie (dla człowieka)
```
cd game
bash scripts/test.sh     # testy
bash scripts/run.sh      # headless runner
```
Wymagania: Python 3.11+ i pytest (`python3 -m pip install pytest`, jeśli brak).
