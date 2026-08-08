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
i bitwy ma nieść stan wizualnie — a od 2026-08-07 (wniosek 40) czytamy to
ostrzej: ekran ma nieść **to, czego reguła wymaga od decydującego gracza**,
nie tylko ładny obraz stanu. **[W]**

**Assety i osiągnięty wygląd są częścią kryterium, nie polishem po MVP.**
Feedback autora (2026-07-27): *„prawdziwe MVP będzie wtedy, kiedy będą assety
i tekstury… żeby były jakieś sensowne prawdziwe assety."* Widoki rysują
**realne pliki graficzne**, nie prostokąty z etykietą; zakres mały, ale
prawdziwy. Próg = spójne assety mapy/osad/armii, czytelna bitwa, brak
placeholderów, kompletne licencje i **jawna akceptacja screenshotów przez
człowieka**. **[W]** Spełnione 2026-08-06 w K106.

## Stan faktyczny (aktualizowany przy przeglądach)
- Rdzeń `tbb` (Python): kampania, ekonomia, kalendarz, jednostki/progresja,
  morale, bitwa heksowa, AI, sukcesja — **headless, TDD**.
- Most `tbbbridge`: snapshot JSON, komendy/rozkazy, JSON Lines na stdio,
  `serve`/`--resume`, round-trip save/load (RNG + `last_battle`) — **gotowe**.
- Klient Godot 4 w `game/`: `SnapshotModel`, `BridgeClient` przez plik, oba
  widoki, statusy, bieżące rozkazy; **start bez terminala + save/load** (K82–K86).
- **Pakiet Linuksa, pętla partii, obrona osady, 5 regionów / 2 osady na stronę**
  — DOMKNIĘTE (K88–K92).
- **Oprawa K94–K105 — DOMKNIĘTA:** kompozycja mapy, ikony, armie, `move`+cel,
  bitwa (heks/dekoracje/PŻ), hierarchia ekranu, PL/teatr (`WorldPresentation`),
  herby/status/baner, tabliczki/panel/feedback, przyciski/legenda, podłoże,
  keep/outpost, cue PŻ, **figury w isometrii/¾**, centrowanie bitwy
  (`1ebbbd4`…`d054581`). Bez reguł/mostu w tej serii.
- **Minimum assetów GOTOWE (K87, Kenney CC0); próg wizualny OSIĄGNIĘTY
  2026-08-06 (K106)** — człowiek zaakceptował pakiet G106.1a–c (screenshoty
  `task-591…593` w 1152×648), audyt bez residuali i bez follow-upu. Zapis
  odwołuje bramkę planowania oprawy 4 graficzne / batch.
- `tbbui` — **tylko diagnostyka**, nie docelowy klient.
- **Nowa partia z UI (K107) — DOMKNIĘTA** (`2c4ace0`…`12d67bc`).
- **K108 — DOMKNIĘTY:** rozkaz „Uderz na wojsko wroga" ze statusem i ikoną,
  warunek siły 2:1 w `ai.take_duchy_military_action`, dowody wizualne
  `task-605…607`.
- **K109 — DOMKNIĘTY** (`53d6d98`…`6d6946a`): znacznik `Party.acted_this_month`,
  zerowanie na nowy miesiąc, round-trip w persystencji, blokada drugiej akcji
  wojskowej jako `changed=false` (nie błąd) i polski status w kliencie.
- **Pomiary po K108/K109 (2026-08-06/07, `seed=73`)** — pełne zapisy
  w `BACKLOG.md`, sekcje K108–K110. Skrót: presja AI i ekonomia tury działają;
  pomiar po K109 odsłonił zakleszczenie „armia pod murami" → **K110**.
- **K110 — DOMKNIĘTY 2026-08-07** (`b9682a5`…`d81cb79`): szturm „spod murów"
  w rdzeniu (rozstawienie, skutek w świecie, koszt miesiąca), `assault` bez
  celu skierowany do tej ścieżki w moście i widoczna zmiana strony regionu po
  kliku. **R111.1** (`24f5a4a`) zdjął zgadywanie znacznika akcji w kliencie.
- **Rozgrywka — pomiar po K110 (2026-08-07, uruchomienie mostu na `seed=73`):**
  zakleszczenie zniknęło — martwa dotąd sekwencja `engage` → `assault` →
  `march` kończy partię zwycięstwem w **roku 1, miesiącu 7**; regresje stoją
  (bierny gracz przegrywa w 13 turach, priorytet `assault` → `engage` → `march`
  wygrywa w roku 1, miesiącu 4). **K111** (marsz zablokowany przez wrogą armię
  mówi tylko „bez zmian") jest w kolejce jako task-621…624. Ten sam pomiar
  odsłonił brak następny — **wojsko z garnizonu nie ma jak trafić w pole**:
  `recruit`/`muster` biorą *pierwszą* pasującą osadę, więc gracz „rozwojowy"
  wychodzi w pole **jedynką**, a po jej stracie partia **zamiera** (120 tur,
  `is_over: false`, armia AI nieruchoma przy niespełnionym progu 2:1). Zakres
  **K112**; pełne liczby → `BACKLOG.md`.
- **Pomiar przy przeglądzie 2026-08-07 (po R111.1):** `pytest` zielony w
  całości. Uruchomiony most (`seed=73`) potwierdził pułapkę z wniosku 39
  liczbowo (`recruit`×10 → `muster` = `size 5, hp 73`; z `develop`×10 wcześniej
  = `size 1, hp 25`) i odsłonił brak **po stronie widoku**: oba stany wyglądają
  na ekranie **identycznie**. Most niesie na region siłę oddziału i garnizon
  osady, `SnapshotModel` je przepuszcza, a panel regionu pokazuje wyłącznie
  „twoja armia" i nazwę osady (`game/scripts/main.gd:654-667`); siły wroga
  przed szturmem też nie widać. Zakres **K113** — klient-only.
- **K112 — DOMKNIĘTY 2026-08-08:** pomiar przez żywy most na `seed=73`, po
  `develop`×10 → `recruit`×10 → `muster`, kończy partię po **6 turach** z
  `winner: "ai"` i `player_result: "defeat"`. W przebiegu wzmocnienia
  oddział AI rośnie **2 → 4** po pobraniu garnizonu własnego `ai outpost`,
  którego stan spada **1 → 0**. Reguła usuwa martwą partię bez armii; wynik
  i pełny zapis przebiegu są w sekcji K112 w `BACKLOG.md`.

## Ograniczenia i priorytety
- **[W]** Rdzeń `tbb` jest **jedynym źródłem reguł**. Godot nie duplikuje logiki;
  Python nie zależy od Godota ani UI.
- **[W]** Komunikacja Godot↔Python przez jawny, testowalny interfejs (stan jako
  JSON): `python -m tbbbridge serve`, JSON Lines po stdio, stan w pliku.
- **[W]** Budowa klienta Godota jest **bieżącym priorytetem**. Nie dokładać
  mechaniki w nieskończoność kosztem widocznej gry.
- **[W] Po progu wizualnym (2026-08-06) priorytetem w kliencie jest grywalność
  pętli, nie kolejny przycisk ani warstwa oprawy.** Wolno ruszyć rdzeń, gdy
  defekt rozgrywki jest zmierzony na uruchomionym kodzie, a plasterek kończy
  się czymś widocznym (wniosek 32). Balansu ani strojenia AI to nie otwiera.
- **[W]** Determinizm: seedowalny RNG, testy bez losowości.
- **[W]** TDD, małe przyrosty, kryteria akceptacji; `simple|standard|complex`
  + ryzyko; toolchain/integracja Godot↔Python = `complex` + review pętli.
- **[P]** Rdzeń przed prezentacją **wewnątrz plasterka** — plasterek kończy się
  czymś widocznym, nie samą regułą.
- **[W]** Widoki rysują **prawdziwe assety** (patrz kryterium). Ilość mała;
  *istnienie* assetów — nie.
- **[W] Bramka oprawy — ODWOŁANA 2026-08-06** po akceptacji K106 (wymagała ≥4
  zadań graficznych i ≤2 mechanicznych na batch; nie obowiązuje).
- **[W]** Zadanie graficzne: asset + miejsce użycia, widoczny efekt w Godocie,
  screenshot/review, licencja per plik w `game/assets/CREDITS.md`. Sam
  test/dokumentacja/refaktor ≠ grafika.
- **[P]** Assety z paczek OS (CC0: Kenney, OpenGameArt); atrybucja w repo.
  Czytelność > ładność.
- **[P]** Pakiet Linuksa: **systemowy `python3`** (wniosek 10); bundling
  CPythona **[O]**.
- **[O]** Kod/zasoby z Battle for Wesnoth.

**Wnioski kierunkowe** *(1–12 z K82–K88; dawne 21–31 scalone w 21–27, stąd luka
przed 32; detale → DECISIONS/BACKLOG)*:
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
21. **Tekstury ≠ osiągnięty wygląd** — każdy przyrost widoczny na ekranie
    z dowodem wizualnym 1152×648.
22. Oprawę da się poprawiać bez reguł (K94–G96, K97 `move(target)`).
23. **Rola assetu = obraz/źródło, nie nazwa** (`plains`=heks; forest/hills=dekoracje).
24. Lokalny widok ≠ spójny ekran — ocena na pełnej scenie świeżej partii/bitwy.
25. Tabliczki ≠ pełna warstwa PL — jedno mapowanie (`WorldPresentation`, K100).
26. **K101–K105:** residuale przeszły bez reguł, ale recolor top-down RTS **nie**
    domknął spójności — barwa ≠ rodzina kształtów (stąd figury isometrii/¾).
27. **K105→K106:** figury zrobione w kodzie, a i tak dopiero brak screenshotów
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
    wdrożeniu.** Dwa warunki brzegowe w mocy: reguła **obowiązuje także
    oddziały AI** (wniosek 16), a znacznik ustawia **wyłącznie akcja, która
    zmieniła świat** (`take_duchy_military_action` robi w jednej turze
    `muster`+`march`+`assault`, więc „pierwsza akcja zawsze" cofało K108).
    Wzorzec: **regresję K108 mierzy się na `seed=73` przy każdej zmianie reguł
    ruchu i walki.**
36. **Kosztowna tura odsłania koniec ścieżki, nie koniec pracy (2026-08-07).**
    Dopóki rozkazy były darmowe, partia kończyła się w trzy miesiące i nikt nie
    dochodził do stanu „armia stoi pod obcą stolicą". Po K109 partia trwa
    latami — i dopiero wtedy było widać, że **rdzeń nie znał szturmu spod
    murów** (mechanizm → `BACKLOG.md`, sekcja K110). Wniosek
    kierunkowy: **każde domknięcie ekonomii tury trzeba domierzyć długą partią,
    nie krótką** — defekty kolejnego etapu leżą za horyzontem poprzedniego.
37. **Zakleszczenie ≠ przegrana, i to jest gorsze (2026-08-07).** Stan bez
    wyjścia nie daje graczowi sygnału: rozkazy mówią „bez zmian", kalendarz
    idzie, nic się nie dzieje; reguła symetryczna (wniosek 16) zakleszcza tak
    samo AI, a warunek zwycięstwa z briefu staje się nieosiągalny dla obu
    stron. **K110 broni kryterium sukcesu**, nie wygody gracza.
38. **Wniosek 36 potwierdził się natychmiast (2026-08-07, po K110).** Naprawa
    szturmu spod murów odsłoniła **drugi stan bez wyjścia**, po stronie AI:
    armia bez progu 2:1 z K108 nie robi **nic** — przez 120 zmierzonych tur.
    Dopóki jedynym kształtem akcji AI jest „maszeruj i szturmuj przy
    przewadze", każdy niespełniony warunek zamienia przeciwnika w dekorację.
    **Nie naprawia się tego stałą.**
39. **Rekrut, który nigdy nie wychodzi za mury, to zmarnowana ekonomia
    (2026-08-07).** `recruit`/`muster` biorą *pierwszą* pasującą osadę, więc ta
    sama sekwencja daje oddział 1 albo 5 jednostek zależnie od tego, czy padło
    wcześniej `develop`. Brakuje **reguły wzmocnienia oddziału garnizonem**,
    nie kolejnego przycisku: zdejmuje pułapkę graczowi i daje AI sposób na
    własny, niezmieniony próg (**K112**). Wybór osady dla rozkazów
    gospodarczych zostaje osobnym, późniejszym plasterkiem.
40. **Dane w moście ≠ dane na ekranie (2026-08-07).** Cztery kamienie z rzędu
    naprawiały *reguły* pętli, a przy pomiarze okazało się, że klient nie
    pokazuje **żadnej liczby siły**, choć most niesie je od K63. Kryterium
    „grać patrząc" pilnowaliśmy po stronie **oprawy** i to uśpiło pytanie, czy
    przez ten ładny ekran **da się podjąć decyzję**: rdzeń AI decyduje po
    stosunku sił 2:1, gracz po ikonce. Wzorzec na każdy przegląd: obok „czy
    reguła działa" pytać **„czy gracz widzi to, czego reguła od niego
    wymaga"**. **K113** to pierwsza spłata — projekcja danych, które już
    przychodzą, nie nowa seria polish.

## Klimat, ton, kierunek wizualny
Średniowiecze **bez magii i fantastyki**, surowy i realistyczny ton. **[W]**
Interfejs i teksty po polsku. **[P]**

Wizualnie: spójna 2D w Godocie — mapa regionów/osad/armii i siatka heksów.
Nie AAA ani dźwięk; czytelna, mniej prototypowa gra. Oba widoki, prawdziwe
tekstury i spójność/czytelność = **[W]**; technika i paczka = **[P]**.

Dobór assetów: średniowieczne, nie-fantastyczne; realistyczny ton > kreskówka;
spójna rodzina > zlepek ładnych obrazków. Kenney = przejściowe minimum,
wymieniane etapami. **[P]**

Seria oprawy (K94–K105) i pakiet progu (K106) są **wyczerpane**; nowa seria
polish nie jest otwarta. Każdy przyszły przyrost widoczny na ekranie — także
czysto informacyjny, jak liczby z K113 — nadal wymaga dowodu wizualnego
1152×648. **[W]**

## Sugestie autora briefu
- `godot-notes.md` jest **niewiążące** — inspiracja, nie specyfikacja.
- `tbbui` zostaje diagnostyką; nie rozwijamy go jako produktu (wstrzymany K62).
- Porządek repo gry (sondy vs produkcja, `out/`) — **[P]** *(zrobione: R82.1)*.
- **Assety przesądzają o prawdziwym MVP** (2026-07-27) — **[W]**, nie sugestia.
- Brief 2026-07-30: bramka 4 zadań graficznych/batch obowiązywała do ludzkiej
  akceptacji — K106 zamknął ten warunek 2026-08-06. **[W]**

## Kolejne prawdopodobne etapy
1–6. ~~K82–K92, K94–K105, **K106 (próg wizualny, akceptacja 2026-08-06)**,
   K107~~ — **zrobione**; szczegóły w „Stan faktyczny" i `BACKLOG.md`.
7. ~~**K108 — przeciwnik, który nie roztrwania armii, i `engage` w kliencie**~~
   — **domknięte** (kod, pomiar, dowody wizualne task-605…607).
8. ~~**K109 — rozkaz wojskowy kosztuje miesiąc**~~ — **domknięte 2026-08-07**
   (`53d6d98`…`6d6946a`). Warunki brzegowe → wniosek 35.
9. ~~**K110 — armia stojąca w regionie wrogiej osady potrafi ją zdobyć**~~ —
   **domknięte 2026-08-07** (`b9682a5`…`d81cb79`, + `24f5a4a` R111.1);
   zakleszczenie zmierzone jako usunięte, regresje K108/K109 stoją.
10. **K111 — czytelny powód, gdy marsz blokuje wroga armia** — w kolejce
   (task-621…624): rdzeń wskazuje blokujący oddział, most nazywa region,
   klient mówi po polsku, kto zagradza drogę, dowód z żywej sesji. Defekt
   czytelności, nie reguł — odpowiedź („Uderz na wojsko wroga") już istnieje.
   `R111.1` (`24f5a4a`) już wpadł: znacznik akcji miesiąca idzie z rdzenia.
11. **K112 — wojsko z garnizonu trafia w pole.** Jedna brakująca reguła
   rdzenia: oddział w regionie własnej osady wciąga jej garnizon (symetrycznie
   dla AI, koszt miesiąca), rozkaz `reinforce` w moście, użycie po stronie AI
   zamiast bezczynności przy niespełnionym progu oraz widoczny wzrost oddziału
   w kliencie. Powód: wnioski 38–39. **Progu 2:1 z K108 nie wolno tknąć** —
   regresje `seed=73` (13 tur / rok 1, miesiąc 4) są kryterium G112.1b.
12. **K113 — siła widoczna liczbą** (nowe, ten przegląd): panel wybranego
   regionu pokazuje liczebność i PŻ oddziału oraz garnizon osady, dla obu
   stron, z odświeżeniem po rozkazie i turze. **Wyłącznie klient** — bez
   rdzenia, bez mostu, bez nowego rozkazu; dane już przychodzą. Powód:
   wniosek 40. Uwaga kolejności: „licznik oddziału" z G112.1d dziś nie
   istnieje — albo K113 idzie przed nim, albo G112.1d ogranicza się do statusu
   i figury i **nie tworzy drugiego licznika**.
13. **Prawdopodobnie potem:** wybór osady dla `develop`/`recruit`/`muster`
   (mapa ma już zaznaczenie regionu z K97), tempo presji AI oraz ile garnizonu
   wolno zabrać. Osobne plasterki, nie razem z K112 ani K113.

## Świadomie odłożone
- Kampania/fabuła, multiplayer, magia, oddziały masowe, AAA, dźwięk, edytor map
  — **poza zakresem**. Alert gospodarczy HTML (K62) — **wstrzymany**.
- Bogatszy model ran/terenu/budynków, więcej jednostek, balans/AI,
  `StrategicTurn` — po widocznej, grywalnej grze. Skala K92.2 ≠ balans.
  **Doprecyzowanie 2026-08-06/07:** warunek „nie szturmuj bez szans" (K108),
  jedna akcja wojskowa na miesiąc (K109), szturm spod murów (K110) i
  wzmocnienie oddziału garnizonem (K112) to naprawy defektów rozgrywki, nie
  strojenie AI; krzywe, wagi, **wartość progu 2:1**, taktyka AI i koszty
  rozkazów gospodarczych zostają odłożone. Miarą jest pomiar na uruchomionym
  kodzie (`seed=73`), nie ocena „czy gra jest ciekawa".
- **Pełny panel ekonomii osady w kliencie** (zapasy, produkcja, konsumpcja,
  ludność — most niesie to od K63) — **odłożone**. K113 bierze z tego
  **wyłącznie** garnizon i siłę oddziału, bo tylko te dwie liczby są potrzebne
  do decyzji „bić czy nie". Reszta dopiero, gdy pokaże ją zmierzona potrzeba.
- Wybór osady dla rozkazów gospodarczych (`develop`/`recruit`/`muster` biorą
  *pierwszą* pasującą osadę, `target` jest ignorowany) — **odłożone do po
  K112**, żeby nie mieszać dwóch zmian kontraktu rozkazu naraz.
- „Ile garnizonu wolno zabrać" (`muster` i wzmocnienie z K112 opróżniają osadę
  do zera) — **odłożone**: to strojenie, nie defekt blokujący pętlę.
- Szturm na osadę **sąsiedniego** regionu zajętego przez oddział nie-obrońcę
  (G92.1c) — nadal odłożony: z 3. księstwem lub reprodukcją. **To nie jest
  K110**; wspólny mają wyłącznie guard `apply_settlement_battle_result`.
- Podział dużych docs (ARCHITECTURE/DECISIONS/DESIGN) — dług, nie blokuje celu.
- Niezależne reguły, AI, ekonomia, ruch, protokół, save/load, porządki i docs
  pozostają odłożone względem celu grywalnego MVP (bramce oprawy już nie
  podlegają — K106).
