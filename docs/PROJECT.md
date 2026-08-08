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
- **Oprawa K94–K105 — DOMKNIĘTA** (`1ebbbd4`…`d054581`): kompozycja, ikony,
  armie, `move`+cel, bitwa, hierarchia ekranu, PL/teatr (`WorldPresentation`),
  chrome, figury isometrii/¾. Bez reguł/mostu. **Assety K87 (Kenney CC0)
  i próg wizualny K106 — OSIĄGNIĘTE 2026-08-06**, człowiek zaakceptował
  G106.1a–c (1152×648); to odwołało bramkę oprawy 4/batch.
- `tbbui` — **tylko diagnostyka**, nie docelowy klient.
- **K107–K110 — DOMKNIĘTE:** nowa partia z UI; „Uderz na wojsko wroga" + próg
  2:1 w `ai.take_duchy_military_action` (K108); jedna akcja wojskowa na miesiąc
  — `Party.acted_this_month`, round-trip, `changed=false` zamiast błędu (K109);
  szturm „spod murów" (K110). **R111.1** zdjął zgadywanie znacznika akcji
  w kliencie. Pomiary → `BACKLOG.md`, K108–K110.
- **K111 — DOMKNIĘTY 2026-08-08**: rdzeń wskazuje
  blokujący oddział, most niesie `blocked_region`, klient mówi, kto zagradza
  drogę. **Wzorzec diagnostyki rozkazu** przez warstwy — reużywa go K114.
- **K112 — DOMKNIĘTY 2026-08-08:** oddział wciąga garnizon własnej osady
  (`reinforce`), symetrycznie dla AI. Pomiar `seed=73`: `develop`×10 →
  `recruit`×10 → `muster` kończy partię po **6 turach** (`winner: "ai"`),
  oddział AI rośnie **2 → 4** kosztem garnizonu `ai outpost` **1 → 0**.
- **K113 — DOMKNIĘTY 2026-08-08**: panel wybranego regionu pokazuje liczbę
  jednostek, PŻ i garnizon dla obu stron (`WorldPresentation`).
- **K114 — DOMKNIĘTY 2026-08-08:** rozkaz gospodarczy niesie powód odmowy
  (przejściowy vs trwały, liczy rdzeń — wniosek 42), klient pokazuje go
  po polsku oraz dokłada **wolną ludność** do panelu osady. Pełne liczby →
  `BACKLOG.md`.
- **K115 — DOMKNIĘTY 2026-08-08:** naprawa głodu (wniosek 43) — po `develop`×2
  i 5× `next_turn` wolna ludność odrasta (`free` 2→5 / 4→6), a `develop`/
  `recruit` po odroście dają `changed:true`. Regresje: bierna R1M7, aktywna
  R1M4.
- **K116 — DOMKNIĘTY 2026-08-08:** `develop`/`recruit`/`muster` kierują się
  wskazanym regionem (`target`), powód odmowy z K114 dotyczy wskazanej osady,
  a panel osady z K113 + wybór regionu z K97 razem pozwalają graczowi
  wydawać rozkazy gospodarcze „w tę osadę, którą widać". Regresje stoją:
  bierna R1M7, aktywna R1M4.
- **Pomiar kadencji 2026-08-09 (po K116, żywy most `seed=73`, wyłącznie
  rozkazy z klienta):** `pytest` zielony w całości. Regresje rozstrzygnięcia
  stoją — aktywny rush (`recruit`×5 → `muster` → `march` → `nt` → `march`
  → `nt` → `assault`) wygrywa w **R1M4**, bierny przegrywa w **R1M7**.
  Pomiar długiej partii (wniosek 36) odsłonił **nowy defekt rozgrywki, wcześniej
  uznany za strojenie**: każda strategia **poza rushem** przegrywa —
  gracz „gospodarczy" (`develop`×2 + 10× `next_turn`) w R1M7, gracz „mocna
  obrona" (`develop`×2 + `recruit`×4 + 10× `next_turn`) w R1M10. Powód w
  rdzeniu: `Settlement.muster` (`src/tbb/settlement.py:183-193`) i przez nią
  `WorldMap.reinforce_party` (`src/tbb/world.py:182-214`) zostawiają
  `garrison=()`, więc wyjście w pole = bezbronny dom, zostawienie garnizonu
  = brak armii. Trzeciej drogi nie ma. Zakres **K117**; pełne liczby →
  `BACKLOG.md`.

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

**Wnioski kierunkowe** *(1–27 z K82–K106 skompaktowane przy przeglądzie
2026-08-08 dla progu 20 KB — pełne brzmienie w historii gita, detale →
DECISIONS/BACKLOG; dawne 21–31 scalone w 21–27, stąd luka przed 32)*:
1–12. **(bootstrap, most, pakiet, assety — K82–K88).** Ścieżka rozkazu jest
    sparametryzowana, więc „kolejny przycisk" nie zbliża do celu; Godot 4.2.2
    bez `OS.execute_with_pipe` → one-shot + plik stanu (`--resume`); kontrakt
    po jednym polu ratuje mikro-TDD; **dowód „działa" dotyczy tylko artefaktu,
    na którym go zrobiono** (dev ≠ PCK); `battle.hexes` = tylko heksy
    z jednostkami; **teren istnieje wyłącznie w bitwie** (teren mapy = zmiana
    rdzenia i mostu); toolchain to osobna bramka przed treścią; **pakiet bez
    własnego Pythona**; **„plik się ładuje" ≠ poprawna treść obrazka** (CREDITS
    + review człowieka); Hexagon Pack bez postaci → RTS Medieval, strony = para
    plików, nie tint.
13. **Zielone testy ≠ grywalność** — sekwencja gracza na żywym moście.
14. Legalny wynik bitwy ≠ błąd rozkazu (K89: kontrakt przed regułą ruchu).
15. Pozycja startowa to reguła gry (K90), nie odłożony balans.
16. Gracz i AI przez te same reguły świata (K90/K91).
17–20. **(skala i sterowanie — K92, K97).** Jedna osada/stronę za mała (min.
    dwie w pięciu regionach), obrona osady odblokowała skalowanie, a 5 regionów
    odsłoniło brak **sterowania**, nie defekt skali; `march` (ku osadzie) ≠
    `move` (krok do sąsiada, bez wrogiej osady).
21–27. **(oprawa — K94–K106).** **Tekstury ≠ osiągnięty wygląd**: każdy
    przyrost widoczny na ekranie z dowodem 1152×648; oprawę da się poprawiać
    bez reguł; **rola assetu = obraz/źródło, nie nazwa**; lokalny widok ≠
    spójny ekran (ocena na pełnej scenie); jedno mapowanie PL
    (`WorldPresentation`); barwa ≠ rodzina kształtów; i dopiero **brak
    screenshotów oraz ludzkiej akceptacji** wymusił pakiet progu.
32. **Odhaczone kryterium ≠ gra (2026-08-06).** Po K106 wszystkie punkty
    kryterium „gotowe" są spełnione, a pierwszy pomiar samej rozgrywki pokazał
    trzymiesięczną, bezoporową partię. Widoczność stanu została zbudowana
    **zanim** było co pokazywać. Wzorzec powtórzony w K117 (2026-08-09).
33–35. **(K108–K109).** `Duchy.is_defeated` wymaga braku osad **i** oddziałów,
    więc reguła przegranej dyktuje kolejność plasterków. **Rozkaz bez kosztu =
    brak przeciwnika:** AI gra wyłącznie wewnątrz `next_turn`, więc presję robi
    dopiero **ekonomia tury**. Znacznik akcji obowiązuje też oddziały AI (wniosek
    16) i ustawia go **wyłącznie akcja, która zmieniła świat**. Wzorzec:
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
    kryterium sukcesu**. Naprawa odsłoniła drugi taki stan po stronie AI (armia
    bez progu 2:1 stoi 120 zmierzonych tur) → K112. **Nie naprawia się tego
    stałą.**
39. **Rekrut, który nigdy nie wychodzi za mury, to zmarnowana ekonomia
    (2026-08-07).** Brakowało **reguły wzmocnienia garnizonem** (**K112**),
    nie kolejnego przycisku; wybór osady dla rozkazów gospodarczych (**K116**)
    został osobnym plasterkiem. **Domknięte.**
40. **Dane w moście ≠ dane na ekranie (2026-08-07).** Cztery kamienie z rzędu
    naprawiały *reguły* pętli, a klient nie pokazywał żadnej liczby siły, choć
    most niósł je od K63. Kryterium „grać patrząc" pilnowaliśmy po stronie
    **oprawy** i to uśpiło pytanie, czy **da się podjąć decyzję**: rdzeń AI
    decyduje po stosunku sił 2:1, gracz po ikonce. Wzorzec na każdy przegląd:
    pytać **„czy gracz widzi to, czego reguła od niego wymaga"**. **K113/K114
    spłaciły ten dług w części (siła, wolna ludność, powód odmowy).**
41. **Rozkaz gospodarczy odmawia bez powodu, a powód bywa nieodwracalny
    (2026-08-08).** Dwie blokady: (a) chwilowa — `develop`/`recruit` czerpią z
    tej samej wolnej ludności, więc po `recruit`×8 kolejne `develop` dają
    `changed:false` (mija po turze); (b) trwała — głód (wniosek 43) zamraża
    `free` na 0 bez końca. Wzorce: (i) rozkaz bez skutku niesie **powód**, nie
    „bez zmian" (K111 ruch, K114 gospodarka); (ii) powód rozróżnia **„poczekaj"
    od „nie doczekasz się"**; (iii) zasób konkurujący ma być widoczny **zanim**
    gracz go wyda. K114 dokłada na ekran wyłącznie wolną ludność. **Domknięte
    w K114.**
42. **Diagnostyka rozkazu należy do rdzenia, nie do mostu.** K111
    (`_blocked_region_name`) powiela guardy rdzenia — nazwany dług. W K114 powód
    odmowy liczy **rdzeń**, most go tylko przenosi.
43. **Głód jest stanem pochłaniającym, a wchodzi się w niego przed pustym
    spichlerzem (2026-08-08).** Niedodatnie saldo pszenicy = koniec wzrostu na
    zawsze; **żaden rozkaz klienta tego nie odwraca**. Predykat „czy to minie"
    bierze się z **sekwencji ticków** (`tick_growth` po `tick_economy`,
    `world.py:133-145`; warunki rozjeżdżają się na progu — zapas 5 i 4,
    saldo 0 i −2), nie z pola stanu (`wheat > 0` kłamie na progu). Naprawa
    reguły = **K115** (defekt rozgrywki, nie balans; wartości progów odłożone).
    **Domknięte w K115.**
44. **Wąska pętla = kolejny stan bez wyjścia, tylko lepiej ukryty
    (2026-08-09).** Po K116 formalne kryterium sukcesu jest odhaczone,
    a pomiar krótkiej partii (rush R1M4 / bierny R1M7) wygląda dobrze.
    Dopiero **pomiar długiej partii** (wniosek 36) odsłonił, że **jedyna**
    ścieżka wygranej to rush — każda strategia gospodarcza/obronna przegrywa
    w 7–10 tur. Powód w rdzeniu: `Settlement.muster`/`reinforce_party`
    zostawiają `garrison=()` (settlement.py:191), więc gracz wybiera między
    „wyjść i zostawić bezbronny dom" a „nie wyjść i nie mieć armii". Wzorce:
    (i) **każdy kamień ekonomii/rozstrzygnięcia domierzać długą partią, nie
    tylko rushem** (scalenie z wnioskiem 36); (ii) wpis „odłożone strojenie"
    może zostać **obalony pomiarem** — wtedy zmienia priorytet (tu: „ile
    garnizonu wolno zabrać" → **K117**, defekt rozgrywki); (iii) kształt
    reguły (≥1 obrońca) to defekt, wartość to balans (to samo rozróżnienie
    co wniosek 43/K115).

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
16. **K117 — osada nie zostaje bezbronna po zbiórce/ wzmocnieniu (kadencja
    2026-08-09):** wniosek 44 — pomiar długiej partii po K116 pokazuje, że
    jedyną ścieżką wygranej jest „rush", bo `Settlement.muster`/
    `reinforce_party` opróżniają osadę do zera. Zmiana **kształtu reguły**
    (≥1 obrońca zostaje) — defekt rozgrywki, nie balans; liczba zostawionych
    obrońców zostaje odłożona. Symetryczne dla gracza i AI (wniosek 16), z
    pomiarem, że regresje K108/K109/K115/K116 stoją. Pełna diagnoza →
    `BACKLOG.md`, K117. **Bez zmian progu 2:1 z K108, tempa AI, kosztów
    rozkazów, reguł ruchu/walki i ekonomii z K115.**
17. **Prawdopodobnie potem:** tempo presji AI (partia nadal jest krótka —
    4–10 miesięcy), panel ekonomii osady (saldo pszenicy — dane w snapshocie
    od K63, gracz widzi dziś tylko `free` z K114), sterowanie jednostką w
    bitwie (dziś auto-resolve; brief mówi „rozegrać bitwę").

## Świadomie odłożone
- Kampania/fabuła, multiplayer, magia, oddziały masowe, AAA, dźwięk, edytor map
  — **poza zakresem**. Alert gospodarczy HTML (K62) — **wstrzymany**.
- Bogatszy model ran/terenu/budynków, więcej jednostek, balans/AI,
  `StrategicTurn` — po widocznej, grywalnej grze. Skala K92.2 ≠ balans.
  **Doprecyzowanie 2026-08-06/07 (zaktualizowane 2026-08-09):** K108 (nie
  szturmuj bez szans), K109 (akcja na miesiąc), K110 (szturm spod murów),
  K112 (wzmocnienie), K115 (głód) i K117 (≥1 obrońcy po `muster`) to naprawy
  **defektów rozgrywki**, nie strojenie; krzywe, wagi, **wartość progu 2:1**,
  taktyka AI, koszty rozkazów i liczba zostawionych obrońców zostają odłożone.
  Miarą jest pomiar na `seed=73`, nie ocena „czy gra jest ciekawa".
- **Pełny panel ekonomii osady w kliencie** (zapasy, produkcja, konsumpcja —
  most niesie od K63) — **nadal odłożone**. K113 wziął garnizon i siłę oddziału;
  K114 dokłada **wyłącznie wolną ludność** (rozstrzyga, czy przycisk zadziała),
  a stan głodu niesie **tekst powodu**, nie liczby (na progu zapas jest jeszcze
  dodatni i myli — wniosek 43). Zapasy/produkcja — dopiero gdy pokaże je
  zmierzona potrzeba.
- ~~Wybór osady dla rozkazów gospodarczych (`develop`/`recruit`/`muster` biorą
  *pierwszą* pasującą osadę, `target` ignorowany)~~ — **zrobione jako K116
  (2026-08-08)**.
- **„Ile garnizonu wolno zabrać" — część przesunięta do K117 (kadencja
  2026-08-09):** dotąd wpis figurował tu jako odłożone **strojenie**. Pomiar
  długiej partii po K116 (wniosek 44) obalił to — **kształt reguły** (osada
  nigdy nie jest bez obrońcy) to defekt rozgrywki i wchodzi jako K117.
  **Wartość** zostawionych obrońców pozostaje odłożonym strojeniem.
- Szturm na osadę **sąsiedniego** regionu zajętego przez oddział nie-obrońcę
  (G92.1c) — nadal odłożony: z 3. księstwem lub reprodukcją. **To nie jest
  K110**; wspólny mają wyłącznie guard `apply_settlement_battle_result`.
- Podział dużych docs (ARCHITECTURE/DECISIONS/DESIGN) — dług, nie blokuje celu.
  Ten plik trzymany pod 20 KB kompaktowaniem starych wniosków, nie podziałem.
- Niezależne reguły, AI, ekonomia, ruch, protokół, save/load, porządki i docs
  pozostają odłożone względem celu grywalnego MVP.
