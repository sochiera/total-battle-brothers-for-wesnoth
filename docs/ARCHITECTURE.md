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

**Raport bitwy HTML (K17.1a / K21.1b / K21.1c):** `tbbui.battlereport.render_battle_report(battle)
-> str` — parsowalny fragment XML z korzeniem `<div data-battle-report="">`;
konsumuje `battle.report()` (rdzeń bez zmian). Dziecko
`<div data-battle-result="…">` z `report.result.value` (`attacker_win` /
`defender_win` / `draw`); po jednym `<div data-battle-side="attacker|defender">`
z atrybutami `data-fallen` / `data-stunned` / `data-active` = liczności krotek
`BattleSideReport` (kolejność: attacker, potem defender). Obok maszynowych
atrybutów fragment niesie tekst czytelny dla człowieka (K21.1b/c): widoczny
wynik (`Zwycięstwo atakującego` / `Zwycięstwo broniącego` / `Remis` wg
`report.result`) oraz w każdym `data-battle-side` wiersz strat
(`Atakujący/Broniący: polegli N, ogłuszeni M, zdolni K`, zgodny z
`data-fallen`/`data-stunned`/`data-active`). Czyste, deterministyczne,
bez mutacji `battle`.

**Agregacja siły bojowej (R25.1 / R27.1):** `tbbui.unitstrength.combat_totals(units)
-> tuple[int, int, int]` — czysty helper `(hp, attack, defense)` = suma
`Unit.hp` / `Unit.damage` / `Unit.defense` po sekwencji jednostek (pusta →
`(0, 0, 0)`); bez mutacji wejść. `tbbui.unitstrength.wounded_count(units) -> int`
— czysty helper = liczba jednostek z niepustą krotką `wounds` (`len(wounds) > 0`;
pusta sekwencja → `0`); bez mutacji wejść. Oba reużywane przez panele party i osad.

**Panel osad HTML (K22.1a–b / K23.3a / K25.2a–b / K26.1a–b / K27.2a):** `tbbui.settlementpanel.render_settlement_panel(world, player_duchy_id=None)
-> str` — parsowalny fragment XML z korzeniem `<div data-settlement-panel="">`;
po jednym `<div data-settlement-row="<region.name>">` na region z osadą w
kolejności `world.regions` (region bez osady → brak wiersza). Atrybuty wiersza:
`data-owner` (`owner_id` lub `""`), `data-wheat`/`data-gold` (`storage`),
`data-population`/`data-free`/`data-garrison` (`population`/`free`/
`len(garrison)`), `data-garrison-hp` / `data-garrison-attack` /
`data-garrison-defense` (z `combat_totals(garrison)`; pusty → `0`),
`data-buildings` (`len(active_buildings)`), `data-building-names` (nazwy
`active_buildings` złączone `", "`, pusty → `""`) oraz
`data-garrison-wounded` (z `wounded_count(garrison)`; pusty garnizon → `0`). Gdy
`player_duchy_id` nie jest `None`, wiersze z `owner_id == player_duchy_id`
dostają `data-player-owned=""`; `None` (domyślnie) → wynik bajt-w-bajt jak bez
argumentu. Obok atrybutów widoczny tekst
`<Settlement.name> (<owner_id lub „—">): pszenica W, złoto G · populacja P
(wolne F), garnizon N · siła garnizonu: HP H, atak A, obrona D · budynki: B
(nazwa1, …) · ranni: W` (nawias z nazwami tylko gdy `B>0`) zgodny z atrybutami.
Czyste, deterministyczne, bez mutacji `world`; rdzeń bez zmian.

**Panel postępu do celu HTML (K33.1a / K33.1b / K33.2a):**
`tbbui.victoryprogress.render_victory_progress(game, player_duchy_id=None) ->
str` — parsowalny fragment XML z korzeniem `<div data-victory-progress="">`.
Gdy `player_duchy_id` wskazuje księstwo w `game.duchies`, korzeń niesie
`data-enemies-remaining="N"` (`N` = liczba księstw z `duchy_id !=
player_duchy_id` i `not is_defeated`) oraz widoczny tekst
`Wrogów do pokonania: N` zgodny z atrybutem; na każde wrogie księstwo
(`duchy_id != player`, kolejność `game.duchies`, w tym pokonane) dokłada
dziecko `<div data-enemy-duchy="<id>" data-settlements="…" data-hero="true|false"
data-defeated="true|false">` z tekstem `<id>: osady N, bohater tak|nie`
(`N` = `len(settlements)`, `data-hero` z `Duchy.has_hero`, `data-defeated` z
`Duchy.is_defeated`; sufiks ` — pokonany` gdy pokonany). Gdy `player_duchy_id`
jest `None` albo spoza `game.duchies` — sam pusty korzeń (bez
`data-enemies-remaining`, bez wierszy i bez tekstu). Czyste, deterministyczne,
bez mutacji `game`; rdzeń bez zmian.

**Podsumowanie zmian po turze HTML (K38.1a–b):**
`tbbui.turnsummary.render_turn_summary(before, after) -> str` — parsowalny
fragment XML z korzeniem `<div data-turn-summary="">`. `before: GameState |
None`, `after: GameState`. Gdy `before is None` — sam pusty korzeń (bez
`data-changed`, bez `data-change-count`, bez tekstu i dzieci). Gdy `before`
jest `GameState`, korzeń niesie `data-changed="true|false"` oraz
`data-change-count="N"`: `N` = liczba księstw dopasowanych po `duchy_id`
różniących się między `before` a `after` w `(len(settlements), has_hero)`;
`data-changed="true"` iff `N > 0`; widoczny tekst `Zmiany w tej turze: tak|nie`
zgodny z flagą. Na każde zmienione księstwo (kolejność `after.duchies`) —
dziecko `<div data-turn-duchy="<id>" data-settlements-before data-settlements-after
data-hero-before data-hero-after>` z tekstem
`<id>: osady A→B, bohater <tak|nie>→<tak|nie>` (`hero-*` z `Duchy.has_hero`);
księstwa bez zmian nie dają wiersza; `data-change-count` = liczba dzieci
`data-turn-duchy`. Czyste, deterministyczne, bez mutacji `before`/`after`;
rdzeń bez zmian.

**Podpowiedź następnego kroku HTML (K34.1a):**
`tbbui.nextobjective.render_next_objective(game, player_duchy_id=None) -> str`
— parsowalny fragment z korzeniem `<p data-next-objective="TEXT">TEXT</p>`
(atrybut i ciało = te same znaki, `html.escape(..., quote=True)`). Gdy
`player_duchy_id` jest `None` albo spoza `game.duchies` — pusty korzeń
(`TEXT=""`). Inaczej, względem wrogów (`duchy_id != player`, `not is_defeated`):
brak niepokonanych → `Cel osiągnięty: wszyscy wrogowie pokonani`; suma
`len(settlements)` po niepokonanych `S > 0` → `Odbierz wrogie osady
(pozostało: S)`; `S == 0` → `Dobij wrogich bohaterów (pozostało: H)`
(`H` = liczba niepokonanych z `has_hero`). Czyste, deterministyczne, bez
mutacji `game`; rdzeń bez zmian.

**Lokator wrogiego bohatera HTML (K35.1a):**
`tbbui.herolocator.render_enemy_hero_locator(world, game, player_duchy_id=None)
-> str` — parsowalny fragment z korzeniem `<div data-hero-locator="">`. Gdy
`player_duchy_id` wskazuje księstwo w `game.duchies`, korzeń niesie
`data-heroes-on-map="K"` (`K` = liczba wrogich księstw z `has_hero`, których
party stoi na mapie: istnieje region z `world.party_at(region).owner_id ==
duchy_id`) oraz po jednym dziecku `<div data-enemy-duchy="<id>"
data-hero-region="<region|">` na wroga z `has_hero` (kolejność
`game.duchies`; wrogowie bez bohatera bez wiersza). Region = pierwszy w
`world.regions` o zgodnym `owner_id`; tekst `<id>: bohater w <region>` albo
przy braku party na mapie `data-hero-region=""` i `<id>: bohater
niewystawiony`. Gdy `player_duchy_id` jest `None` albo spoza `game.duchies` —
sam pusty korzeń (bez `data-heroes-on-map`, bez wierszy i bez tekstu).
Czyste, deterministyczne, bez mutacji `world`/`game`; rdzeń bez zmian.

**Dystans pościgu HTML (K36.1a–b / K36.2a):** rdzeń dostaje czysty prymityw
grafu `tbb.ai.region_distance(world, start, target) -> int | None` — BFS po
`world.neighbors` (deque jak `next_march_step`), liczba krawędzi najkrótszej
ścieżki; `start==target`→`0`, brak drogi→`None`, region spoza `world.regions`→
`ValueError`; surowy dystans (NIE omija party, w przeciwieństwie do
`next_march_step`); nie mutuje mapy.
`tbbui.herochase.render_hero_chase(world, game, player_duchy_id=None) -> str` —
parsowalny fragment z korzeniem `<div data-hero-chase="">`. Gdy `player_duchy_id`
wskazuje księstwo w `game.duchies`: korzeń niesie `data-player-on-map="true|false"`
(gracz ma party na mapie — pierwszy region w `world.regions` z
`party_at.owner_id == player`), a przy `"false"` brak wierszy. Przy `"true"` na
każdego wroga (`duchy_id != player`) z `has_hero`, którego party stoi na mapie
(kolejność `game.duchies`), dziecko `<div data-enemy-duchy="<id>"
data-distance="<D>">` z `D = region_distance(region_gracza, region_bohatera)` i
tekstem `<id>: D pól marszu`; brak drogi (`None`) → `data-distance=""` i
`<id>: brak drogi`; wiersz o `data-distance="1"` dostaje dodatkowo
`data-in-reach=""` i sufiks „ — w zasięgu" (K36.2a). Wrogowie bez `has_hero`
lub bez party na mapie bez wiersza. `player_duchy_id` `None`/spoza `game.duchies`
→ sam pusty korzeń. Czyste, deterministyczne, bez mutacji `world`/`game`.

**Podgląd siły celu szturmu HTML (K37.1a–b / K37.2a):**
`tbbui.engagementpreview.render_engagement_preview(world, game,
player_duchy_id=None) -> str` — parsowalny fragment z korzeniem
`<div data-engagement-preview="">`. Przy graczu w `game.duchies` z party na
mapie (`first_party_region(world, player_duchy_id)`): korzeń niesie
`data-player-on-map="true"` i `data-own-hp`/`data-own-attack`/`data-own-defense`
z `combat_totals((party.hero, *party.units))`. Na każdy sąsiedni (kolejność
`world.neighbors`) region z jawnym wrogim celem — wiersz
`<div data-target-region data-target-owner data-target-kind="settlement|party"
data-enemy-hp data-enemy-attack data-enemy-defense data-advantage="true|false">`:
osada → siła `combat_totals(garrison)` i tekst „garnizon HP H, atak A, obrona D",
party → siła `combat_totals(hero+units)` i tekst „oddział HP H, atak A, obrona D";
osada przed party w tym samym regionie. `data-advantage="true"` gdy suma własnych
statystyk ≥ suma celu (sufiks „ — przewaga"), inaczej „ — niekorzystnie". Gracz
bez party → `data-player-on-map="false"` bez wierszy; brak/nieznany gracz → sam
pusty korzeń. Osadzony w `render_game_page` zaraz po `data-hero-chase` (K37.1c).
Czyste, deterministyczne, bez mutacji `world`/`game`; rdzeń bez zmian.

**Alert zagrożonych pozycji HTML (K39.1a–c / K39.2a):**
`tbbui.threatalert.render_threat_alert(world, game, player_duchy_id=None) -> str`
— parsowalny fragment z korzeniem `<div data-threat-alert="">`. Gdy
`player_duchy(game, player_duchy_id) is None` (`player_duchy_id` `None` lub
spoza `game.duchies`) → sam pusty korzeń (bez `data-threats`, bez tekstu, bez
dzieci). Przy znanym graczu: `data-threats="N"` i tekst `Zagrożone pozycje: N`
oraz wiersze `data-threatened-region` / `data-threatened-kind` /
`data-enemy-region` / `data-enemy-owner` plus `data-own-hp` /
`data-own-attack` / `data-own-defense` (`combat_totals` garnizonu lub
`hero+units` własnej pozycji) i `data-enemy-hp` / `data-enemy-attack` /
`data-enemy-defense` (`combat_totals` zagrażającego party); tekst wiersza
dostaje sufiks ` · siła obronna: … · siła wroga: …` (kolejność
`world.regions`, w regionie osada przed party; wróg = pierwsze sąsiednie party
z jawnym `owner_id != player_duchy_id` w kolejności `world.neighbors`; `N` =
liczba wierszy). Osadzony w `render_game_page` zaraz po
`data-engagement-preview` (K39.1c). Czyste, deterministyczne, bez mutacji
`world`/`game`; rdzeń bez zmian.

**Lokalizacja party na mapie (R37.1):**
`tbbui.maplookup.first_party_region(world, owner_id) -> Region | None` — pierwszy
region w `world.regions` z `party_at(region).owner_id == owner_id` (inaczej
`None`); czysty, bez mutacji. Reużywany przez `herolocator`, `herochase`
i `engagementpreview` (region gracza / wroga).

**Lokalizacja księstwa gracza (R38.1):**
`tbbui.gamelookup.player_duchy(game, player_duchy_id) -> Duchy | None` —
`None` gdy `player_duchy_id is None`, inaczej pierwsze księstwo w
`game.duchies` o `duchy_id == player_duchy_id`, inaczej `None`; czysty, bez
mutacji `game`. Reużywany przez `playersummary`, `nextobjective`,
`victoryprogress`, `herolocator`, `herochase` i `engagementpreview`.

**Panel party HTML (K22.2a / K24.1a / K25.1a / K25.1b / K27.1a):** `tbbui.partypanel.render_party_panel(world,
player_duchy_id=None) -> str` — parsowalny fragment XML z korzeniem
`<div data-party-panel="">`; po jednym `<div data-party-row="<region.name>">`
na region z party w kolejności `world.regions` (region bez party → brak wiersza).
Atrybuty: `data-owner` (`owner_id` lub `""`), `data-size` (`len(party.units)`),
`data-hp` / `data-attack` / `data-defense` z `combat_totals((hero, *units))`,
`data-wounded` z `wounded_count((hero, *units))`; widoczny tekst
`<region.name> (<owner_id lub „—">): bohater + N podkomendnych · siła: HP H, atak A, obrona D · ranni: W`
zgodny z `data-size`/`data-hp`/`data-attack`/`data-defense`/`data-wounded`. Gdy
`player_duchy_id` nie jest `None`, wiersze z `owner_id == player_duchy_id`
dostają `data-player-owned=""`; `None` (domyślnie) → wynik bajt-w-bajt jak bez
argumentu. Czyste, deterministyczne, bez mutacji `world`; rdzeń bez zmian.

**Legenda właścicieli HTML (K23.1a / K24.2a):**
`tbbui.ownerlegend.render_owner_legend(world, player_duchy_id=None) -> str` —
parsowalny fragment XML z korzeniem `<div data-owner-legend="">`; po jednym
`<div data-owner-legend-row="<owner_id>">` na wpis `owner_palette(world)` w tej
samej kolejności (pierwsze wystąpienie). Atrybuty wiersza: `data-owner`
(= `owner_id`), `data-color` (kolor z palety); widoczny tekst
`<owner_id>: <kolor>` zgodny z atrybutami. Opcjonalny `player_duchy_id` (K24.2a)
— gdy równa się `owner_id` wiersza, ten wiersz dostaje `data-player-owner=""` i
prefiks `» ` przed tekstem; id spoza palety → żaden wiersz nieoznaczony; `None`
(domyślnie) → wynik bajt-w-bajt jak bez argumentu. Brak właścicieli → sam pusty
korzeń (bez wierszy). Czyste, deterministyczne, bez mutacji `world`; rdzeń bez
zmian.

**Podsumowanie księstwa gracza HTML (K30.3a / K30.3b):**
`tbbui.playersummary.render_player_summary(game, player_duchy_id=None) -> str`
— parsowalny fragment XML z korzeniem `<div data-player-summary="">`. Gdy
`player_duchy_id` wskazuje księstwo w `game.duchies`, korzeń ma atrybuty
`data-settlements` / `data-parties` (= `len` osad / oddziałów księstwa),
`data-gold` / `data-wheat` (sumy `settlement.storage.gold` / `.wheat` po
osadach), `data-hp` / `data-attack` / `data-defense` (z
`combat_totals` po bohaterze i podkomendnych każdej party z `duchy.parties`)
oraz widoczny tekst
`Twoje księstwo: osady N, oddziały M · pszenica W, złoto G · siła oddziałów:
HP H, atak A, obrona D` zgodny z atrybutami. Gdy `player_duchy_id` jest
`None` albo spoza `game.duchies` — sam pusty korzeń (bez atrybutów
liczbowych i bez tekstu). Czyste, deterministyczne, bez mutacji `game`;
rdzeń bez zmian.

**Strona HTML partii (V13.4a / K16.1a / K17.1b / K20.1a / K20.1b / K21.1a / K22.1c / K22.2b / K23.1b / K23.2a / K23.3b / K24.1b / K24.2b / K26.2a–b / K27.3a–b / K30.3c / K31.2a / K32.1a / K32.1b / K32.1c / K33.1c / K34.1b / K35.1b / K36.1c / K37.1c / K38.1c / K39.1c):** `tbbui.gamepage.render_game_page(world,
game, calendar, battle=None, player_duchy_id=None, previous_game=None) -> str` — parsowalny HTML z korzeniem `<html>`;
dokładnie jeden `<head>` z `<title>Total Battle Brothers</title>` (K32.1a)
bezpośrednio przed `<body>` (tytuł stały, niezależny od `player_duchy_id` /
`battle`); pierwszym dzieckiem `<body>` jest widoczny nagłówek
`<h1 data-page-title="">Total Battle Brothers</h1>` (K32.1b; stały, niezależny
od `player_duchy_id` / `battle`), zaraz potem stała linia celu
`<p data-objective="…">…</p>` (K32.1c; `_OBJECTIVE_TEXT` =
„Cel: pokonaj księstwo AI — odbierz mu wszystkie osady i pokonaj jego
bohatera"; ta sama treść w atrybucie i w ciele; niezależna od
`player_duchy_id` / `game` / `battle`), potem kanoniczny string z
`render_world_svg(world)`; zawsze osadza też
kanoniczny string z `render_owner_legend(world, player_duchy_id)` (K23.1b /
K24.2b, dokładnie jeden `data-owner-legend` w `<body>`); opcjonalny
`battle: HexBattle | None = None` — gdy podany, osadza w `<body>` kanoniczne
stringi z `render_battle_svg(battle)` (`tbbui.battlesvg`) oraz
`render_battle_report(battle)` (`tbbui.battlereport`); zawsze osadza też
nagłówki sekcji
`<h2 data-panel-section="settlements">Osady</h2>` (K27.3a) bezpośrednio przed
kanonicznym stringiem z `render_settlement_panel(world, player_duchy_id)`
(K22.1c / K23.3b),
`<h2 data-panel-section="parties">Oddziały</h2>` (K27.3b) bezpośrednio przed
kanonicznym stringiem z
`render_party_panel(world, player_duchy_id)` (K22.2b / K24.1b) oraz
`<h2 data-panel-section="duchies">Księstwa</h2>` (K27.3b) bezpośrednio przed
pierwszym wierszem `data-duchy` (kolejność: settlements, parties, duchies);
gdy `None` (domyślnie) wynik jest identyczny bajt-w-bajt jak bez argumentu;
element `data-calendar` z `data-year` / `data-month` z podanego `Calendar` oraz
widocznym tekstem `Rok N, miesiąc M` (K21.1a, zgodnym z atrybutami); opcjonalny
`previous_game: GameState | None = None` (K38.1c) — gdy podany, osadza w
`<body>` dokładnie jeden kanoniczny string z
`render_turn_summary(previous_game, game)` bezpośrednio po `data-calendar`
(niezależnie od `player_duchy_id`); `None` (domyślnie) → bez `data-turn-summary`
(bajt-w-bajt jak bez argumentu); po jednym
elemencie `data-duchy` (= `duchy_id`) na każde `game.duchies` z `data-morale`,
`data-settlements` i `data-parties` (liczby), `data-hero` / `data-heir`
(`"true"`/`"false"` z `Duchy.has_hero` / `heir is not None`) oraz widocznym
tekstem `<duchy_id>: osady N, party M, morale K, bohater tak|nie, dziedzic tak|nie`
(zgodnym z atrybutami); opcjonalny
`player_duchy_id` (K23.2a / K23.3b / K24.1b / K24.2b / K30.3c / K31.2a / K33.1c / K34.1b / K35.1b) — gdy równa się
`duchy_id` wiersza, ten element dostaje `data-player-duchy=""` i prefiks `» `
przed tekstem statusu, w osadzonych panelach osad i party wiersze z
`owner_id == player_duchy_id` dostają `data-player-owned=""`, a w osadzonej
legendzie wiersz z `owner_id == player_duchy_id` dostaje `data-player-owner=""`
i prefiks `» `; gdy `player_duchy_id is not None`, osadza też w `<body>`
kanoniczny string z `render_player_summary(game, player_duchy_id)` (K30.3c,
dokładnie jeden `data-player-summary`), zaraz po nim kanoniczny string z
`render_victory_progress(game, player_duchy_id)` (K33.1c, dokładnie jeden
`data-victory-progress`), zaraz po postępie kanoniczny string z
`render_next_objective(game, player_duchy_id)` (K34.1b, dokładnie jeden
`data-next-objective`), zaraz po podpowiedzi kanoniczny string z
`render_enemy_hero_locator(world, game, player_duchy_id)` (K35.1b, dokładnie
jeden `data-hero-locator`), zaraz po lokatorze kanoniczny string z
`render_hero_chase(world, game, player_duchy_id)` (K36.1c, dokładnie jeden
`data-hero-chase`), zaraz po pościgu kanoniczny string z
`render_engagement_preview(world, game, player_duchy_id)` (K37.1c, dokładnie
jeden `data-engagement-preview`), zaraz po podglądzie starcia kanoniczny string
z `render_threat_alert(world, game, player_duchy_id)` (K39.1c, dokładnie jeden
`data-threat-alert`) oraz dokładnie jeden
`<p data-player-result-text="…">…</p>` z `_player_result_text` (K31.2a:
`Gra w toku` / `Zwycięstwo Twojego księstwa` / `Porażka Twojego księstwa` /
`Remis` wg `game.is_over` i `game.winner` względem `player_duchy_id`); `None`
(domyślnie) → bajt-w-bajt jak bez argumentu (bez `data-player-summary`, bez
`data-victory-progress`, bez `data-next-objective`, bez `data-hero-locator`,
bez `data-hero-chase`, bez `data-engagement-preview`, bez `data-threat-alert` i
bez `data-player-result-text`);
element `data-result` = `duchy_id` zwycięzcy / `draw` / `ongoing` wg
`game.is_over` i `game.winner`; zawsze `<p data-result-text="…">` z czytelnym
tekstem z `_result_text` (`Gra w toku` / `Remis` / `Zwycięstwo: <duchy_id>`) —
ten sam stan co `data-result`. Czyste, deterministyczne, bez mutacji wejść (w
tym `battle`). Serwer podglądu — osobny przyrost (V13.5); wstrzyknięcie realnej
bitwy z rozkazu gracza — K16.1d.

**Snapshot CLI (V13.4b):** `python -m tbbui [ścieżka]` → `tbbui.__main__.main(argv)
-> int`. Rozgrywa deterministyczną partię headless (`create_headless_game` +
`run_headless_game` z ustalonym seedem `73`, jak `python -m tbb`) i zapisuje
`render_game_page` do pliku HTML. Opcjonalny pierwszy argument `argv` to ścieżka
wyjścia (domyślnie `out/game.html`); katalog nadrzędny jest tworzony, gdy nie
istnieje. Zwraca `0`. Dwa uruchomienia z tym samym seedem dają identyczną treść.

**Routing podglądu (V13.5a / K14.1b / K14.2a–e2 / K15.1b–c / K15.2b–c / K21.2 / K31.1a–b / K38.2a):** `tbbui.serve.GameApp(world, game,
calendar, rng, player_duchy_id=None, seed=None)` trzyma stan partii w pamięci i udostępnia
czystą metodę `handle(method, path) -> (kod_http, treść)` — bez gniazda HTTP.
Opcjonalny `seed` jest przechowywany na app (restart `POST /new` w K31.1a); domyślnie `None`.
`GameApp.previous_game: GameState | None` (K38.2a) — init `None`; `_render` woła
`render_game_page(..., previous_game=self.previous_game)` (podsumowanie tury w stronie).
`handle` rozdziela ścieżkę od query (`path.partition("?")`) na początku routingu.
`POST /new` (K31.1a): zawsze zeruje `previous_game`; gdy `seed is not None` podmienia
`world`/`game` na świeże
`create_headless_game()`, `calendar` na `Calendar()`, `rng` na `Rng(seed)`, zeruje
`last_battle`, ustawia `last_notice` = `"Nowa gra: rok 1, miesiąc 1"` (`player_duchy_id`
bez zmian); gdy `seed is None` — no-op stanu (`world`/`game`/`calendar`/`rng`/
`last_battle` bez zmian), `last_notice` = `"Nowa gra: brak zmian"`; zawsze
`(200, strona)`.
`GET /` → `(200, strona)` z `render_game_page(..., player_duchy_id=self.player_duchy_id,
previous_game=self.previous_game)`
(K23.2b — panel księstw z `data-player-duchy` przy wierszu gracza; K38.2a — dziennik
zmian gdy `previous_game` ustawione) plus znacznik
`data-player` (wartość `player_duchy_id` lub `""` gdy `None`), slot komunikatu
rozkazu `<p data-notice="{escape(last_notice)}">{escape(last_notice)}</p>`
(K28.1a / K29.1a — `GameApp.last_notice` inicjalizowane na `""`; ta sama
escapowana wartość w atrybucie i w widocznym ciele akapitu; `html.escape`;
K28.1b — `_apply_player_order` ustawia skutek rozkazu rozwoju) oraz formularze
`<form method="post" action="/new">` (przycisk `Nowa gra`, K31.1b — zawsze w
extras, niezależnie od `is_over` i `player_duchy_id`). Przy `game.is_over`
extras kończy się na `/new` — bez `/turn`, bez `/order/*` i bez
`data-order-section` (K32.2a; routing POST bez zmian). Przy grze w toku dalej:
`<form method="post" action="/turn">` (przycisk `Następna tura`),
`<form method="post" action="/order/recruit">` (`Rekrutuj (koszt złota: N)`
z `tbb.settlement.RECRUIT_GOLD_COST`, K30.2a),
`<form method="post" action="/order/muster">` (`Zbierz oddział`),
`<form method="post" action="/order/develop">` (`Rozbuduj osadę`)
(K29.2a — polskie etykiety `<button>`; `action`/`method` bez zmian),
przed blokiem rozwoju (recruit/muster/develop) nagłówek
`<h2 data-order-section="develop">Rozwój</h2>` bezpośrednio przed
`/order/recruit` (K30.1a; stała `_DEVELOP_SECTION_HEADER`), a przed grupami
marszu/szturmu/starcia po jednym nagłówku
`<h2 data-order-section="march|assault|engage">Marsz|Szturm|Starcie</h2>`
(K21.2, kolejność develop→marsz→szturm→starcie; formularze/routing bez zmian),
sekcję marszu (K15.1c: gdy gracz ma party — po jednym
`<form method="post" action="/order/march?target=<nazwa>">` na region z obcą
osadą, `quote` na nazwie, przycisk = nazwa; inaczej bare
`<form method="post" action="/order/march">` z `<button>Marsz</button>`) i
sekcję szturmu (K15.2c: ten sam guard i cele `_march_targets` — po jednym
`<form method="post" action="/order/assault?target=<nazwa>">`; inaczej bare
`<form method="post" action="/order/assault">` z `<button>Szturm</button>`)
oraz sekcję starcia party↔party (K19.1c: gdy `player_duchy_id` ustawiony,
gra nie `is_over` i `_engage_targets` niepuste — po jednym
`<form method="post" action="/order/engage?target=<nazwa>">` na sąsiednią
wrogą party w kolejności `world.neighbors`; inaczej bare
`<form method="post" action="/order/engage">` z `<button>Starcie</button>`)
(K29.2b — polskie etykiety bare `<button>`; cele nadal `region.name`). Wspólny emiter HTML formularzy celu (R16.1 / R21.1): prywatny
`GameApp._emit_target_forms(order_path, targets)` buduje pętlę
`<form action="{path}?target=quote(name)">` + przycisk z nazwą; reużywany przez
marsz, szturm i starcie. Guardy i dobór celów zostają per sekcja: prywatny
`GameApp._target_forms(order_path, bare_form)` (party gracza + `_march_targets`)
dla marszu/szturmu — `_march_forms` / `_assault_forms` tylko przekazują ścieżkę
i fallback; `_engage_forms` z `_engage_targets` (sąsiednie wrogie party, nie
obce osady) woła ten sam emiter przy niepustych celach, inaczej bare.
`POST /turn` → jedna tura przez
`run_headless_game(..., max_turns=1, calendar=..., player_duchy_id=...)` i
aktualizacja wewnętrznego stanu (gdy podany `player_duchy_id`, driver pomija
AI tego księstwa — K14.1a); po wykonanej turze `previous_game` = `GameState`
sprzed tury (K38.2a); gdy `game.is_over` przed żądaniem, no-op (stan bez
zmian, wciąż `200`) i `previous_game = None`; w obu przypadkach zeruje
`last_battle` i ustawia `last_notice` (K28.1e): po
turze `f"Następna tura: rok {calendar.year}, miesiąc {calendar.month}"`,
przy no-op `is_over` → `"Następna tura: gra zakończona"`.
`POST /order/*` (recruit/muster/develop/march/assault/engage) zeruje
`previous_game` (K38.2a — dziennik nie wisi po innym działaniu gracza).
Rozkazy gracza `POST /order/recruit` (K14.2a),
`POST /order/muster` (K14.2b), `POST /order/develop` (K14.2c),
`POST /order/march` (K14.2d2 / K15.1b) idzie wspólnym helperem
`_apply_player_order(transition, label)` (K28.1b / R29.1): guard księstwa
przez `_resolve_player_duchy() -> Duchy | None` (`None` gdy `is_over`, brak
`player_duchy_id` lub księstwo nieobecne w `game.duchies`); gdy duchy jest,
stosuje `transition(world, player_duchy)`
(`ai.recruit_duchy_unit` / `ai.muster_duchy_party` /
`ai.develop_duchy_settlement` / dla marszu: wspólne
`_order_target_region(query)` — niepusty, URL-dekodowany `target` dopasowany
do `world.regions` po nazwie → `ai.march_duchy_party_to`; brak/pusty/nieznany
`target` → fallback `ai.march_duchy_party`), podmienia `world` i
re-synchronizuje `game = game.sync_from_world(world)`; w przeciwnym razie
no-op; zawsze `(200, strona)`. Gdy podano `label`, po próbie ustawia
`self.last_notice` na `f"{label}: wykonano"` gdy nowy `world !=` poprzedni,
inaczej `f"{label}: brak zmian"` (również przy odrzuceniu przez guardy).
Etykiety: `POST /order/recruit` → `"Rekrutacja"`, `muster` →
`"Zebranie oddziału"`, `develop` → `"Rozbudowa"`, marsz ze znanym celem →
`f"Marsz do {region.name}"`, marsz bez/nieznany cel → `"Marsz"` (K28.1c).
`POST /order/assault` (K14.2e2 / K15.2b /
K16.1d-2 / K28.1d / R29.1) ma te same guardy przez
`_apply_player_assault_order` → `_resolve_player_duchy()`: jawny `target` →
`ai.assault_duchy_party_to_recorded` z etykietą
`f"Szturm na {region.name}"`, auto → `ai.assault_duchy_party_recorded` z
etykietą `"Szturm"` (oba z `self.rng` i
`morale_by_owner={d.duchy_id: d.morale for d in game.duchies}`); wynik
`(world, battle)` podmienia `world`, sync `game`, a gdy `battle is not None`
ustawia `self.last_battle` (init `None`; no-op/guardy nie ustawiają bitwy);
po wykonaniu `self.last_notice` = `f"{label}: bitwa"` gdy bitwa, inaczej
`f"{label}: brak zmian"` (również przy guardach).
`POST /order/engage` (K18.1c / K19.1b / K28.1d) — te same guardy i
`last_notice` przez `_apply_player_assault_order`; routing `?target=` jak
szturm (`_order_target_region`): jawny znany region →
`ai.engage_duchy_party_to_recorded` z etykietą
`f"Starcie z {region.name}"`, brak/pusty/nieznany `target` →
`ai.engage_duchy_party_recorded` z etykietą `"Starcie"` (auto-cel: pierwsze
sąsiednie wrogie party); oba z `self.rng` + `morale_by_owner` jak szturm;
na trafieniu ustawia `last_battle`, no-op/guardy nie ruszają bitwy. GET `/` sekcja engage (K19.1c / R21.1):
`_engage_forms()` — `_engage_targets(world, player_duchy_id)` to sąsiedzi
pozycji party gracza (pierwsza w `world.regions` z `owner_id == player`)
trzymający party z jawnym `owner_id != player`; gdy niepuste i guardy OK —
`_emit_target_forms("/order/engage", targets)`; inaczej bare `_ENGAGE_FORM`. `POST /turn` oraz
`/order/recruit|muster|develop|march` zerują `self.last_battle` (K16.1d-3);
`assault`/`engage` nie zerują przed wykonaniem. `_render` woła
`render_game_page(..., battle=self.last_battle)`. Inna ścieżka lub metoda →
`(404, treść)`. Determinizm: ten sam seed i sekwencja `handle` →
te same treści i stan. `player_duchy_id=None` zachowuje zachowanie
obserwatora AI-vs-AI.

**Serwer podglądu (V13.5b / K14.1b / K15.1b–c / K15.2b–c):** cienki adapter nad `GameApp.handle`:
`handle_request(app, method, path) -> (kod, bajty UTF-8)` oraz
`make_server(app, host="127.0.0.1", port=0) -> http.server.HTTPServer`.
Handler GET/POST deleguje do `handle_request` z pełnym `self.path` (query
zachowane; routing query w `GameApp.handle`), ustawia status i
`Content-Type: text/html; charset=utf-8`. `make_server` tylko wiąże gniazdo
(port `0` = efemeryczny); nie woła `serve_forever`. CLI:
`python -m tbbui serve [port]` tworzy świeżą deterministyczną partię
(`create_headless_game` + `Rng(73)` + `Calendar()`), `GameApp` z
`player_duchy_id="player"` i `seed=HEADLESS_SEED` (K31.1c — restart
`POST /new`) oraz `make_server`, potem `serve_forever()`.

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
│       ├── battlereport.py  # HTML fragment raportu bitwy (wynik + straty)
│       ├── unitstrength.py # czysta agregacja siły/rannych sekwencji Unit (R25.1/R27.1)
│       ├── settlementpanel.py # HTML panel osad (zasoby + populacja + garnizon)
│       ├── partypanel.py   # HTML panel party (właściciel + siła oddziału)
│       ├── victoryprogress.py # HTML panel postępu do celu (wrogowie do pokonania)
│       ├── herolocator.py  # HTML lista pościgu wrogich bohaterów (K35.1)
│       ├── herochase.py   # HTML dystans marszu do wrogich bohaterów (K36.1)
│       ├── engagementpreview.py # HTML podgląd siły celu szturmu (K37.1)
│       ├── threatalert.py # HTML alert zagrożonych pozycji (K39.1a–c / K39.2a)
│       ├── turnsummary.py # HTML podsumowanie zmian po turze (K38.1a–b)
│       ├── maplookup.py    # czysty helper: pierwszy region party właściciela (R37.1)
│       ├── gamelookup.py   # czysty helper: księstwo gracza po id (R38.1)
│       ├── nextobjective.py # HTML podpowiedź następnego kroku (K34.1)
│       ├── ownerlegend.py  # HTML legenda właścicieli (owner_id → kolor palety)
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
│   ├── test_battlereport.py  # HTML raport bitwy (tbbui, K17.1a)
│   ├── test_settlementpanel.py # HTML panel osad (tbbui, K22.1)
│   ├── test_partypanel.py  # HTML panel party (tbbui, K22.2)
│   ├── test_victoryprogress.py # HTML panel postępu do celu (tbbui, K33.1)
│   ├── test_herolocator.py # HTML lista pościgu wrogich bohaterów (tbbui, K35.1)
│   ├── test_herochase.py # HTML dystans marszu do wrogich bohaterów (tbbui, K36.1)
│   ├── test_engagementpreview.py # HTML podgląd siły celu szturmu (tbbui, K37.1)
│   ├── test_threatalert.py # HTML alert zagrożonych pozycji (tbbui, K39.1a–c / K39.2a)
│   ├── test_turnsummary.py # HTML podsumowanie zmian po turze (tbbui, K38.1a–b)
│   ├── test_ui_maplookup.py # helper lokalizacji party właściciela (tbbui, R37.1)
│   ├── test_ui_gamelookup.py # helper lokalizacji księstwa gracza (tbbui, R38.1)
│   ├── test_nextobjective.py # HTML podpowiedź następnego kroku (tbbui, K34.1)
│   ├── test_ownerlegend.py # HTML legenda właścicieli (tbbui, K23.1)
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
