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
  polsku i dokłada **wolną ludność** do panelu osady.
- **K115 — DOMKNIĘTY 2026-08-08:** naprawa głodu (wniosek 43) — po `develop`×2
  i 5× `next_turn` wolna ludność odrasta (player lands `free` 2→5 /
  population 5→8; player outpost `free` 4→6 / population 5→7, osada utracona
  na rzecz AI w turze 5), a `develop`/`recruit` po odroście dają
  `changed:true`. Regresje: bierna R1M7, aktywna R1M4.
- **K116 — DOMKNIĘTY 2026-08-08:** `develop`/`recruit`/`muster` słuchają
  wskazanego regionu (`target`) — panel osady z K113 i wybór regionu z K97
  razem pozwalają wydawać rozkazy „w tę osadę, którą widać".
- **K117.1b — POMIAR 2026-08-09, żywy most `seed=73`:** po `develop`×2,
  `recruit`×4 i `muster` osada zachowuje `garrison=1` bezpośrednio po zbiórce
  i po `next_turn` (snapshot po wznowieniu jest identyczny). Sama sekwencja
  `next_turn` kończy się przegraną gracza w **R1M7** (`winner: "ai"`), a
  aktywna sekwencja z `reinforce` (`recruit`×5 → `muster` → `march` →
  `next_turn` → `reinforce` → `next_turn` → `march` → `next_turn` →
  `assault` → `next_turn` → `assault` → `next_turn` → `assault`) daje
  zwycięstwo gracza w **R1M5** (`winner: "player"`).
  Długa ścieżka obronna `develop`×2 → `recruit`×4 → `next_turn`×20 pozostaje
  `ongoing` po 20 turach, w **R2M8**; oba snapshoty osad zachowują `player lands`
  **`garrison=3`** i `player outpost` **`garrison=3`**.
- **K118 — DOMKNIĘTY 2026-08-09:** żywy most `seed=73` przez dwa procesy
  przenosi powody odmowy wojskowej przy `changed:false`: po `muster`
  `engage` mówi „W zasięgu nie ma wrogiego wojska.”, a `assault` mówi
  „W zasięgu nie ma wrogiej osady — uderz na wojsko wroga.”. Na trasie
  `recruit`×3 → `muster` → `march` → `next_turn` oddział gracza w `player
  outpost` dostaje od `assault` wskazanie `engage`, a wznowiony proces
  rozstrzyga starcie; powód mostu i status klienta są identycznie zmapowane.
  Regresje pozostają: rush wygrywa w **R1M4**, bierny gracz przegrywa w
  **R1M7**, a K115/K116/K117 zachowują odpowiednio odrost ludności, wskazany
  cel gospodarczy i `garrison>=1`.
- **Pomiar kadencji 2026-08-09 (bazowy, przed K117, żywy most `seed=73`,
  wyłącznie rozkazy z klienta).** Regresje rozstrzygnięcia stały — rush
  (`recruit`×5 → `muster` → `march` → `nt` → `march` → `nt` → `assault`)
  wygrywał w **R1M4**, bierny przegrywał w **R1M7**. Pomiar długiej partii
  (wniosek 36) odsłonił defekt wcześniej uznany za strojenie: **każda
  strategia poza rushem przegrywała** — „gospodarcza" w R1M7, „mocna obrona"
  w R1M10, bo `Settlement.muster` (`settlement.py:183-193`) i
  `WorldMap.reinforce_party` (`world.py:182-214`) zostawiały `garrison=()`.
- **Druga kadencja 2026-08-09 (przegląd po pomiarze K117.1b).** K117 pozostaje
  priorytetem do domknięcia części klientowej i długiego pomiaru. Dwa nowe
  ustalenia: (a) **`pytest` nie był zielony** — poprzedni przegląd, kompaktując
  ten plik, wykasował z niego zmierzony marker `5→7` i wywalił
  `test_seed73_free_population_regrows_on_live_bridge_and_k115_is_closed`
  (naprawione tutaj, wniosek 45); (b) **rozkazy wojskowe odmawiają bez powodu**
  — na `seed=73` `engage` i `assault` bez celu w zasięgu dają gołe
  `{"changed": false}` przy `acted_this_month=false`, więc klient mówi tylko
  „Rozkaz szturm nie zmienił stanu.". Zakres **K118**; liczby → `BACKLOG.md`.

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
39. **Rekrut, który nigdy nie wychodzi za mury, to zmarnowana ekonomia
    (2026-08-07).** Brakowało **reguły wzmocnienia garnizonem** (K112), nie
    kolejnego przycisku. **Domknięte.**
40. **Dane w moście ≠ dane na ekranie (2026-08-07).** Cztery kamienie z rzędu
    naprawiały *reguły* pętli, a klient nie pokazywał żadnej liczby siły, choć
    most niósł je od K63. Kryterium „grać patrząc" pilnowaliśmy po stronie
    **oprawy** i to uśpiło pytanie, czy **da się podjąć decyzję**: rdzeń AI
    decyduje po stosunku sił 2:1, gracz po ikonce. Wzorzec na każdy przegląd:
    pytać **„czy gracz widzi to, czego reguła od niego wymaga"**. **K113/K114
    spłaciły ten dług w części (siła, wolna ludność, powód odmowy).**
41. **Rozkaz odmawia bez powodu, a powód bywa nieodwracalny (2026-08-08).**
    Dwie blokady: (a) chwilowa — `develop`/`recruit` dzielą wolną ludność, więc
    po `recruit`×8 `develop` daje `changed:false` (mija po turze); (b) trwała —
    głód (wniosek 43) zamraża `free` na 0. Wzorce: (i) rozkaz bez skutku niesie
    **powód**, nie „bez zmian" (K111 ruch, K114 gospodarka, **K118 wojsko** —
    wniosek 45); (ii) powód rozróżnia **„poczekaj" od „nie doczekasz się"**;
    (iii) zasób konkurujący ma być widoczny **zanim** gracz go wyda.
42. **Diagnostyka rozkazu należy do rdzenia, nie do mostu.** K111
    (`_blocked_region_name`) powiela guardy rdzenia — nazwany dług. W K114 powód
    odmowy liczy **rdzeń**, most go tylko przenosi.
43. **Głód jest stanem pochłaniającym, a wchodzi się w niego przed pustym
    spichlerzem (2026-08-08).** Niedodatnie saldo pszenicy = koniec wzrostu na
    zawsze; **żaden rozkaz klienta tego nie odwraca**. Predykat „czy to minie"
    bierze się z **sekwencji ticków** (`tick_growth` po `tick_economy`,
    `world.py:133-145`), nie z pola stanu (`wheat > 0` kłamie na progu).
    Naprawa reguły = **K115** (defekt rozgrywki, nie balans).
44. **Wąska pętla = kolejny stan bez wyjścia, tylko lepiej ukryty
    (2026-08-09).** Krótka partia wygląda dobrze (rush R1M4 / bierny R1M7);
    dopiero **długa** (wniosek 36) pokazała, że **jedyną** ścieżką wygranej
    jest rush, bo `Settlement.muster`/`reinforce_party` zostawiają
    `garrison=()` (`settlement.py:191`) — wybór stoi między „bezbronny dom"
    a „brak armii". Wzorce: (i) każdy kamień ekonomii/rozstrzygnięcia
    domierzać **długą** partią; (ii) wpis „odłożone strojenie" może zostać
    **obalony pomiarem** i zmienić priorytet (→ K117); (iii) kształt reguły
    to defekt, wartość to balans (jak wniosek 43/K115).
45. **Powód odmowy domknięto tylko dla połowy rozkazów, a dokument jest
    testowany (2026-08-09).** Dwie rzeczy, jedna przyczyna — „zrobione" ustalano
    per plasterek, nie per klasa problemu. (a) Wniosek 41(i) mówi „rozkaz bez
    skutku niesie powód"; K111 dał to marszowi, K114 gospodarce, ale **rozkazy
    wojskowe `assault`/`engage` odmawiają gołym `changed:false`** — zmierzone
    na `seed=73`. Klient ma tylko jeden wyjątek (wyczerpana akcja miesiąca,
    czytana z `acted_this_month`); każdy inny powód schodzi do „Rozkaz szturm
    nie zmienił stanu.". → **K118**. (b) Pomiary z żywego mostu są **zapisane
    w asercjach testów** (`test_protocol.py` czyta `BACKLOG.md` i
    `docs/PROJECT.md`), więc kompaktowanie tych plików potrafi zepsuć zielony
    build — poprzedni przegląd zgubił `5→7`, a ten przegląd przy pierwszej próbie
    kompaktacji zgubił pomiar K112. **Wzorzec: po każdej edycji
    tych dwóch plików puścić `pytest`, nawet gdy zmiana jest „tylko
    dokumentacyjna".**

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
1–12. ~~K82–K113~~ — **zrobione**. 13–15. ~~K114/K115/K116~~ — **zrobione
   2026-08-08**. Regresje stoją (bierna R1M7, aktywna R1M4).
16. **K117 — osada nie zostaje bezbronna po zbiórce/wzmocnieniu (kadencja
    2026-08-09):** wniosek 44 — zmiana **kształtu reguły** (≥1 obrońca
    zostaje), defekt rozgrywki, nie balans; liczba obrońców odłożona.
    Symetryczne dla gracza i AI, z pomiarem, że regresje K108/K109/K115/K116
    stoją. **Bez zmian progu 2:1, tempa AI, kosztów rozkazów, reguł
    ruchu/walki i ekonomii z K115.** Diagnoza → `BACKLOG.md`, K117.
17. **K118 — szturm i starcie mówią, dlaczego nic nie zrobiły (kadencja
    2026-08-09):** wniosek 45(a). Domyka klasę „rozkaz bez skutku niesie
    powód" (wniosek 41(i)) na ostatnich dwóch rozkazach, tą samą drogą co
    K111/K114: **rdzeń liczy powód** (wniosek 42), most go przenosi, klient
    tłumaczy na polski, pomiar na żywym moście. Zakres wąski: żadnych zmian
    reguł walki, ruchu, progu 2:1 ani ekonomii. Diagnoza → `BACKLOG.md`, K118.
18. **Prawdopodobnie potem:** tempo presji AI (partia nadal jest krótka —
    4–10 miesięcy), panel ekonomii osady (saldo pszenicy — dane w snapshocie
    od K63, gracz widzi dziś tylko `free` z K114) oraz **sterowanie jednostką
    w bitwie** — dziś bitwa jest w całości `auto_resolve` w rdzeniu, a brief
    mówi „taktyczne bitwy na heksach" i „rozegrać bitwę". To **największa
    otwarta rozbieżność z briefem**; formalne kryterium odhaczyliśmy czytając
    „rozegrać" jako „zobaczyć wynik". Nie otwieramy tego przed K117/K118, ale
    to najpoważniejszy kandydat na kolejny kamień.

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
