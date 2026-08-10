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
**realne pliki graficzne**, nie prostokąty z etykietą. Próg = spójne assety
mapy/osad/armii, czytelna bitwa, brak placeholderów, kompletne licencje
i **jawna akceptacja screenshotów przez człowieka**. **[W]** Spełnione
2026-08-06 w K106.

## Stan faktyczny (aktualizowany przy przeglądach)
- Rdzeń `tbb` (Python): kampania, ekonomia, kalendarz, jednostki/progresja,
  morale, bitwa heksowa, AI, sukcesja — **headless, TDD**.
- Most `tbbbridge`: snapshot JSON, komendy/rozkazy, JSON Lines na stdio,
  `serve`/`--resume`, round-trip save/load (RNG + `last_battle`) — **gotowe**.
- Klient Godot 4 w `game/`: `SnapshotModel`, `BridgeClient` przez plik, oba
  widoki, statusy, bieżące rozkazy; **start bez terminala + save/load** (K82–K86).
- **Pakiet Linuksa, pętla partii, obrona osady, 5 regionów / 2 osady na stronę**
  — DOMKNIĘTE (K88–K92).
- **Oprawa K94–K105 — DOMKNIĘTA**: kompozycja, ikony, armie, `move`+cel,
  bitwa, hierarchia ekranu, PL/teatr (`WorldPresentation`), chrome,
  figury isometrii/¾. **Assety K87 (Kenney CC0)
  i próg wizualny K106 — OSIĄGNIĘTE 2026-08-06**, człowiek zaakceptował
  G106.1a–c (1152×648); to odwołało bramkę oprawy 4/batch.
- `tbbui` — **tylko diagnostyka**, nie docelowy klient.
- **K107–K110 — DOMKNIĘTE:** nowa partia z UI; próg 2:1 w
  `ai.take_duchy_military_action` (K108); jedna akcja wojskowa na miesiąc
  (`Party.acted_this_month`, K109); szturm „spod murów" (K110). **R111.1**
  zdjął zgadywanie znacznika akcji w kliencie.
- **K111/K113 — DOMKNIĘTE 2026-08-08:** powód blokady marszu przez warstwy
  (`blocked_region`) — **wzorzec diagnostyki rozkazu**, reużyty w K114/K116;
  panel wybranego regionu pokazuje jednostki, PŻ i garnizon obu stron
  (`WorldPresentation`).
- **K112 — DOMKNIĘTY 2026-08-08:** pomiar zaktualizowany po K117 (2026-08-09):
  oddział wciąga garnizon własnej osady (`reinforce`), symetrycznie dla AI.
  Pomiar `seed=73`: `develop`×10 → `recruit`×10 → `muster` kończy partię po
  **8 turach** (`winner: "ai"`), a **oddział AI rośnie 1 → 3**; garnizon
  `ai outpost` przechodzi **2 → 1** i utrzymuje `garrison: 1`.
- **K114 — DOMKNIĘTY 2026-08-08:** rozkaz **gospodarczy** niesie powód odmowy
  (przejściowy vs trwały, liczy rdzeń — wniosek 42), klient pokazuje go po
  polsku i dokłada **wolną ludność** do panelu osady. Pomiar zamykający z
  `seed=73`: `recruit`×8 → `develop` daje powód przejściowy przy zapasie 10 i
  saldzie +5; w turze 3 przebiegu co-turę `develop` + `recruit` obie osady
  mają `free=0`, zapas 5 i 4 oraz saldo 0 i −2, a odmowa jest trwała; kolejna
  tura potwierdza brak wzrostu (Keep 8→8, Outpost 9→9), a przy zapasie 0
  powód nadal jest trwały. Regresje: bierna partia R1M7, aktywna R1M4.
- **K115 — DOMKNIĘTY 2026-08-08:** naprawa głodu (wniosek 43) — po `develop`×2
  i 5× `next_turn` wolna ludność odrasta (player lands `free` 2→5 /
  population 5→8; player outpost `free` 4→6 / population 5→7, osada utracona
  na rzecz AI w turze 5), a `develop`/`recruit` po odroście dają
  `changed:true`. Regresje: bierna R1M7, aktywna R1M4.
- **K116 — DOMKNIĘTY 2026-08-08:** `develop`/`recruit`/`muster` słuchają
  wskazanego regionu (`target`) — panel osady z K113 i wybór regionu z K97
  razem pozwalają wydawać rozkazy „w tę osadę, którą widać".
- **K117 — DOMKNIĘTY 2026-08-09:** `muster`/`reinforce` zostawiają ≥1 obrońcę
  w osadzie (defekt rozgrywki, nie strojenie — wniosek 44). Pomiar `seed=73`:
  po `muster` osada ma `garrison=1`; bierna partia przegrywa w **R1M7**,
  aktywna (`recruit`×5 → `muster` → `march` → `next_turn` → `reinforce` →
  `next_turn` → `march` → `next_turn` → `assault` → `next_turn` → `assault`
  → `next_turn` → `assault`) wygrywa w **R1M5**; długa ścieżka obronna
  (`develop`×2 → `recruit`×4 → `next_turn`×20) pozostaje `ongoing` w **R2M8**
  z `garrison=3` w obu osadach. Regresje: bierna R1M7, aktywna R1M5.
- **K118 — DOMKNIĘTY 2026-08-09:** `assault`/`engage` bez skutku niosą powód
  przez most; klient kieruje do `engage`, gdy w zasięgu jest tylko wojsko.
  Domyka wniosek 41(i) na całej klasie rozkazów. Regresje: rush R1M4, bierny
  R1M7, K115/K116/K117 zachowują odrost ludności, wskazany cel i `garrison>=1`.
  Pomiar zamykający z `seed=73`: `recruit`×3 prowadzi do odmów wojskowych,
  aktywna ścieżka wygrywa w **R1M4**, bierna przegrywa w **R1M7**.

  Trwałe piny pomiarowe bramek live: K115/K116 — rozdzielone regresje z
  `seed=73`: bierna sekwencja 6× `next_turn` prowadzi do przegranej w **R1M7**;
  aktywna sekwencja `recruit`×2 → `muster` → `march` → `next_turn` → `engage`
  → `next_turn` → `assault` → `next_turn` → `assault` prowadzi do zwycięstwa
  w **R1M4**. Niezależnie od tej pary wyników po `develop`×2 gracz ma
  `population=5`, `free=2` (początkowo `free=4`), a po pięciu turach
  `population=8`, `free=5` (odpowiednio posterunek: `population=7`, `free=6`),
  a późniejszy rozkaz daje `changed:true`. K117 — po `muster` jest
  `garrison=1`, aktywna sekwencja to `recruit`×5 → `muster` → `march` → `next_turn` → `reinforce` → `next_turn` → `march` → `next_turn` → `assault` → `next_turn` → `assault` → `next_turn` → `assault`; obrona `develop`×2 → `recruit`×4 → `next_turn`×20 pozostaje `ongoing` w **R2M8** z `garrison=3`.

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
- **[W] Bramka oprawy (≥4 zadania graficzne/batch) — ODWOŁANA 2026-08-06** po
  akceptacji K106.
- **[W]** Zadanie graficzne: asset + miejsce użycia, widoczny efekt w Godocie,
  screenshot/review, licencja per plik w `game/assets/CREDITS.md`.
- **[P]** Assety z paczek OS (CC0: Kenney, OpenGameArt); atrybucja w repo.
  Czytelność > ładność.
- **[P]** Pakiet Linuksa: **systemowy `python3`** (wniosek 10); bundling
  CPythona **[O]**.
- **[O]** Kod/zasoby z Battle for Wesnoth.

**Wnioski kierunkowe** *(1–27 z K82–K106 skompaktowane dla progu 20 KB — pełne
brzmienie w historii gita; dawne 21–31 scalone w 21–27, stąd luka przed 32)*:
1–12. **(bootstrap, most, pakiet, assety — K82–K88).** „Kolejny przycisk" nie
    zbliża do celu, bo ścieżka rozkazu jest sparametryzowana; Godot 4.2.2 bez
    `OS.execute_with_pipe` → one-shot + `--resume`; kontrakt po jednym polu
    ratuje mikro-TDD; **dowód „działa" dotyczy tylko artefaktu, na którym go
    zrobiono** (dev ≠ PCK); `battle.hexes` = tylko heksy z jednostkami;
    **teren istnieje wyłącznie w bitwie** (teren mapy = zmiana rdzenia i
    mostu); toolchain to osobna bramka przed treścią; **pakiet bez własnego
    Pythona**; **„plik się ładuje" ≠ poprawna treść obrazka** (CREDITS + review
    człowieka); strony bitwy = para plików, nie tint.
13–16. **Zielone testy ≠ grywalność** (sekwencja gracza na żywym moście);
    legalny wynik bitwy ≠ błąd rozkazu (K89); pozycja startowa to reguła gry
    (K90), nie balans; gracz i AI przez te same reguły świata (K90/K91).
17–20. **(skala i sterowanie — K92, K97).** Jedna osada/stronę za mała (min.
    dwie w pięciu regionach); 5 regionów odsłoniło brak **sterowania**, nie
    defekt skali; `march` (ku osadzie) ≠ `move` (krok do sąsiada).
21–27. **(oprawa — K94–K106).** **Tekstury ≠ osiągnięty wygląd**: każdy
    przyrost widoczny na ekranie z dowodem 1152×648; **rola assetu =
    obraz/źródło, nie nazwa**; lokalny widok ≠ spójny ekran (ocena na pełnej
    scenie); jedno mapowanie PL (`WorldPresentation`); barwa ≠ rodzina
    kształtów; **brak screenshotów i ludzkiej akceptacji** wymusił pakiet progu.
32. **Odhaczone kryterium ≠ gra (2026-08-06).** Po K106 wszystkie punkty
    kryterium „gotowe" są spełnione, a pierwszy pomiar rozgrywki pokazał
    trzymiesięczną, bezoporową partię: widoczność stanu zbudowano **zanim**
    było co pokazywać. Wzorzec powtórzony w K117/K118.
33–35. **(K108–K109).** `Duchy.is_defeated` wymaga braku osad **i** oddziałów,
    więc reguła przegranej dyktuje kolejność plasterków. **Rozkaz bez kosztu =
    brak przeciwnika:** AI gra wyłącznie wewnątrz `next_turn`, więc presję robi
    dopiero **ekonomia tury**. Znacznik akcji obowiązuje też oddziały AI
    i ustawia go **wyłącznie akcja, która zmieniła świat**. Wzorzec:
    **regresję K108 mierzyć na `seed=73` przy każdej zmianie reguł ruchu/walki.**
36. **Kosztowna tura odsłania koniec ścieżki, nie koniec pracy (2026-08-07).**
    Po K109 partia trwa miesiacami i dopiero wtedy było widać, że rdzeń nie
    znał szturmu spod murów (→ K110). Wzorzec: **każde domknięcie ekonomii tury
    domierzać długą partią, nie krótką** — defekty kolejnego etapu leżą za
    horyzontem poprzedniego. **Scalony z wnioskiem 44 (2026-08-09):** dotyczy
    też ekonomii — po K116 tylko rush wygrywa, a strategie gospodarcze/obronne
    przegrywają; ten defekt widać wyłącznie długą partią.
37–38. **Zakleszczenie ≠ przegrana, i to jest gorsze (2026-08-07).** Stan bez
    wyjścia nie daje sygnału: „bez zmian", kalendarz idzie, nic się nie dzieje;
    reguła symetryczna (wniosek 16) zakleszcza tak samo AI, więc **K110 broni
    kryterium sukcesu**. Naprawa odsłoniła drugi taki stan po stronie AI
    (120 zmierzonych tur) → K112. **Nie naprawia się tego stałą.**
 39–42. **(K112–K118, domknięte).** Wniosek 40 („czy gracz widzi to, czego
     reguła wymaga") spłacony przez K113/K114 (siła, wolna ludność, powód).
     Wniosek 41: rozkaz bez skutku niesie **powód** — domknięty na całej klasie
     (K111 ruch, K114 gospodarka, **K118 wojsko**); powód rozróżnia
     „poczekaj" od „nie doczekasz się". **Diagnostykę liczy rdzeń** (wniosek 42),
     most ją przenosi — nie powiela guardów.
 43. **Głód jest stanem pochłaniającym (K115 — domknięte).** Predykat „czy to
     minie" bierze się z **sekwencji ticków** (`tick_growth` po `tick_economy`),
     nie z `wheat > 0` (kłamie na progu). Kształt reguły = defekt, wartość =
     balans (jak wniosek 44/K117).
 44–45. **Wąska pętla = ukryty stan bez wyjścia; domknięcia klas problemu
     (2026-08-09).** Krótka partia wygląda dobrze (rush R1M4 / bierny R1M7);
     dopiero **długa** (wniosek 36) pokazuje defekty: `garrison=()` po
     `muster` (→ K117), gołe `changed:false` wojska (→ K118). Wzorce:
     (i) każdy kamień ekonomii/rozstrzygnięcia domierzać **długą** partią;
     (ii) wpis „odłożone strojenie" może zostać **obalony pomiarem** (→ K117);
     (iii) domknięcie ustalać **per klasa problemu**, nie per plasterek.
     **Wzorzec krytyczny: pomiary z żywego mostu są zapisane w asercjach
     testów** (`test_protocol.py` czyta `BACKLOG.md` i `docs/PROJECT.md`),
     więc po **każdej** edycie tych dwóch plików puścić `pytest` — kompaktowanie
     potrafi zgubić `5→7` albo pomiar K112.

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
- Brief 2026-07-30 (bramka 4 zadań graficznych/batch): zamknięty K106. **[W]**

## Kolejne prawdopodobne etapy
1–17. ~~K82–K118~~ — **zrobione** (bootstrap, most, pakiet, assety, próg
   wizualny, pętla sandboxa, ekonomia tury, diagnostyka rozkazów). Regresje
   stoją (bierna R1M7, aktywna R1M4–R1M5).
18. **US-001–US-005 — dostarczona pauzowana bitwa (migracja K119,
    2026-08-10):** po `assault` lub `engage` gracz widzi rozmieszczenie obu
    stron przed wynikiem, może przejść następną rundę albo dokończyć walkę
    automatycznie, dostaje jasną blokadę innych działań podczas bitwy i może
    wznowić zapisany stan walki. To dostarczony, najcieńszy krok ku taktycznej
    bitwie na heksach; zachowuje dotychczasowe reguły, bez wyboru celu,
    ręcznego ruchu, zmian zachowania AI, reguł walki, progu 2:1, kosztów
    rozkazów i ekonomii. Dalsza kolejka pozostaje w `BACKLOG.md`.
19. **Prawdopodobnie potem — dalsza agencja w bitwie:** wybór celu jednostki i
    sterowanie ruchem, a także pełne pole bitwy z pustymi heksami i wymiarami.
    To dawny kierunek K120+; wymaga stanu bitwy w toku z US-001–US-005.
20. **Prawdopodobnie potem — informacja i tempo sandboxa:** panel ekonomii
    osady z saldem pszenicy oraz ocena tempa presji AI, ponieważ partia nadal
    trwa zwykle 4–10 miesięcy. Dane ekonomii są w snapshocie od K63; strojenie
    tempa pozostaje odłożone do pomiaru.
21. **Etapy warunkowe zachowane ze starego backlogu:** obsługa przez AI szturmu
    na osadę zajętą przez oddział trzeciej strony dopiero po dodaniu trzeciego
    księstwa lub reprodukcji w zwykłej partii; mechaniczny teren regionów
    dopiero po wykazaniu potrzeby odrębnego znaczenia na mapie.
22. **Poza MVP, zachowane ze starego backlogu:** ewentualny alert gospodarczy
    w kliencie Godota zamiast w diagnostycznym HTML; bogatszy model ran,
    terenu i budynków; więcej typów jednostek; balans ekonomii, rozwoju i AI;
    pełna maszyna faz `StrategicTurn`.
23. **Dług zachowany ze starego backlogu:** wspólna kwerenda własnych osad
    dopiero przy następnym konsumencie wzorca oraz podział rozrośniętych plików
    `docs/ARCHITECTURE.md`, `docs/DESIGN.md`, `docs/DECISIONS.md` i tego pliku.

## Świadomie odłożone
- Kampania/fabuła, multiplayer, magia, oddziały masowe, AAA, dźwięk, edytor map
  — **poza zakresem**. Alert gospodarczy HTML (K62) — **wstrzymany**.
- Bogatszy model ran/terenu/budynków, więcej jednostek, balans/AI,
  `StrategicTurn` — po widocznej, grywalnej grze. Skala K92.2 ≠ balans.
  **Doprecyzowanie 2026-08-06/07 (aktualizowane 2026-08-09):** K108–K110, K112,
  K115, K117 (≥1 obrońcy) i K118 (powód odmowy rozkazu wojskowego) to naprawy
  **defektów rozgrywki**, nie strojenie; krzywe, wagi, **wartość progu 2:1**,
  taktyka AI, koszty rozkazów i liczba zostawionych obrońców zostają odłożone.
  Miarą jest pomiar na `seed=73`, nie ocena „czy gra jest ciekawa".
- **Pełny panel ekonomii osady w kliencie** (zapasy, produkcja, konsumpcja —
  most niesie od K63) — **nadal odłożone**. K113/K114 dały garnizon, siłę i
  wolną ludność; stan głodu niesie **tekst powodu**, nie liczby (na progu zapas
  jest jeszcze dodatni i myli — wniosek 43). Reszta — gdy pokaże ją zmierzona
  potrzeba.
- ~~Wybór osady dla rozkazów gospodarczych~~ — **zrobione jako K116**.
- **„Ile garnizonu wolno zabrać":** kształt reguły (≥1 obrońca) przesunięty do
  **K117** przez pomiar (wniosek 44); **wartość** zostaje strojeniem.
- Szturm na osadę **sąsiedniego** regionu zajętego przez oddział nie-obrońcę
  (G92.1c) — nadal odłożony: z 3. księstwem lub reprodukcją. **To nie jest
  K110.**
- Podział dużych docs (ARCHITECTURE/DECISIONS/DESIGN) — dług, nie blokuje celu.
  Ten plik trzymany pod 20 KB kompaktowaniem starych wniosków, nie podziałem.
- Niezależne reguły, AI, ekonomia, ruch, protokół, save/load i docs pozostają
  odłożone względem celu grywalnego MVP.
