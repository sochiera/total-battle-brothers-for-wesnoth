# PROJECT — Total Battle Brothers (nazwa robocza)

> Trwały kontekst planisty. Co budujemy, dla kogo, po co i w jakiej kolejności.
> Detale mechaniki → `docs/DESIGN.md`, decyzje techniczne → `docs/ARCHITECTURE.md`
> i `docs/DECISIONS.md`, kolejka zadań → `BACKLOG.md`.
> Rozróżnienie: **[W] wymaganie** (z briefu, nienegocjowalne), **[P] preferencja**
> (kierunek, można uzasadnić odstępstwo), **[O] opcja** (pomysł, wolno pominąć).

## Projekt i odbiorca
Single-player **sandbox** (bez scenariuszowej kampanii): turowa strategia łącząca
zarządzanie osadami i armiami z taktycznymi bitwami na heksach — w duchu
**Battle for Wesnoth / Battle Brothers / Total War**. Gracz prowadzi jedno
księstwo przeciw księstwom sterowanym przez AI. **[W]**

Odbiorca: pojedynczy gracz na **Linuksie x86-64**, który uruchamia natywną
aplikację i gra myszą/klawiaturą — **bez terminala, bez ręcznego odpalania
Pythona czy edytora Godota**. **[W]**

Skala kameralna: małe osady, nieliczne wojska, każda jednostka się liczy. **[W]**

## Cel docelowy i kryterium sukcesu
**Gotowe dopiero wtedy**, gdy użytkownik uruchamia natywną aplikację na Linuksie
i bez terminala może: **zarządzać osadą, przemieszczać armię, rozegrać bitwę,
zapisać i wczytać stan**. **[W]**

Rozgrywkowo: pętla sandboxa domyka się, gdy da się pokonać księstwo AI (utrata
jego osad **oraz** śmierć jego bohatera — to również warunek przegranej gracza).

Kryterium pomocnicze: **da się grać patrząc, a nie czytając logi**. Widok mapy
i bitwy ma nieść stan wizualnie. **[W]**

**Assety i osiągnięty wygląd są częścią kryterium, nie polishem po MVP.**
Feedback autora (2026-07-27): *„prawdziwe MVP będzie wtedy, kiedy będą assety
i tekstury. Nie musi być dużo budynków/rodzajów jednostek/terenu, ale żeby były
jakieś sensowne prawdziwe assety."* Widoki rysują **realne pliki graficzne**,
nie prostokąty z etykietą. Zakres mały — po kilka kafli, sylwetek i budynków —
ale prawdziwych. Od 2026-07-30 K87 to tylko minimum techniczne: oprawa trwa do
jawnego progu jakości i akceptacji człowieka na screenshotach. **[W]**

Próg jest osiągnięty dopiero, gdy mapa, osady i armie używają spójnych assetów,
bitwa ma czytelne kafle/jednostki/strony, UI nie opiera się na przypadkowych
placeholderach, licencje są kompletne, człowiek akceptuje screenshoty, a
`docs/PROJECT.md` i `BACKLOG.md` jawnie zapisują ten stan. **[W]**

## Stan faktyczny (aktualizowany przy przeglądach)
- Rdzeń `tbb` (Python): kampania, ekonomia, kalendarz, jednostki/progresja,
  morale, bitwa heksowa, AI, sukcesja — **headless, TDD**.
- Most `tbbbridge`: snapshot JSON, komendy/rozkazy, JSON Lines na stdio,
  `serve`/`--resume`, round-trip save/load (RNG + `last_battle`) — **gotowe**.
- Klient Godot 4 w `game/`: `SnapshotModel`, `BridgeClient` przez plik, oba
  widoki, statusy, bieżące rozkazy; **start bez terminala + save/load** (K82–K86).
- **Minimum assetów — GOTOWE, próg wizualny — NIE** (K87). Kenney CC0 = minimum.
- **Pakiet Linuksa, pętla partii, obrona osady, 5 regionów / 2 osady na stronę**
  — DOMKNIĘTE (K88–K92).
- **Oprawa K94–K105 — DOMKNIĘTA:** kompozycja mapy, ikony, armie, `move`+cel,
  bitwa (heks/dekoracje/PŻ), hierarchia ekranu, PL/teatr (`WorldPresentation`),
  herby/status/baner, tabliczki/panel/feedback, teksturowane przyciski/legenda,
  stonowane `map_ground_*` + `terrain_plains`, keep/outpost i dekoracje w tonie
  pergaminu, cue PŻ, **figury armii/stron w isometrii/¾** (nie top-down RTS),
  centrowanie klastra bitwy, ornament pustego wyboru (`1ebbbd4`…`d054581`,
  wcześniej `task-579-*`…`task-585-*`). Bez reguł/mostu w tej serii.
- `tbbui` — **tylko diagnostyka**, nie docelowy klient.

**Najbliższa luka po K105:** zaplanowany zakres oprawy przed progiem jest w
  kodzie; **brakuje pakietu screenshotów 1152×648 po K105** oraz **jawnej
  ludzkiej akceptacji** progu (K105 nie zostawiło `task-*` w
  `game/screenshots/`). Próg nieosiągnięty. **K106** — cztery stany dowodowe +
  akceptacja; bez nowej serii polish i bez reguł/mostu, chyba że review
  odrzuci konkretny stan.

## Ograniczenia i priorytety
- **[W]** Rdzeń `tbb` jest **jedynym źródłem reguł**. Godot nie duplikuje logiki;
  Python nie zależy od Godota ani UI.
- **[W]** Komunikacja Godot↔Python przez jawny, testowalny interfejs (stan jako
  JSON). Obecnie: `python -m tbbbridge serve`, JSON Lines po stdio, stan w pliku.
- **[W]** Budowa klienta Godota jest **bieżącym priorytetem**. Nie dokładać
  mechaniki w nieskończoność kosztem widocznej gry.
- **[W]** Determinizm: seedowalny RNG, testy bez losowości.
- **[W]** TDD, małe przyrosty, kryteria akceptacji; `simple|standard|complex` +
  ryzyko; bootstrap/toolchain/integracja Godot↔Python = `complex` + review pętli.
- **[P]** Rdzeń przed prezentacją **wewnątrz plasterka** — plasterek kończy się
  czymś widocznym, nie samą regułą.
- **[W]** Widoki rysują **prawdziwe assety** (patrz kryterium). Ilość mała;
  *istnienie* assetów — nie.
- **[W] Bramka oprawy:** do progu wizualnego każde planowanie i batch Forge:
  ≥4 graficzne, ≤2 mechaniczne, ≤6 łącznie. Mechanika tylko jako niezbędna
  zależność efektu graficznego. Brak 4 graficznych → dopisać małe, nigdy
  `no_more_tasks`.
- **[W]** Zadanie graficzne: asset + miejsce użycia, widoczny efekt w Godocie,
  screenshot/ludzkie review, źródło/licencja per plik w `game/assets/CREDITS.md`.
  Sam test/dokumentacja/refaktor ≠ grafika.
- **[P]** Assety z paczek OS (CC0: Kenney, OpenGameArt); atrybucja w repo.
  Czytelność > ładność.
- **[P]** Pakiet Linuksa: **systemowy `python3`** (wniosek 10). Bundling CPythona:
  **[O]**.
- **[O]** Kod/zasoby z Battle for Wesnoth.

**Wnioski kierunkowe** *(1–12 skrócone z K82–K88; detale → DECISIONS/BACKLOG)*:
1. Ścieżka rozkazu jest sparametryzowana — „kolejny przycisk" nie zbliża do celu.
2. Godot 4.2.2 bez `OS.execute_with_pipe`: one-shot + plik stanu (`--resume`).
3. Kontrakt po jednym polu/grupie ratuje mikro-TDD.
4. **Dowód „działa" dotyczy tylko artefaktu, na którym go zrobiono** (dev ≠ PCK).
5. `battle.hexes` = tylko heksy z jednostkami; pełna siatka = późniejsza zmiana mostu.
6. Prostokąt ≠ MVP; K84/85 geometria, K87 nośnik — podmiana nośnika nie rusza geometrii.
7. Toolchain (import/eksport) jako osobna bramka przed treścią.
8. **Teren tylko w bitwie** — `Region` bez terenu; teren mapy = zmiana rdzenia+mostu.
9. Warianty: tekstura + `modulate`, nie osobny plik na wariant.
10. **Pakiet bez własnego Pythona** — systemowy `python3` + czytelny brak.
11. **„Plik się ładuje" ≠ poprawna treść obrazka** — CREDITS + kształt + review człowieka.
12. **Odstępstwo od [P]:** Hexagon Pack bez postaci → RTS Medieval; strony = para plików, nie tint.
13. **Zielone testy ≠ grywalność** — sekwencja gracza na żywym moście (+ pakiet po K88).
14. Legalny wynik bitwy ≠ błąd rozkazu (K89: kontrakt przed regułą ruchu).
15. Pozycja startowa to reguła gry (K90), nie odłożony balans.
16. Gracz i AI przez te same reguły świata (K90/K91).
17. Jedna osada/stronę za mała — min. dwie w pięciu regionach (K92.2), nie duża mapa.
18. Obrona osady odblokowała skalowanie (G92.1); skraj z oddziałem nie-obrońcą odłożony.
19. 5 regionów odsłoniło brak sterowania, nie defekt skali — wartość w wyborze celu.
20. `march` (ku osadzie) ≠ `move` (jeden krok do sąsiada, bez wrogiej osady).
21. **Tekstury ≠ osiągnięty wygląd** — każdy przyrost oprawy z dowodem wizualnym 1152×648.
22. Oprawę da się poprawiać bez reguł (K94–G96); reguła kroku jest — najwęższa ścieżka.
23. K97: `move(target)` + UI/e2e bez zmiany reguł.
24. **Rola assetu = obraz/źródło, nie nazwa** (`plains`=heks 120×140; forest/hills=dekoracje).
25. Lokalny widok ≠ spójny ekran — ocena na pełnej scenie świeżej partii/bitwy.
26. Tabliczki ≠ pełna warstwa PL — jedno mapowanie (`WorldPresentation`); kanon w kontrakcie (K100).
27. K100→K101: po teatrze kolejna warstwa to herby/status/baner, nie reguły.
28. K101→K102: residual `ColorRect`/ciemny HUD tabliczek/PŻ/panel/feedback → bez reguł.
29. **K103:** flat sterowania/legendy + obrys podłoża domknięte; residual Kenney na
    osadach/dekoracjach/sylwetkach (+ cue PŻ) → **K104**.
30. **K104:** keep/outpost, dekoracje i cue PŻ w tonie pergaminu — **zrobione**;
    recolor top-down RTS **nie** domyka spójności z isometrią (wniosek: barwa ≠
    rodzina kształtów) → **K105**.
31. **K105:** figury mapy/bitwy w isometrii/¾ + centrowanie klastra + ornament
    pustego wyboru — **zrobione** w kodzie; brak screenshotów w
    `game/screenshots/` i brak ludzkiej akceptacji → **K106** (pakiet progu,
    nie kolejna warstwa inventowanej oprawy).

## Klimat, ton, kierunek wizualny
Średniowiecze **bez magii i fantastyki**, surowy i realistyczny ton. **[W]**
Interfejs i teksty po polsku. **[P]**

Wizualnie: spójna 2D w Godocie — mapa regionów/osad/armii i siatka heksów.
Nie AAA ani dźwięk; czytelna, mniej prototypowa gra. Oba widoki, prawdziwe
tekstury i spójność/czytelność = **[W]**; technika i paczka = **[P]**.

Dobór assetów: średniowieczne, nie-fantastyczne; realistyczny ton > kreskówka;
spójna rodzina > zlepek ładnych obrazków. Kenney = przejściowe minimum,
wymieniane etapami. **[P]**

Kolejność poprawy: (1–14) ~~mapa…herby, tabliczki/PŻ/panel, przyciski/legenda,
podłoże, keep/outpost, dekoracje, recolor, cue PŻ, kształt figur isometrii/¾,
kompozycja chrome (panel/bitwa)~~ — zrobione (K94–K105); (15) **pakiet progu**
screenshotów 1152×648 + jawna ludzka akceptacja (K106) — bez reguł/mostu i bez
otwierania nowej serii polish, chyba że review odrzuci stan. **[W]**

## Sugestie autora briefu
- `godot-notes.md` jest **niewiążące** — inspiracja, nie specyfikacja.
- `tbbui` zostaje diagnostyką; nie rozwijamy go jako produktu (wstrzymany K62).
- Porządek repo gry (sondy vs produkcja, `out/`) — **[P]** *(zrobione: R82.1)*.
- **Assety przesądzają o prawdziwym MVP** (2026-07-27) — **[W]**, nie sugestia.
- Brief 2026-07-30: bramka 4 zadań graficznych/batch do ludzkiej akceptacji;
  K87 nie kończy oprawy. **[W]**

## Kolejne prawdopodobne etapy
1. ~~K82–K86~~ — **zrobione**.
2. **K87** — minimum assetów gotowe technicznie; próg wizualny nie.
3. ~~K88–K92~~ — **domknięte**.
4. ~~K94–K105~~ — **zrobione** (oprawa aż po figury isometrii/¾ i chrome).
5. **K106 — próg wizualny** — pakiet screenshotów 1152×648 po K105 (świeża
   partia, wybór regionu, bitwa, status/zakończenie) + **jawna ludzka
   akceptacja** zapisana tu i w `BACKLOG.md`. Bez reguł/mostu; residualna
   poprawa tylko gdy review odrzuci konkretny stan.
6. **Nowa partia z UI po końcu gry** — most ma `new_game`, scena nie. Odłożone
   do końca priorytetu graficznego / progu wizualnego.

## Świadomie odłożone
- Kampania/fabuła, multiplayer, magia, oddziały masowe, AAA, dźwięk, edytor map
  — **poza zakresem**.
- Alert gospodarczy HTML (K62) — **wstrzymany** (diagnostyka).
- Bogatszy model ran/terenu/budynków, więcej jednostek, balans/AI,
  `StrategicTurn` — po widocznej, grywalnej grze. Skala K92.2 ≠ balans.
- Szturm na osadę z oddziałem nie-obrońcą (G92.1c) — z 3. księstwem lub reprodukcją.
- Podział dużych docs (ARCHITECTURE/DECISIONS/DESIGN) — dług, nie blokuje celu.
- Do progu wizualnego: niezależne reguły, AI, ekonomia, walka, ruch, rozkazy,
  protokół/most, rdzeń, save/load, porządki i docs poza oprawą — wyjątek tylko
  dla niezbędnej zależności konkretnego zadania graficznego w batchu.
