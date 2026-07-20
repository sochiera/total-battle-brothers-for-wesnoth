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
│       └── layout.py     # deterministyczny layout regionów WorldMap → (col, row)
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
  (`{duchy_id: morale}`) i przekazuje do polityki AI. Driver przewleka
  niemutowalny `Calendar`, kończy każdą wykonaną turę przez `turn.end_turn` i
  zwraca mapę, stan gry oraz kalendarz; CLI odbiera całą trójkę i wypisuje
  wynik wraz z końcowym rokiem i miesiącem, nie wyliczając czasu samodzielnie.
- **Nazwy:** moduł ↔ test 1:1 (patrz wyżej).

## 5. Uruchamianie lokalnie (dla człowieka)
```
cd game
bash scripts/test.sh     # testy
bash scripts/run.sh      # headless runner
```
Wymagania: Python 3.11+ i pytest (`python3 -m pip install pytest`, jeśli brak).
