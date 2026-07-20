# DESIGN — Total Battle Brothers (nazwa robocza)

> **Dokument żywy.** Źródło prawdy o *mechanice i wizji* gry — **wyłącznie aktualny
> stan reguł**. Historia rozstrzygnięć: `DECISIONS.md` (jednoliniowo) oraz git /
> `.forge/tasks/`. Decyzje techniczne: `ARCHITECTURE.md`. Kolejka: `../BACKLOG.md`.

## 1. Pitch
Single-player **sandbox** (bez scenariuszowej kampanii): turowa strategia łącząca
zarządzanie osadami i armiami z taktycznymi bitwami na heksach, w stylu **Battle
for Wesnoth** i **Battle Brothers**. Gracz prowadzi jedno księstwo przeciw
księstwom sterowanym przez **AI**. Skala kameralna: małe osady, nieliczne wojska,
każda jednostka się liczy.

## 2. Klimat i ton
Średniowiecze **bez magii i fantastyki**. Surowy, realistyczny ton. Śmierć jest
prawdziwa i najczęściej permanentna.

## 3. Struktura rozgrywki — dwie warstwy
Gra ma dwie sprzężone warstwy. Rdzeń logiki obu jest oddzielony od prezentacji
(patrz `ARCHITECTURE.md`) i budowany w TDD.

### 3.1 Warstwa strategiczna (mapa świata, turowa)

**Mapa i regiony.** Skończony, niemutowalny graf regionów. `Region` ma niemutowalne
`name`; połączenia są dwukierunkowe; ruch tylko między sąsiadami. Region ma
najwyżej jedną `Settlement` (może być pusty). Kolejność regionów z konstrukcji mapy
wyznacza deterministyczną kolejność zapytań o sąsiadów.

**Party na mapie.** Pozycja = region; `WorldMap` trzyma `Region → Party` (max jedno
party na region). Osada nie zajmuje slotu party — party może stać w regionie
z osadą. Zapytania: `party_at(region)`; przejście: `place_party()` (odrzuca region
spoza grafu i zajęty).

**Ruch.** `move_party` przenosi całe party (bohater + podkomendni) do wolnego,
bezpośrednio sąsiedniego regionu. Koszt połączenia = **1 punkt ruchu**; budżet
przejścia jest jawnym argumentem (≥ 1). Wejście na region już zajęty przez party
jest odrzucane. Mapa wejściowa, osady i garnizony nie są mutowane.

**Bitwa party↔party.**
- `start_battle(source, destination)` — sąsiednie regiony z party, jawni różni
  `owner_id` — tworzy `HexBattle` bez mutacji mapy. Inicjator = ATTACKER, cel =
  DEFENDER. Skład: bohater, potem podkomendni; rozstawienie = rozłączne rzędy na
  Plains (placeholder).
- `apply_party_battle_result(source, destination, result, battle=None)` —
  `ATTACKER_WIN`: broniący znika, atakujący przechodzi na `destination`;
  `DEFENDER_WIN`: atakujący znika; `DRAW`: znikają oba. Walidacja jak `start_battle`.
- `resolve_party_battle_recorded(...) -> (WorldMap, HexBattle)` składa start →
  `auto_resolve` → apply i zwraca mapę + rozstrzygniętą bitwę (bez dodatkowego
  RNG). Zwycięskie party ma skład z ocalałych; remis → oba znikają.
  `resolve_party_battle` deleguje i zwraca tylko mapę. `move_points` placeholder
  (domyślnie `1`); `attacker_morale` / `defender_morale` (domyślnie `0`/`0`).

**Bitwa party↔osada (szturm).**
- `start_settlement_battle` — party w `source` vs osada w sąsiednim `destination`,
  różni właściciele; tworzy `HexBattle` (party = atak, garnizon = obrona) bez
  mutacji mapy/osady/garnizonu.
- `apply_settlement_battle_result(source, destination, result, battle=None)` —
  `ATTACKER_WIN` (**podbój**): `owner_id` osady → właściciel atakującego, party
  na `destination` (odrzucane jeśli region zajęty innym party); `DEFENDER_WIN` /
  `DRAW`: atakujący znika, owner bez zmian. Z `battle`: garnizon z ocalałych
  obrońców (`absorb_defenders`); bez `battle`: garnizon nietknięty (zgodność wstecz).
- `resolve_settlement_battle_recorded(...) -> (WorldMap, HexBattle)` składa
  start → auto_resolve → apply i zwraca mapę + rozstrzygniętą bitwę (bez
  dodatkowego RNG). `resolve_settlement_battle` deleguje i zwraca tylko mapę.
  Parametry morale i `move_points` jak w BM.1.

**Własność.** `Party` i `Settlement` mają opcjonalny `owner_id` (tekst księstwa).
Rozpoczęcie bitwy wymaga jawnego właściciela po obu stronach; równe id = sojusznik
(blokada), różne = wrogowie, brak = blokada.

**Rekonstrukcja ocalałych.**
- `HexBattle.side_survivors(side)` — jednostki strony na planszy (aktywne +
  ogłuszone) w `_deployment_order` (przeplatane; slot 0 = bohater).
- `Party.reconstruct(original, survivors)` — slot 0 = hero, reszta = units;
  `owner_id` z original; ocalali zachowują rany/XP, wracają z `stunned=False`;
  pusta sekwencja odrzucona; limit 12 podkomendnych.
- apply_* z `battle` rekonstruje party pozostające na mapie; bez `battle` —
  placeholderowy skład.

**AI rozwoju i tury księstwa.**
- `develop_duchy_settlement(world, duchy)` — w pierwszej własnej osadzie (kolejność
  regionów) otwiera pierwszy brakujący budynek **Farm → Smith → Market**, jeśli
  starczy wolnej populacji; max jeden budynek; brak kandydata = no-op; bez RNG.
- `take_duchy_turn(world, duchy, rng, morale_by_owner=None)` — stała kolejność:
  **rozwój → rekrutacja → akcja wojskowa**; wynik każdego kroku jest wejściem
  następnego; opcjonalne `morale_by_owner` idzie do akcji wojskowej.

**Czas.** 1 tura = **1 miesiąc**. Rok = **13 miesięcy** × 4 tygodnie. Start: rok 1,
miesiąc 1; po miesiącu 13 → miesiąc 1 kolejnego roku. Kalendarz trzyma tylko rok
i miesiąc.

**Bohater i księstwo.** Dokładnie **jeden** bohater na księstwo — król i dowódca;
armia rusza się wyłącznie z bohaterem. Bez bohatera jednostki stoją lub bronią
osady jako garnizon.
- `Duchy`: niepusty `duchy_id`, wymagany `hero: Unit` (lub `None` w stanie
  bezhetmańskim), podpisany `morale` (domyślnie 0), opcjonalny `heir: Unit | None`
  (nie ten sam obiekt co hero), krotki `settlements` / `parties` (kopiowane;
  każdy `owner_id == duchy_id`).
- Sukcesja `succeed()`: z dziedzicem — heir→hero, heir=None, morale
  −`SUCCESSION_MORALE_PENALTY` (placeholder `2`); bez dziedzica — `hero=None`,
  ta sama kara; `has_hero`.
- `is_defeated` = `True` iff `has_hero is False` **i** `settlements == ()`
  (party nie wpływają).
- `GameState(duchies)`: unikalne `duchy_id`; `contenders` = niepokonani;
  `is_over` gdy `len(contenders) ≤ 1`; `winner` = jedyny pretendent lub `None`.

**Party (skład).** `Party`: wymagany `hero` + krotka ≤ **12** podkomendnych;
bohater **nie** wlicza się do limitu 12.

**Strony startowe.** Każde księstwo startuje z **1–3 osadami**. Brak neutralnych
band — przeciwnikami są księstwa AI.

### 3.2 Warstwa bitwy (heksy, turowa)
Turowa siatka heksów; gracz steruje jednostkami indywidualnie.

**Teren.** `Terrain(move_cost ≥ 1, defense_mod, accuracy_mod)`. Katalog:
- **Plains** — `1, 0, 0`
- **Forest** — `2, +2, −1`
- **Hills** — `2, +1, +1`

`Battlefield`: rzadkie `Hex → Terrain`, domyślnie Plains; zapytania
`terrain_at` / `move_cost_at` / `defense_at` / `accuracy_at`.

**Geometria.** Axial `(q, r)` + cube; `Hex.distance`, sąsiedzi; `Hex.line_to(other)`
— sekwencja `distance+1` heksów, cube-interpolacja, deterministyczna reguła remisu.

**Atak dystansowy.** `Unit.ranged_range` (domyślnie `0`). `≥ 2` → strzał na dystans
`2…ranged_range`; ten sam wzór trafienia i `Unit.damage`; jeden rzut RNG; bez
kontrataku. Jednostka na heksie pośrednim linii blokuje strzał przed RNG.

**Morale.** Wpływa **wyłącznie na celność** (podpisany modyfikator); **nie** powoduje
ucieczek. W auto-rozgrywce i resolve mapy: **per strona**
(`attacker_morale` / `defender_morale`).

**Szansa trafienia (zwarcie i dystans):**
`clamp(50 + accuracy_att + accuracy_mod_terenu_att + morale
 − defense_def − defense_mod_terenu_def, 5, 95)`.

**Rany.** Niemutowalny mod `accuracy`/`defense`; `duration_months=None` = trwała.
Kary sumują się; efektywne statystyki ≥ 0. Katalog: **Bruise** (2 mies., −1/−1),
**Maimed** (trwała, −2/−2). `Unit.tick_wounds(months=1)` starzeje rany czasowe.
`Settlement.tick_healing()` w łańcuchu miesięcznym; `WorldMap.tick_parties()`
stosuje `Party.tick_wounds(1)` w kolejności regionów (driver po `tick_settlements`).

**0 HP.** Jeden rzut 50/50: śmierć (usunięcie) albo `stunned=True` + Bruise.
Ogłuszona nie rusza się ani nie atakuje. `Unit.stunned` (domyślnie `False`);
`HexBattle.resolve_defeat(position, rng)`.

**Koniec bitwy.** Aktywna = HP > 0 i nie ogłuszona. Wygrywa strona z jedynymi
aktywnymi; obie bez aktywnych → remis.

**Raport.** Wynik + poległe / ogłuszone / zdolne per strona; rejestr poległych
w `HexBattle`; kolejność deterministyczna.

**Doświadczenie.** Ocalali (aktywni + ogłuszeni) +**1** XP; polegli bez nagrody.

**Deployment i ruch.** `HexBattle`: `Battlefield` + mapa `Hex → Unit` (max 1/heks).
`deploy` / `move(source, destination, move_points)` / `reachable` — koszt = suma
`move_cost` wchodzonych heksów po najtańszej ścieżce; inne jednostki blokują.
Bieżące HP = max przy deploy; obrażenia z podłogą 0. Strony ATTACKER/DEFENDER;
atak wręcz tylko wrogowie-sąsiedzi; 1 rzut RNG.

**Driver bitwy.**
- `nearest_enemy(position)` — najbliższa aktywna wroga; remis: `_deployment_order`.
- Tura jednostki: sąsiad → 1 atak wręcz (+ resolve 0 HP); inaczej ruch ku celowi
  `(dist, q, r)`; albo atak, albo ruch.
- `auto_resolve(move_points, rng, attacker_morale=0, defender_morale=0)` — rundy
  do wyniku lub `max_rounds=1000`; snapshot kolejności na rundę; morale per strona.

**Morale w AI/driverze.** `assault_nearest_enemy_settlement` /
`take_duchy_military_action` / `take_duchy_turn` przyjmują opcjonalne
`morale_by_owner: dict[owner_id, morale]`. `run_headless_game` buduje mapę z
bieżącego `GameState` przed każdym `take_duchy_turn`.

## 4. Osady, populacja, ekonomia
- **Surowce:** dokładnie **pszenica** i **złoto** (`Resources`, nieujemne, niemutowalne).
- **Populacja** rośnie przez urodzenia i imigrantów; to pula ludzi na rekrutację
  i obsadę budynków (`staff` per typ). Zamknięcie budynku oddaje obsadę do puli.
- **Ekonomia miesięczna** (`tick_economy`): aktywny (obsadzony) budynek produkuje
  `output`; cała populacja je **1 pszenicę / mieszkaniec / miesiąc**; bilans
  podłogowany na zero. Katalog: **Farm** (`wheat=3`, `staff=1`), **Market**
  (`gold=2`, `staff=1`), **Smith** (output zerowy — uzbrojenie).
- **Urodzenia** (`tick_growth` po ekonomii): +1 wolnej populacji gdy
  `storage.wheat > 0` i poniżej `capacity` (`None` = bez limitu); głód nie rośnie.
- **Imigracja** (`tick_immigration` po growth): +1 gdy `gold > 0` i `wheat > 0`
  i poniżej `capacity`.
- **Łańcuch mapy:** `tick_settlements()` =
  `economy → growth → immigration → training → equipment → healing`.
- **Rekrutacja:** `Settlement.recruit()` — `occupy(1)` + `Unit()` do garnizonu +
  `RECRUIT_GOLD_COST` złota (placeholder `1`); brak populacji/złota → `ValueError`.
- **absorb_defenders(survivors):** zastępuje garnizon; polegli odejmują
  `population` i `occupied` ( `free` bez zmian); sekwencja dłuższa niż garnizon
  odrzucona; ocalali z `stunned=False`.
- **Straty po bitwie osady:** DEF/DRAW + `battle` → absorb obrońców; ATTACKER_WIN
  + `battle` → absorb, potem zmiana owner; bez `battle` garnizon nietknięty.

## 5. Jednostki i progresja
Trzy niezależne filary: **trening**, **uzbrojenie**, **doświadczenie** (tylko walka).

**Statystyki (placeholder liniowy):**
- `hp = 10 + training`
- `accuracy = training + experience`
- `damage = equipment`
- `defense = equipment + experience`

**Nakład → poziom (trening/uzbrojenie):** `T(n) = n·(n+1)/2`,
`level(inv) = (isqrt(8·inv + 1) − 1) // 2`.
- `Unit.train(months)` / `Unit.equip(investment)` — postęp resztkowy
  `training_progress` / `equipment_progress`; 0 = no-op, ujemne = błąd.
- `Settlement.tick_training()`: `TRAINING_MONTHS_PER_TURN` (placeholder `1`) na
  każdego w garnizonie.
- `Settlement.tick_equipment()`: przy Smith + garnizon + `EQUIP_GOLD_COST` złota
  uzbraja jednego o najniższym `equipment` (remis: najwcześniejsza pozycja);
  placeholdery kosztu/inwestycji = `1`.

Jednostki w maszerującym party **nie** trenują/uzbrajają w `tick_settlements`
(leczenie party: `tick_parties`).

## 6. Pętla rozgrywki (MVP)
Najmniejsza grywalna pętla, single-player vs **jedno** księstwo AI:
1. Twoje księstwo: 1 osada z populacją, pszenicą i złotem; naprzeciw AI.
2. Rozwój: rekrutuj, trenuj, wyposażaj.
3. Marsz: bohater prowadzi party; garnizon może zostać w obronie.
4. Bitwa na heksach: teren, wręcz + dystans, morale→celność, rany, śmierć permanentna.
5. Cel: pokonać AI (utrata jego osad **oraz** bohatera).

## 7. Model danych (aktualny)

- **`Resources`** — `{wheat, gold}`, nieujemne; `add`/`subtract` → nowy obiekt.
- **`Unit`** — filary + `training_progress`/`equipment_progress`; stan bojowy
  `{current hp, wounds[], stunned}`; opcjonalnie `ranged_range`.
- **`Settlement`** — populacja (`population`/`occupied`/`free`), budynki, garnizon,
  `storage: Resources`, opcjonalny `owner_id`/`capacity`.
  - `recruit()`, `raise_hero()` → `(osada, świeży Unit())`: population −1,
    `HERO_GOLD_COST` (placeholder `2`), **nie** do garnizonu.
  - `muster(hero)` — garnizon → `Party`; population/occupied −liczba żołnierzy.
  - `absorb_defenders`, `tick_*`, `open_building`.
- **`Party`** — hero + ≤12 units, `owner_id`; `reconstruct`, `tick_wounds`.
- **`Duchy`** — jak §3.1; `succeed()`, `is_defeated`, `has_hero`.
- **`GameState`** — krotka księstw; `sync_from_world(world)` odtwarza
  settlements/parties po `owner_id` w kolejności regionów; `contenders`/`is_over`/`winner`.
- **`WorldMap`** — regiony, connections, osady, party; `move_party`, `muster_party`,
  `start_battle` / `start_settlement_battle`, `apply_*`, `resolve_*`,
  `tick_settlements`, `tick_parties`, `with_settlement`.
- **`HexBattle`** — teren, rozstawienie, strony, HP, resolve_defeat, raport,
  `nearest_enemy`, `take_unit_turn`, `auto_resolve`, `side_survivors`.
- **`Calendar`** — rok, miesiąc; `end_turn` +1 miesiąc.
- **`StrategicTurn`** — faza: **osady → ruch → bitwy → zakończona**; wejście w ruch
  = 1×`tick_settlements`; kalendarz +1 przy końcu bitew; `move_party` tylko w ruchu;
  `start_battle` / `start_settlement_battle` tylko w bitwach.
- **`Rng`** — seedowalny generator.

**Wystawianie bohatera i dziedzica (AI/driver):**
- `ai.raise_duchy_hero(world, duchy)` — gdy brak hero: pierwsza własna osada z
  free≥1 i `HERO_GOLD_COST` złota → `raise_hero`; no-op gdy ma hero lub brak kandydata.
- `ai.designate_duchy_heir(world, duchy)` — gdy ma hero i brak heir: analogicznie
  świeży Unit jako heir; no-op w pozostałych przypadkach.
- Driver woła **raise → designate → take_duchy_turn** dla każdego niepokonanego
  księstwa (z sync po krokach).

**Muster na mapie:** `WorldMap.muster_party(region, hero)` atomowo muster + place
w regionie (wymaga osady i wolnego slotu party).

## 8. AI księstw i driver headless

**Prymitywy wojskowe (czyste, deterministyczne przy ustalonym seedzie):**
- `nearest_enemy_settlement(world, start, owner_id)` — najbliższa wroga osada
  (różny jawny owner); remis: kolejność regionów; brak → `None`.
- `next_march_step(world, start, target)` — sąsiad na najkrótszej drodze; omija
  regiony z party; `None` gdy start sąsiaduje z celem lub brak drogi.
- `march_toward_nearest_enemy(world, position)` — 1 krok, MP=1.
- `assault_nearest_enemy_settlement(world, position, rng, morale_by_owner=None)` —
  resolve gdy cel sąsiad; inaczej no-op.
- `muster_duchy_party` — max jedno party/księstwo; pierwsza własna osada z wolnym
  slotem; no-op gdy party już jest lub brak hero.
- `take_duchy_military_action` — **muster → marsz → szturm** (pozycja party
  ponownie szukana po każdym kroku).
- `recruit_duchy_unit` — 1 rekrut w pierwszej własnej osadzie z free≥1,
  złoto ≥ `RECRUIT_GOLD_COST`, garnizon < **12**.
- `take_duchy_turn` — develop → recruit → military (+ `morale_by_owner`).
- `march_duchy_party` / `march_duchy_party_to(world, duchy, target)` —
  party księstwa (`_duchy_party_position`) + marsz auto / jawny target.
- `assault_duchy_party` / `_recorded` / `assault_duchy_party_to` / `_to_recorded` —
  analogicznie dla szturmu (auto = najbliższa wroga osada); no-op bez
  party/sąsiedztwa/wrogiej osady **bez** RNG; recorded →
  `(WorldMap, HexBattle | None)`.
- `engage_duchy_party_recorded(world, duchy, rng, morale_by_owner=None)` —
  starcie party↔party: pierwsze sąsiednie party z **różnym, jawnym** `owner_id`
  (kolejność `world.neighbors`) → `resolve_party_battle_recorded`; morale z
  `morale_by_owner` (brak wpisu → `0`); no-op bez party gracza / bez wrogiego
  sąsiada → `(world, None)` **bez** RNG.

**Setup i pętla:**
- `create_headless_game()` → `WorldMap` + `GameState` z księstwami `player` i `ai`;
  każde: 1 bohater zdolny do obrażeń, 1 własna osada z populacją i dodatnimi
  zapasami wheat/gold na przeciwnych końcach mapy; party puste; stały, bez RNG.
- `driver.resolve_hero_survival(duchy, world_before, world_after)` — party było
  przed i brak po (po `owner_id`) → `succeed()`; obecność party = zgodny owner_id.
- `driver.run_headless_game(world, game, rng, max_turns=1000, calendar=Calendar(),
  player_duchy_id=None) → (WorldMap, GameState, Calendar)`.
  - Wejście już `is_over` lub `max_turns == 0` → dokładnie wejściowe obiekty.
  - Każda tura: `tick_settlements` → `tick_parties` → `sync_from_world`; potem
    przebieg niepokonanych księstw (migawka id z początku tury):
    `raise_duchy_hero` → `designate_duchy_heir` → (budowa `morale_by_owner`) →
    `take_duchy_turn` (pomijane gdy `duchy_id == player_duchy_id`) →
    `resolve_hero_survival` → sync.
  - Koniec natychmiast przy `is_over` (także w środku tury); po ukończonej turze
    kalendarz +1 miesiąc.
  - Bazowa partia (seed `73`, domyślny `max_turns`): **remis na bezpieczniku**
    (`winner is None`, kalendarz rok 77 / miesiąc 13) — skutek sukcesji i
    landless-bohatera; zamierzone.
- CLI: `python -m tbb` (`run.sh`) — create + run + wypis winner/draw + rok/miesiąc;
  exit 0. Driver używa `take_duchy_turn` bezpośrednio (nie maszyny faz
  `StrategicTurn` w pętli headless).

## 9. Zasady projektowe
- **Determinizm:** cała losowość przez wstrzykiwany, seedowalny RNG.
- **Rdzeń bez prezentacji:** logika nie importuje UI/render.
- **Małe, czyste przejścia stanu** zamiast metod z efektami ubocznymi.

## 10. Poza zakresem (na start)
Scenariuszowa kampania/fabuła, multiplayer sieciowy, magia/fantastyka, oddziały
masowe (np. 60 ludzi w jednostce), grafika AAA/dźwięk, edytor map.

## 11. Warstwa wizualna (`tbbui`)
Rdzeń zostaje bez importów UI; prezentacja to osobny pakiet **stdlib**:
deterministyczne SVG/HTML + `http.server`; wyświetlacz = przeglądarka. Rdzeń
`tbb` nigdy nie importuje `tbbui`.

**Render:**
- `render_world_svg(world)` — węzły `g[data-region]`, etykiety, `<line>` na
  connections (`data-from`/`data-to`), znaczniki osady/party (`data-settlement` /
  `data-party` + `data-owner`), `fill` z `owner_palette(world)` (cykliczna paleta;
  `None` → kolor neutralny).
- `tbbui.hexgeom` — pointy-top `hex_to_pixel` / `hex_corners`.
- `render_battle_svg(battle)` — heksy obwiedni zajętych ±1, znaczniki
  `data-side`/`data-hp`/`data-stunned`.
- `render_battle_report(battle)` — fragment `data-battle-report` z wynikiem i
  stratami per strona z `HexBattle.report()`.
- `render_game_page(world, game, calendar, battle=None)` — SVG mapy, kalendarz
  (`data-calendar`), panel księstw (`data-duchy`), wynik (`data-result`), opcjonalnie
  SVG bitwy i raport bitwy gdy `battle` podane.

**GameApp / rozkazy gracza:**
- `GameApp(..., player_duchy_id=None)` — w `POST /turn` woła `run_headless_game`
  z `max_turns=1` i tym id; `GET /` ma `data-player`. CLI `python -m tbbui serve`
  ustawia `player_duchy_id="player"`.
- Wspólny warunek rozkazu: ustawiony gracz, gra nie `is_over`, księstwo w
  `game.duchies` → `_apply_player_order` + `sync_from_world`; inaczej no-op;
  zawsze `(200, strona)`.
- `POST /order/recruit|muster|develop` → `recruit_duchy_unit` /
  `muster_duchy_party` / `develop_duchy_settlement`.
- `POST /order/march` / `?target=<region>` — parse `target` przez
  `_order_target_region` (`parse_qs`, dopasowanie `Region.name`); znany target →
  `march_duchy_party_to`; brak/nieznany → `march_duchy_party`.
- `POST /order/assault` / `?target=` — `assault_duchy_party_to_recorded` /
  `assault_duchy_party_recorded` z `morale_by_owner` z `game.duchies` i
  `self.rng`; wynikowa `HexBattle` trafia do `last_battle` (no-op / guardy
  zostawiają `last_battle` bez bitwy).
- `POST /order/engage` — `engage_duchy_party_recorded` (auto-cel: pierwsze
  sąsiednie wrogie party) z tymi samymi guardami i `morale_by_owner` /
  `self.rng` co szturm; przez `_apply_player_assault_order`; na hit ustawia
  `last_battle`, no-op/guardy bez zmian. GET `/` ma bare formularz
  `action="/order/engage"`.
- `GameApp.last_battle: HexBattle | None` — init `None`; `_render` przekazuje
  `battle=self.last_battle` do `render_game_page` (SVG + raport bitwy w stronie
  po szturmie / starciu). `POST /turn` oraz rozkazy nie-bitewne
  (`/order/recruit|muster|develop|march`) zerują `last_battle` (stara bitwa nie
  wisi po innym działaniu gracza); `assault`/`engage` nie zerują przed wykonaniem.
- UI celów: gdy gracz ma party na mapie — po jednym formularzu
  `?target=<quote(nazwa)>` na obcą osadę (kolejność `world.regions`, helper
  `_march_targets`); bare action nieobecny. Brak party / brak id / gra skończona →
  pojedynczy bare formularz.

**PLAN K14 (rozkazy gracza w podglądzie, single-player):** obserwator K13 rusza
obie strony jako AI. K14 daje graczowi sprawczość: steruje **jednym** księstwem
(`player`), AI resztą. „Następna tura" odpala wyłącznie AI —
`run_headless_game` dostaje `player_duchy_id` i pomija `take_duchy_turn` tego
księstwa (tick ekonomii, sukcesja i wyznaczanie dziedzica zostają). `GameApp`
przechowuje `player_duchy_id` i przewleka go do drivera. Rozkazy `POST /order/*`
reużywają prymitywów AI; po rozkazie mapa + `sync_from_world`. Wybór celu/osady
w K14 pozostaje automatyczny (placeholder) — K15 dodaje jawny cel. Rdzeń `tbb`
nie importuje `tbbui`.

**PLAN K15 (wybór celu przez gracza):** gracz wskazuje *dokąd* maszeruje i *którą*
sąsiednią wrogą osadę szturmuje. Prymitywy `march_duchy_party_to` /
`assault_duchy_party_to`; routing `?target=`; brak target → dotychczasowe auto
prymitywy; formularze per region-cel. Bez zmiany rozstrzygania bitwy ani morale.

**PLAN K16 (obserwowalna bitwa w podglądzie):** opcjonalny slot `battle` w
`render_game_page`; `resolve_settlement_battle_recorded`;
`assault_duchy_party_to_recorded` / `assault_duchy_party_recorded`; `GameApp`
trzyma ostatnią bitwę ze szturmu i przekazuje do strony (K16.1d). Nagranie nie
zmienia rozstrzygania ani morale.

**PLAN K17 (czytelny wynik bitwy):** K16 pokazał SVG bitwy, ale nie jej wynik.
K17 dokłada czysty prymityw `tbbui.battlereport.render_battle_report(battle)`
(fragment `data-battle-report` z `data-battle-result` i per-stroną
`data-battle-side`/`data-fallen`/`data-stunned`/`data-active` z
`HexBattle.report()`), a `render_game_page(..., battle=…)` osadza go obok SVG
bitwy. Bez zmian w rdzeniu `tbb.battle`; `GameApp` dostaje raport przez istniejące
przekazanie `last_battle`.

**PLAN K18 (starcie party↔party gracza):** gracz szturmuje tylko osady, więc
bezosadowy, wędrujący bohater AI kończy bazową partię remisem. K18 wystawia
graczowi bitwę party↔party: rdzeń dokłada `WorldMap.resolve_party_battle_recorded`
(nagrana wersja `resolve_party_battle`), `ai.engage_duchy_party_recorded` atakuje
pierwsze sąsiednie wrogie party (auto-cel, no-op bez RNG), a `GameApp` udostępnia
rozkaz `POST /order/engage` reużywający `_apply_player_assault_order` +
`last_battle`. Jawny wybór celu party — Kamień 19.

**PLAN K19 (jawny wybór celu starcia party↔party):** jak K15 dla szturmu, K19
odwraca placeholder auto-celu: prymityw `ai.engage_duchy_party_to_recorded(world,
duchy, target, rng, morale_by_owner=None)` (jawny sąsiedni wrogi `target`, no-op
`(world, None)` bez RNG); routing `POST /order/engage?target=` (znany target →
`_to_recorded`, brak/nieznany → auto `engage_duchy_party_recorded`); GET `/`
pokazuje po jednym formularzu na sąsiednią wrogą party (helper
`_engage_targets`; inaczej bare form). Bez zmian w rozstrzyganiu bitwy ani morale.

**PLAN K20 (czytelna dla człowieka strona partii):** strona komunikuje stan
atrybutami `data-*` (kontrakt testów), lecz w przeglądarce nie ma widocznego
tekstu. K20 dokłada widoczny banner wyniku (`<p data-result-text>`:
`Gra w toku` / `Remis` / `Zwycięstwo: <duchy_id>`) i czytelny wiersz statusu w
każdym panelu `data-duchy` (nazwa + osady/party/morale); istniejące markery
`data-result`/`data-duchy`/`data-*` bez zmian. Bez zmian w rdzeniu.

## 12. Otwarte pytania (nadal)
- **Krzywe filarów:** różne parametry stromości per filar oraz wpływ budynków/
  mnożników — strojenie przy balansie (bazowa trójkątna krzywa: U3.2 w DECISIONS).
- **Rany:** bogatszy katalog, strategiczne leczenie poza miesięcznym tickiem, balans kar.
- **Wzrost populacji:** tempo urodzeń/imigracji > 1/turę przy dużej nadwyżce.
- **Strojenie wartości** placeholderów (koszty złota, kary morale, wagi XP, MP).
- **Semantyka pełna modyfikatorów terenu** w złożonych przypadkach poza wzorem B4.3a.
- **Granice/kształt planszy bitwy**, amunicja/kary dystansu, typy broni, wycofanie.
- **Rozwój jednostek w party** na mapie (trening/uzbrojenie poza garnizonem).
- **Pełna maszyna faz `StrategicTurn` w driverze headless** (obecnie `take_duchy_turn`).
