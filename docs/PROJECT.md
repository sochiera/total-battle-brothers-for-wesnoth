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
Warunek został spełniony 2026-08-06 w K106.

## Stan faktyczny (aktualizowany przy przeglądach)
- Rdzeń `tbb` (Python): kampania, ekonomia, kalendarz, jednostki/progresja,
  morale, bitwa heksowa, AI, sukcesja — **headless, TDD**.
- Most `tbbbridge`: snapshot JSON, komendy/rozkazy, JSON Lines na stdio,
  `serve`/`--resume`, round-trip save/load (RNG + `last_battle`) — **gotowe**.
- Klient Godot 4 w `game/`: `SnapshotModel`, `BridgeClient` przez plik, oba
  widoki, statusy, bieżące rozkazy; **start bez terminala + save/load** (K82–K86).
- **Minimum assetów — GOTOWE (K87); próg wizualny — OSIĄGNIĘTY 2026-08-06
  (K106).** Kenney CC0 było minimum technicznym.
- **Pakiet Linuksa, pętla partii, obrona osady, 5 regionów / 2 osady na stronę**
  — DOMKNIĘTE (K88–K92).
- **Oprawa K94–K105 — DOMKNIĘTA:** kompozycja mapy, ikony, armie, `move`+cel,
  bitwa (heks/dekoracje/PŻ), hierarchia ekranu, PL/teatr (`WorldPresentation`),
  herby/status/baner, tabliczki/panel/feedback, teksturowane przyciski/legenda,
  stonowane `map_ground_*` + `terrain_plains`, keep/outpost i dekoracje w tonie
  pergaminu, cue PŻ, **figury armii/stron w isometrii/¾** (nie top-down RTS),
  centrowanie klastra bitwy, ornament pustego wyboru (`1ebbbd4`…`d054581`,
  wcześniej `task-579-*`…`task-585-*`). Bez reguł/mostu w tej serii.
- **Próg wizualny K106 — OSIĄGNIĘTY 2026-08-06:** człowiek zaakceptował
  pakiet G106.1a–c (`task-591-fresh-post-k105-1152x648.png`, parę
  `task-592-selected-region-{empty,selected}-1152x648.png` oraz
  `task-593-visible-battle-post-k105-1152x648.png`). Audyt pełnych ekranów
  nie wskazał residualnego chrome, angielskich tokenów, top-downowych figur,
  pustego panelu bez ornamentu ani luk atrybucji w `game/assets/CREDITS.md`.
  Zapis odwołuje bramkę planowania oprawy 4 graficzne / batch.
- `tbbui` — **tylko diagnostyka**, nie docelowy klient.

**K106 zamknął lukę po K105:** pakiet screenshotów 1152×648 po K105 został
  przejrzany i zaakceptowany 2026-08-06. Nie ma otwartego residualu chrome ani
  braków CREDITS do follow-upu; dalsze poprawki oprawy nie są wymagane przez
  próg.

- **Nowa partia z UI (K107) — DOMKNIĘTA:** most, przycisk, wiązanie i dowód
  wizualny paska (`2c4ace0`…`12d67bc`).
- **K108 — zrobiony w kodzie, zostały dowody wizualne:** rozkaz „Uderz na
  wojsko wroga" ze statusem i ikoną, klik rozgrywający starcie, warunek siły w
  `ai.take_duchy_military_action` oraz refaktor paska rozkazów
  (`7de20e4`…`d4de6e1`). W kolejce: task-605 (ekran bitwy nie wypycha mapy),
  task-606/607 (dowody wizualne wojska wroga i starcia).
- **Rozgrywka — pomiar po K108 (2026-08-06, uruchomienie rdzenia na `seed=73`,
  nie lektura):** defekt z poprzedniego przeglądu **jest naprawiony** — wojsko
  AI stoi na mapie od miesiąca 2 i przesuwa się (`border` → `player outpost` →
  `player lands`), a gracz bierny **przegrywa partię w 13 turach**
  (`result = {"is_over": true, "winner": "ai", "player_result": "defeat"}`).
  Ten sam pomiar odsłonił brak głębszy: **rozkazy wojskowe nic nie kosztują**.
  Bez ani jednego `next_turn` sekwencja `recruit`×5 → `muster` →
  (`march`+`assault`)×3 daje `player_result="victory"` w **roku 1, miesiącu 1** —
  kalendarz nie drgnął, AI nie dostało tury, przeciwnik nie zdążył się pojawić.
  To jest zakres **K109**.

## Ograniczenia i priorytety
- **[W]** Rdzeń `tbb` jest **jedynym źródłem reguł**. Godot nie duplikuje logiki;
  Python nie zależy od Godota ani UI.
- **[W]** Komunikacja Godot↔Python przez jawny, testowalny interfejs (stan jako
  JSON). Obecnie: `python -m tbbbridge serve`, JSON Lines po stdio, stan w pliku.
- **[W]** Budowa klienta Godota jest **bieżącym priorytetem**. Nie dokładać
  mechaniki w nieskończoność kosztem widocznej gry.
- **[W] Po progu wizualnym (2026-08-06) priorytetem w obrębie klienta jest
  grywalność pętli, nie kolejny przycisk ani kolejna warstwa oprawy.** Wolno
  ruszyć rdzeń, gdy defekt rozgrywki jest zmierzony na uruchomionym kodzie i
  plasterek kończy się czymś widocznym na ekranie (wniosek 32). To nie
  otwiera balansu ani strojenia AI — patrz „Świadomie odłożone".
- **[W]** Determinizm: seedowalny RNG, testy bez losowości.
- **[W]** TDD, małe przyrosty, kryteria akceptacji; `simple|standard|complex` +
  ryzyko; bootstrap/toolchain/integracja Godot↔Python = `complex` + review pętli.
- **[P]** Rdzeń przed prezentacją **wewnątrz plasterka** — plasterek kończy się
  czymś widocznym, nie samą regułą.
- **[W]** Widoki rysują **prawdziwe assety** (patrz kryterium). Ilość mała;
  *istnienie* assetów — nie.
- **[W] Bramka oprawy (odwołana 2026-08-06 po akceptacji K106):** do osiągnięcia
  progu każde planowanie i batch Forge wymagały ≥4 graficznych, ≤2 mechanicznych
  i ≤6 łącznie. Mechanika była dopuszczalna tylko jako niezbędna zależność
  efektu graficznego; po osiągnięciu progu reguła nie obowiązuje.
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
    pustego wyboru — **zrobione** w kodzie; brak screenshotów i ludzkiej
    akceptacji doprowadził do K106 (pakietu progu, nie kolejnej warstwy oprawy).
32. **Odhaczone kryterium ≠ gra (2026-08-06).** Po K106 wszystkie punkty
    kryterium „gotowe" są spełnione, a pierwszy pomiar samej rozgrywki pokazał
    trzymiesięczną, bezoporową partię i przeciwnika, który co turę traci własną
    armię. Widoczność stanu została zbudowana **zanim** było co pokazywać:
    następny priorytet to przeciwnik, który zostaje na planszy.
33. **Reguła przegranej dyktuje kolejność plasterków.** `Duchy.is_defeated`
    wymaga braku osad **i** braku oddziałów, więc powściągliwszy AI **bez**
    rozkazu `engage` w kliencie uczyniłby partię niewygrywalną. Najpierw
    odpowiedź gracza na wojsko w polu, potem wojsko, które w polu zostaje.
34. **Rozkaz bez kosztu = brak przeciwnika (2026-08-06, po K108).** AI gra
    wyłącznie wewnątrz `next_turn`, a gracz może wydać dowolnie wiele rozkazów
    wojskowych w jednym miesiącu — więc cała presja zbudowana w K108 działa
    tylko na gracza, który dobrowolnie kończy turę. Naprawiony przeciwnik nie
    czyni gry grą; czyni ją nią dopiero **ekonomia tury**.
35. **Regułę tury zweryfikowano symulacją przed zaplanowaniem (2026-08-06).**
    Przy jednej akcji wojskowej oddziału na miesiąc partia na `seed=73` jest
    wygrywalna (zwycięstwo w roku 1, miesiącu 4) i **zawiera realne starcie w
    polu** (`engage` w miesiącu 2). Kolejność z wniosku 33 zostaje zachowana:
    gracz ma czym odpowiedzieć, zanim tura zacznie kosztować.
    **Doprecyzowanie po recenzji (ta sama data):** pierwsza symulacja objęła
    wyłącznie stronę gracza, więc nie rozstrzygała przypadku AI. Reguła
    **obowiązuje także oddziały AI** (wniosek 16 — wyjęcie ich spod niej jest
    wykluczone), a znacznik ustawia **wyłącznie akcja, która zmieniła świat**.
    Powód jest zmierzony: `ai.take_duchy_military_action` (`src/tbb/ai.py:553`)
    robi w jednej turze AI `muster` + `march` + `assault`, czyli dwie z czterech
    blokowanych akcji. Przy dosłownym odczycie „pierwsza akcja ustawia znacznik"
    (bezskuteczny `march` też liczy się jako akcja) AI po turze 11 nigdy już nie
    szturmuje i bierny gracz nie przegrywa nawet po 20 turach — K109 **cofnąłby
    K108**. Przy odczycie „tylko akcja zmieniająca świat" przegrana wypada w
    turze 13, jak dziś, bo `march` oddziału już sąsiadującego z celem jest
    no-opem. Regresja na `seed=73` jest kryterium G109.1b.

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
screenshotów 1152×648 + jawna ludzka akceptacja (K106, 2026-08-06) — zrobione,
bez reguł/mostu i bez otwierania nowej serii polish. **[W]**

## Sugestie autora briefu
- `godot-notes.md` jest **niewiążące** — inspiracja, nie specyfikacja.
- `tbbui` zostaje diagnostyką; nie rozwijamy go jako produktu (wstrzymany K62).
- Porządek repo gry (sondy vs produkcja, `out/`) — **[P]** *(zrobione: R82.1)*.
- **Assety przesądzają o prawdziwym MVP** (2026-07-27) — **[W]**, nie sugestia.
- Brief 2026-07-30: bramka 4 zadań graficznych/batch obowiązywała do ludzkiej
  akceptacji; K87 nie kończyło oprawy, a K106 zamknął ten warunek 2026-08-06.
  **[W]**

## Kolejne prawdopodobne etapy
1. ~~K82–K86~~ — **zrobione**.
2. ~~**K87** — minimum assetów gotowe technicznie~~; próg domknięty dopiero K106.
3. ~~K88–K92~~ — **domknięte**.
4. ~~K94–K105~~ — **zrobione** (oprawa aż po figury isometrii/¾ i chrome).
5. ~~**K106 — próg wizualny** — pakiet screenshotów 1152×648 po K105 i
   **jawna ludzka akceptacja 2026-08-06** zapisana tu i w `BACKLOG.md`.~~
6. ~~**K107 — nowa partia z UI po końcu gry**~~ — **domknięte**.
7. **K108 — przeciwnik, który nie roztrwania armii, i `engage` w kliencie** —
   **zrobiony w kodzie i zmierzony jako skuteczny**; w kolejce zostały dowody
   wizualne (task-605…607).
8. **K109 — rozkaz wojskowy kosztuje miesiąc.** Znacznik akcji oddziału w
   rdzeniu (zerowany przez `tick_parties`, trwały w persystencji), blokada
   drugiej akcji wojskowej w tym samym miesiącu jako `changed=false` (nie
   błąd) i czytelny polski status w kliencie. Powód: wnioski 34–35.
   **Dwa warunki brzegowe, bez których K109 cofa K108** (wniosek 35): reguła
   obejmuje **także oddziały AI** — żadnego wyjątku po właścicielu (wniosek 16)
   — a znacznik ustawia **wyłącznie akcja, która zmieniła świat**, więc
   bezskuteczny `march` nie zużywa miesiąca. G109.1b niesie regresję na
   `seed=73`: bierny gracz nadal przegrywa w 13 turach.
9. **Prawdopodobnie potem:** tempo presji AI (dopiero gdy tura kosztuje) oraz
   ile garnizonu wolno zabrać `muster`-em. Osobne plasterki, nie razem z K109.

## Świadomie odłożone
- Kampania/fabuła, multiplayer, magia, oddziały masowe, AAA, dźwięk, edytor map
  — **poza zakresem**.
- Alert gospodarczy HTML (K62) — **wstrzymany** (diagnostyka).
- Bogatszy model ran/terenu/budynków, więcej jednostek, balans/AI,
  `StrategicTurn` — po widocznej, grywalnej grze. Skala K92.2 ≠ balans.
  **Doprecyzowanie 2026-08-06:** jeden jawny warunek „nie szturmuj bez szans"
  w `ai.take_duchy_military_action` (K108) oraz jedna akcja wojskowa oddziału
  na miesiąc (K109) to naprawy defektów rozgrywki, nie strojenie AI; krzywe,
  wagi, taktyka AI i koszty rozkazów gospodarczych zostają odłożone.
- Szturm na osadę z oddziałem nie-obrońcą (G92.1c) — z 3. księstwem lub reprodukcją.
- Podział dużych docs (ARCHITECTURE/DECISIONS/DESIGN) — dług, nie blokuje celu.
- Niezależne reguły, AI, ekonomia, walka, ruch, rozkazy, protokół/most, rdzeń,
  save/load, porządki i docs poza oprawą pozostają odłożone względem celu
  grywalnego MVP; po zamknięciu K106 nie podlegają już bramce oprawy.
