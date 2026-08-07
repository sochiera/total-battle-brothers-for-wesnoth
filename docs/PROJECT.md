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
nie prostokąty z etykietą; zakres mały, ale prawdziwy. Próg = spójne assety
mapy/osad/armii, czytelna bitwa, brak przypadkowych placeholderów, kompletne
licencje i **jawna akceptacja screenshotów przez człowieka**. **[W]**
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
  stonowane podłoże, keep/outpost i dekoracje w tonie pergaminu, cue PŻ,
  **figury w isometrii/¾**, centrowanie bitwy, ornament pustego wyboru
  (`1ebbbd4`…`d054581`). Bez reguł/mostu w tej serii.
- **Próg wizualny K106 — OSIĄGNIĘTY 2026-08-06:** człowiek zaakceptował pakiet
  G106.1a–c (świeża partia, wybór regionu, bitwa; screenshoty `task-591…593`
  w 1152×648). Audyt nie wskazał residualnego chrome, angielskich tokenów,
  top-downowych figur ani luk w `game/assets/CREDITS.md`; nie ma otwartego
  follow-upu. Zapis odwołuje bramkę planowania oprawy 4 graficzne / batch.
- `tbbui` — **tylko diagnostyka**, nie docelowy klient.
- **Nowa partia z UI (K107) — DOMKNIĘTA:** most, przycisk, wiązanie i dowód
  wizualny paska (`2c4ace0`…`12d67bc`).
- **K108 — DOMKNIĘTY:** rozkaz „Uderz na wojsko wroga" ze statusem i ikoną,
  klik rozgrywający starcie, warunek siły w `ai.take_duchy_military_action`,
  refaktor paska rozkazów oraz zaakceptowane dowody wizualne z żywej sesji
  (`task-605` — ekran bitwy nie wypycha mapy, `task-606` — wojsko AI na mapie,
  `task-607` — rozstrzygnięte starcie po `engage`).
- **K109 — DOMKNIĘTY** (`53d6d98`…`6d6946a`): znacznik `Party.acted_this_month`,
  zerowanie na nowy miesiąc, round-trip w persystencji, blokada drugiej akcji
  wojskowej jako `changed=false` (nie błąd) i polski status w kliencie.
- **Pomiary po K108 i K109 (2026-08-06/07, `seed=73`)** — pełne zapisy
  w `BACKLOG.md`, sekcje K108–K110. Skrót: presja AI działa (bierny gracz
  przegrywa w 13 turach), ekonomia tury działa (aktywny wygrywa w roku 1,
  miesiącu 4), a pomiar po K109 odsłonił zakleszczenie „armia pod murami" —
  zakres **K110**.
- **K110 — DOMKNIĘTY 2026-08-07** (`b9682a5`…`d81cb79`): szturm „spod murów"
  w rdzeniu (rozstawienie, skutek w świecie, koszt miesiąca), skierowanie
  `assault` bez celu do tej ścieżki w moście i widoczna zmiana strony regionu
  po kliku. **R111.1** (`24f5a4a`) zdjął przy okazji zgadywanie znacznika akcji
  w kliencie. Testy `pytest` zielone w całości przy tym przeglądzie.
- **Rozgrywka — pomiar po K110 (2026-08-07, uruchomienie mostu na `seed=73`):**
  zakleszczenie zniknęło — martwa dotąd sekwencja `engage` → `assault` →
  `march` kończy partię zwycięstwem w **roku 1, miesiącu 7**; regresje stoją
  (bierny gracz przegrywa w 13 turach, priorytet `assault` → `engage` → `march`
  wygrywa w roku 1, miesiącu 4). **K111** (marsz zablokowany przez wrogą armię
  mówi tylko „bez zmian") jest już w kolejce jako task-621…624.
  Ten sam pomiar odsłonił brak następny — **wojsko z garnizonu nie ma jak
  trafić w pole**: `recruit` obsadza *pierwszą* osadę z wolną ludnością, a
  `muster` zbiera garnizon *pierwszej* osady bez oddziału, więc gracz
  „rozwojowy" (`develop`×10 → `recruit`×10 → `muster`) wychodzi w pole
  **jedynką**, podczas gdy pięciu rekrutów zostaje w drugiej osadzie na zawsze.
  Gdy taki oddział zginie (miesiąc 3), partia **zamiera na 10 lat gry**:
  sprawdzone do tury 120 (`is_over: false`), armia AI stoi na `border` bez
  ruchu, bo próg 2:1 z K108 nigdy nie zostaje osiągnięty (`str_att` 78→108 vs
  `str_def` 40→63), a własne garnizony AI (4 + 3 jednostki) nie mają jak wejść
  do pola. To jest zakres **K112**.

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

**Wnioski kierunkowe** *(1–12 skrócone z K82–K88; dawne 21–31 z serii oprawy
scalone w 21–27, stąd luka przed 32; detale → DECISIONS/BACKLOG)*:
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
22. Oprawę da się poprawiać bez reguł (K94–G96, K97 `move(target)` = UI/e2e bez reguł).
23. **Rola assetu = obraz/źródło, nie nazwa** (`plains`=heks 120×140; forest/hills=dekoracje).
24. Lokalny widok ≠ spójny ekran — ocena na pełnej scenie świeżej partii/bitwy.
25. Tabliczki ≠ pełna warstwa PL — jedno mapowanie (`WorldPresentation`); kanon w kontrakcie (K100).
26. **K101–K104:** kolejność residuali (herby/status/baner → tabliczki/PŻ/panel →
    sterowanie/legenda/podłoże → keep/outpost/dekoracje/cue PŻ) dała się przejść
    bez reguł; recolor top-down RTS **nie** domknął spójności — barwa ≠ rodzina
    kształtów, stąd K105.
27. **K105→K106:** figury isometrii/¾ zrobione w kodzie, ale brak screenshotów
    i ludzkiej akceptacji wymusił pakiet progu, nie kolejną warstwę oprawy.
32. **Odhaczone kryterium ≠ gra (2026-08-06).** Po K106 wszystkie punkty
    kryterium „gotowe" są spełnione, a pierwszy pomiar samej rozgrywki pokazał
    trzymiesięczną, bezoporową partię. Widoczność stanu została zbudowana
    **zanim** było co pokazywać.
33. **Reguła przegranej dyktuje kolejność plasterków.** `Duchy.is_defeated`
    wymaga braku osad **i** braku oddziałów, więc powściągliwszy AI **bez**
    rozkazu `engage` w kliencie uczyniłby partię niewygrywalną.
34. **Rozkaz bez kosztu = brak przeciwnika (2026-08-06, po K108).** AI gra
    wyłącznie wewnątrz `next_turn`, więc cała presja z K108 działała tylko na
    gracza, który dobrowolnie kończy turę. Przeciwnika czyni grą dopiero
    **ekonomia tury**.
35. **Regułę tury zweryfikowano symulacją przed planowaniem i pomiarem po
    wdrożeniu.** Dwa warunki brzegowe zostają w mocy: reguła **obowiązuje także
    oddziały AI** (wniosek 16), a znacznik ustawia **wyłącznie akcja, która
    zmieniła świat** — `ai.take_duchy_military_action` robi w jednej turze
    `muster`+`march`+`assault`, więc dosłowne „pierwsza akcja liczy się zawsze"
    cofało K108. Wzorzec do powtarzania: **regresję K108 mierzy się na
    `seed=73` przy każdej zmianie reguł ruchu i walki.**
36. **Kosztowna tura odsłania koniec ścieżki, nie koniec pracy (2026-08-07).**
    Dopóki rozkazy były darmowe, partia kończyła się w trzy miesiące i nikt nie
    dochodził do stanu „armia stoi pod obcą stolicą". Po K109 partia trwa
    latami — i dopiero wtedy było widać, że **rdzeń nie znał szturmu spod
    murów** (mechanizm → `BACKLOG.md`, sekcja K110). Wniosek
    kierunkowy: **każde domknięcie ekonomii tury trzeba domierzyć długą partią,
    nie krótką** — defekty kolejnego etapu leżą za horyzontem poprzedniego.
37. **Zakleszczenie ≠ przegrana, i to jest gorsze (2026-08-07).** Stan bez
    wyjścia nie daje graczowi żadnego sygnału: rozkazy odpowiadają „bez zmian",
    kalendarz idzie, nic się nie dzieje. Reguła symetryczna (wniosek 16)
    zakleszcza tak samo AI. Warunek zwycięstwa z briefu („utrata osad **oraz**
    śmierć bohatera") jest wtedy nieosiągalny dla obu stron, więc **K110 broni
    samego kryterium sukcesu**, nie wygody gracza.
38. **Wniosek 36 potwierdził się natychmiast (2026-08-07, po K110).** Naprawa
    szturmu spod murów odsłoniła **drugi stan bez wyjścia**, tej samej klasy co
    wniosek 37, ale po stronie AI: armia, która nie spełnia progu 2:1 z K108,
    nie robi **nic** — przez 120 zmierzonych tur. Dopóki jedynym kształtem
    akcji AI jest „maszeruj i szturmuj przy przewadze", każdy niespełniony
    warunek zamienia przeciwnika w dekorację. **Nie naprawia się tego stałą.**
39. **Rekrut, który nigdy nie wychodzi za mury, to zmarnowana ekonomia
    (2026-08-07).** `recruit` i `muster` biorą *pierwszą* pasującą osadę, więc
    ta sama sekwencja rozkazów daje oddział 1 albo 5 jednostek zależnie od
    tego, czy wcześniej padło `develop` — a klient nie mówi o tym nic. Brakuje
    **reguły wzmocnienia stojącego oddziału garnizonem**, nie kolejnego
    przycisku: ta jedna reguła zdejmuje pułapkę graczowi i zarazem daje AI
    sposób na osiągnięcie własnego, niezmienionego progu (**K112**). Wybór
    osady dla rozkazów gospodarczych zostaje osobnym, późniejszym plasterkiem.

## Klimat, ton, kierunek wizualny
Średniowiecze **bez magii i fantastyki**, surowy i realistyczny ton. **[W]**
Interfejs i teksty po polsku. **[P]**

Wizualnie: spójna 2D w Godocie — mapa regionów/osad/armii i siatka heksów.
Nie AAA ani dźwięk; czytelna, mniej prototypowa gra. Oba widoki, prawdziwe
tekstury i spójność/czytelność = **[W]**; technika i paczka = **[P]**.

Dobór assetów: średniowieczne, nie-fantastyczne; realistyczny ton > kreskówka;
spójna rodzina > zlepek ładnych obrazków. Kenney = przejściowe minimum,
wymieniane etapami. **[P]**

Kolejność poprawy oprawy (K94–K105) i pakiet progu (K106) są **wyczerpane**;
nowa seria polish nie jest otwarta. Każdy przyszły przyrost oprawy nadal
wymaga dowodu wizualnego 1152×648. **[W]**

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
7. ~~**K108 — przeciwnik, który nie roztrwania armii, i `engage` w kliencie**~~ —
   **domknięte**: kod, pomiar oraz zaakceptowane dowody wizualne z żywej sesji
   (task-605…607).
8. ~~**K109 — rozkaz wojskowy kosztuje miesiąc**~~ — **domknięte 2026-08-07**
   (`53d6d98`…`6d6946a`): znacznik akcji oddziału zerowany przez `tick_parties`,
   trwały w persystencji, druga akcja w miesiącu jako `changed=false`, polski
   status w kliencie. Regresja K108 potwierdzona pomiarem (bierny gracz
   przegrywa w 13 turach; aktywny wygrywa w roku 1, miesiącu 4). Warunki
   brzegowe → wniosek 35.
9. ~~**K110 — armia stojąca w regionie wrogiej osady potrafi ją zdobyć**~~ —
   **domknięte 2026-08-07** (`b9682a5`…`d81cb79`, + `24f5a4a` R111.1);
   zakleszczenie zmierzone jako usunięte, regresje K108/K109 stoją.
10. **K111 — czytelny powód, gdy marsz blokuje wroga armia** — w kolejce
   (task-621…624): rdzeń wskazuje blokujący oddział, most nazywa region,
   klient mówi po polsku, kto zagradza drogę, dowód z żywej sesji. Defekt
   czytelności, nie reguł — odpowiedź („Uderz na wojsko wroga") już istnieje.
11. **K112 — wojsko z garnizonu trafia w pole.** Jedna brakująca reguła
   rdzenia: oddział stojący w regionie własnej osady wciąga jej garnizon
   (symetrycznie dla AI, koszt miesiąca jak każdy rozkaz wojskowy), rozkaz
   `reinforce` w moście, użycie po stronie AI zamiast bezczynności przy
   niespełnionym progu 2:1 oraz widoczny wzrost oddziału w kliencie. Powód:
   wnioski 38–39. **Warunek brzegowy: progu 2:1 z K108 nie wolno tknąć** —
   regresje `seed=73` (13 tur / rok 1, miesiąc 4) są kryterium G112.1b.
12. **Prawdopodobnie potem:** wybór osady dla `develop`/`recruit`/`muster`
   (mapa ma już zaznaczenie regionu z K97), tempo presji AI oraz ile garnizonu
   wolno zabrać. Osobne plasterki, nie razem z K112.

## Świadomie odłożone
- Kampania/fabuła, multiplayer, magia, oddziały masowe, AAA, dźwięk, edytor map
  — **poza zakresem**.
- Alert gospodarczy HTML (K62) — **wstrzymany** (diagnostyka).
- Bogatszy model ran/terenu/budynków, więcej jednostek, balans/AI,
  `StrategicTurn` — po widocznej, grywalnej grze. Skala K92.2 ≠ balans.
  **Doprecyzowanie 2026-08-06, uzupełnione 2026-08-07:** jeden jawny warunek
  „nie szturmuj bez szans" w `ai.take_duchy_military_action` (K108), jedna
  akcja wojskowa oddziału na miesiąc (K109), szturm spod murów (K110) oraz
  wzmocnienie oddziału garnizonem (K112) to naprawy defektów rozgrywki, nie
  strojenie AI; krzywe, wagi, **wartość progu 2:1**, taktyka AI i koszty
  rozkazów gospodarczych zostają odłożone. Miarą jest zawsze pomiar na
  uruchomionym kodzie (`seed=73`), nie ocena „czy gra jest ciekawa".
- Wybór osady dla rozkazów gospodarczych (`develop`/`recruit`/`muster` biorą
  dziś *pierwszą* pasującą osadę, a `target` jest po cichu ignorowany) —
  **odłożone do po K112**, żeby nie mieszać dwóch zmian kontraktu rozkazu naraz.
- „Ile garnizonu wolno zabrać" (`muster` i wzmocnienie z K112 opróżniają osadę
  do zera) — **odłożone**: to strojenie, nie defekt blokujący pętlę.
- Szturm na osadę **sąsiedniego** regionu zajętego przez oddział nie-obrońcę
  (G92.1c) — nadal odłożony: z 3. księstwem lub reprodukcją. **To nie jest
  K110** (tam oddział stoi w regionie samej osady); wspólny mają wyłącznie
  guard `apply_settlement_battle_result`.
- Podział dużych docs (ARCHITECTURE/DECISIONS/DESIGN) — dług, nie blokuje celu.
- Niezależne reguły, AI, ekonomia, walka, ruch, rozkazy, protokół/most, rdzeń,
  save/load, porządki i docs poza oprawą pozostają odłożone względem celu
  grywalnego MVP; po zamknięciu K106 nie podlegają już bramce oprawy.
