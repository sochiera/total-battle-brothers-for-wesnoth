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
- **K114 — DOMKNIĘTY 2026-08-08:** żywy most `seed=73` potwierdza trzy stany
  odmowy rozkazu gospodarczego: przejściowy po `recruit`×8 → `develop`, trwały
  przy niezerowym zapasie 5/4 i saldzie 0/−2, z potwierdzonym brakiem wzrostu
  Keep 8→8 i Outpost 9→9, oraz nadal trwały przy zapasie 0. Regresje stoją:
  bierna partia kończy się w R1M7, aktywna w R1M4.
- **Pomiar przy przeglądzie 2026-08-08 (po K112/K113), sprostowany po
  recenzji:** `pytest` zielony w całości (3m06s). Żywy most `seed=73`:
  regresje stoją — aktywny gracz (`recruit`×10 → `muster` →
  `assault`/`engage`/`march`) wygrywa w **roku 1, miesiącu 4**, bierny
  przegrywa w **roku 1, miesiącu 7** (6× „Następna tura"). Odsłonięty brak
  następny: **rozkaz gospodarczy odmawia bez powodu**, przy czym zmierzone są
  **dwie różne blokady**. (a) Chwilowa, w obrębie tury: `develop` i `recruit`
  czerpią z tej samej wolnej ludności, więc `recruit`×8 zeruje `free` i osiem
  kolejnych `develop` daje `changed:false`; po turze `free` odrasta.
  (b) Trwała, i to ona zabija gospodarkę: konsumpcja równa ludności
  przewyższa produkcję, więc ludność zamiera, `free` stoi na 0 i rozkaz
  gospodarczy odmawia turę po turze bez końca. Klient pokazuje na obie to
  samo „bez zmian". Zakres **K114**; pełne liczby → `BACKLOG.md`.

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
    **zanim** było co pokazywać.
33–35. **(K108–K109).** `Duchy.is_defeated` wymaga braku osad **i** oddziałów,
    więc reguła przegranej dyktuje kolejność plasterków (powściągliwsze AI bez
    `engage` w kliencie czyniło partię niewygrywalną). **Rozkaz bez kosztu =
    brak przeciwnika:** AI gra wyłącznie wewnątrz `next_turn`, więc presję robi
    dopiero **ekonomia tury**. Warunki brzegowe znacznika akcji: obowiązuje też
    oddziały AI (wniosek 16) i ustawia go **wyłącznie akcja, która zmieniła
    świat**. Wzorzec: **regresję K108 mierzy się na `seed=73` przy każdej
    zmianie reguł ruchu i walki.**
36. **Kosztowna tura odsłania koniec ścieżki, nie koniec pracy (2026-08-07).**
    Dopóki rozkazy były darmowe, nikt nie dochodził do stanu „armia stoi pod
    obcą stolicą"; po K109 partia trwa latami i dopiero wtedy było widać, że
    **rdzeń nie znał szturmu spod murów** (→ `BACKLOG.md`, K110). Wzorzec:
    **każde domknięcie ekonomii tury domierzyć długą partią, nie krótką** —
    defekty kolejnego etapu leżą za horyzontem poprzedniego.
37–38. **Zakleszczenie ≠ przegrana, i to jest gorsze (2026-08-07).** Stan bez
    wyjścia nie daje sygnału: „bez zmian", kalendarz idzie, nic się nie dzieje;
    reguła symetryczna (wniosek 16) zakleszcza tak samo AI, więc **K110 broni
    kryterium sukcesu**, nie wygody gracza. Naprawa natychmiast odsłoniła drugi
    taki stan po stronie AI (armia bez progu 2:1 stoi 120 zmierzonych tur):
    dopóki jedynym kształtem akcji AI jest „maszeruj i szturmuj przy
    przewadze", każdy niespełniony warunek zamienia przeciwnika w dekorację.
    **Nie naprawia się tego stałą.**
39. **Rekrut, który nigdy nie wychodzi za mury, to zmarnowana ekonomia
    (2026-08-07).** `recruit`/`muster` biorą *pierwszą* pasującą osadę, więc ta
    sama sekwencja daje oddział 1 albo 5 jednostek zależnie od tego, czy padło
    wcześniej `develop`. Brakowało **reguły wzmocnienia garnizonem** (**K112**),
    nie kolejnego przycisku; wybór osady dla rozkazów gospodarczych zostaje
    osobnym, późniejszym plasterkiem.
40. **Dane w moście ≠ dane na ekranie (2026-08-07).** Cztery kamienie z rzędu
    naprawiały *reguły* pętli, a przy pomiarze okazało się, że klient nie
    pokazuje **żadnej liczby siły**, choć most niesie je od K63. Kryterium
    „grać patrząc" pilnowaliśmy po stronie **oprawy** i to uśpiło pytanie, czy
    przez ten ładny ekran **da się podjąć decyzję**: rdzeń AI decyduje po
    stosunku sił 2:1, gracz po ikonce. Wzorzec na każdy przegląd: obok „czy
    reguła działa" pytać **„czy gracz widzi to, czego reguła od niego
    wymaga"**. **K113** to pierwsza spłata — projekcja danych, które już
    przychodzą, nie nowa seria polish.
41. **Rozkaz gospodarczy odmawia bez powodu, a powód bywa nieodwracalny
    (2026-08-08).** Dwie blokady: (a) chwilowa — `develop`/`recruit` czerpią z
    tej samej wolnej ludności, więc po `recruit`×8 kolejne `develop` dają
    `changed:false` (mija po turze); (b) trwała — głód (wniosek 43) zamraża
    `free` na 0 bez końca. Wzorce: (i) rozkaz bez skutku niesie **powód**, nie
    „bez zmian" (K111 ruch, K114 gospodarka); (ii) powód rozróżnia **„poczekaj"
    od „nie doczekasz się"**; (iii) zasób konkurujący ma być widoczny **zanim**
    gracz go wyda. K114 dokłada na ekran wyłącznie wolną ludność.
42. **Diagnostyka rozkazu należy do rdzenia, nie do mostu.** K111
    (`_blocked_region_name` w `protocol.py:41`) powiela guardy rdzenia —
    nazwany dług. W K114 powód odmowy liczy **rdzeń**, most go tylko przenosi.
43. **Głód jest stanem pochłaniającym, a wchodzi się w niego przed pustym
    spichlerzem (2026-08-08).** Gdy saldo pszenicy przestaje być dodatnie,
    **żaden rozkaz klienta tego nie odwraca** (`muster` zbija konsumpcję, ale
    przy produkcji 3 saldo 0 — warunek ostry, ludność nie rośnie). K114 ma
    **nazwać** stan, nie doradzać wyjścia, którego nie ma. Klucz: predykat
    „czy to minie" bierze się z **sekwencji ticków** (`tick_growth` po
    `tick_economy`, `world.py:133-145`; warunki rozjeżdżają się na progu —
    zapas 5 i 4, saldo 0 i −2), nie z pola stanu (`wheat > 0` kłamie na progu).
    Naprawa reguły (produkcja / próg / zapas) to **K115**, defekt rozgrywki,
    nie balans; wartości progów odłożone.

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
1–12. ~~K82–K113~~ — **zrobione** (K111–K113 dnia 2026-08-08); regresje
   K108/K109 stoją. Szczegóły w „Stan faktyczny" i `BACKLOG.md`.
13. **K114 — rozkaz gospodarczy mówi, dlaczego nic nie zrobił** (nowe, ten
   przegląd): rdzeń zwraca jawny powód odmowy `develop`/`recruit`/`muster`
   (brak złota, komplet budynków, limit garnizonu oraz — **rozdzielnie** —
   brak wolnej ludności *przejściowy* i *trwały*, rozróżniane **saldem
   miesięcznym po ticku**, nie stanem spichlerza — wniosek 43), most przenosi
   go obok `changed:false`, klient mówi to po polsku
   i pokazuje w panelu osady **wolną ludność** obok garnizonu z K113; pomiar
   na żywym moście z regresjami. Powód: wnioski 41–43. **Bez zmian kosztów,
   progu 2:1, tempa AI i bez pełnego panelu ekonomii.**
14. **K115 — naprawa głodu (przesądzona pomiarem przy tym przeglądzie):**
    wniosek 43 — niedodatnie saldo pszenicy jest stanem, z którego gracz nie ma
    wyjścia żadnym dostępnym rozkazem. K114 ten stan **nazywa**, K115 go
    **naprawia**; kandydat „wybór osady" ustępuje, bo w stanie trwałym obie osady
    mają `free=0` i wybór niczego nie odblokowuje. **Defekt rozgrywki, nie
    balans** — zmienia się kształt reguły, wartości zostają odłożone. Pełna
    diagnoza → `BACKLOG.md`, K115.
15. **Prawdopodobnie potem:** wybór osady dla
    `develop`/`recruit`/`muster` (`target` ignorowany — potwierdzone pomiarem
    2026-08-08), tempo presji AI, ile garnizonu wolno zabrać, sterowanie
    jednostką w bitwie.

## Świadomie odłożone
- Kampania/fabuła, multiplayer, magia, oddziały masowe, AAA, dźwięk, edytor map
  — **poza zakresem**. Alert gospodarczy HTML (K62) — **wstrzymany**.
- Bogatszy model ran/terenu/budynków, więcej jednostek, balans/AI,
  `StrategicTurn` — po widocznej, grywalnej grze. Skala K92.2 ≠ balans.
  **Doprecyzowanie 2026-08-06/07:** K108 (nie szturmuj bez szans), K109 (akcja
  na miesiąc), K110 (szturm spod murów) i K112 (wzmocnienie garnizonem) to
  naprawy defektów rozgrywki, nie strojenie AI; krzywe, wagi, **wartość progu
  2:1**, taktyka AI i koszty rozkazów gospodarczych zostają odłożone. Miarą
  jest pomiar na `seed=73`, nie ocena „czy gra jest ciekawa". **To samo
  rozróżnienie dotyczy głodu (wniosek 43):** „niedodatnie saldo = koniec
  wzrostu na zawsze" to defekt, ale konkretne liczby produkcji i konsumpcji
  to balans.
- **Pełny panel ekonomii osady w kliencie** (zapasy, produkcja, konsumpcja,
  ludność — most niesie to od K63) — **nadal odłożone**. K113 wziął garnizon
  i siłę oddziału (decyzja „bić czy nie"); K114 dokłada **wyłącznie wolną
  ludność**, bo zmierzono (wniosek 41), że to ona rozstrzyga, czy przycisk
  gospodarczy zadziała — a stan głodu niesie **tekst powodu**, nie liczby
  pszenicy (na progu zapas jest jeszcze dodatni i sam w sobie myli, wniosek
  43). Zapasy i produkcja — dopiero gdy pokaże je zmierzona potrzeba.
- Wybór osady dla rozkazów gospodarczych (`develop`/`recruit`/`muster` biorą
  *pierwszą* pasującą osadę, `target` ignorowany) — blokada „do po K112"
  **wygasła**; teraz odłożone **do po K114**, patrz etap 14b.
- „Ile garnizonu wolno zabrać" (`muster` i K112 opróżniają osadę do zera) —
  **odłożone**: strojenie, nie defekt blokujący pętlę.
- Szturm na osadę **sąsiedniego** regionu zajętego przez oddział nie-obrońcę
  (G92.1c) — nadal odłożony: z 3. księstwem lub reprodukcją. **To nie jest
  K110**; wspólny mają wyłącznie guard `apply_settlement_battle_result`.
- Podział dużych docs (ARCHITECTURE/DECISIONS/DESIGN) — dług, nie blokuje celu.
  Ten plik trzymany pod 20 KB kompaktowaniem starych wniosków, nie podziałem.
- Niezależne reguły, AI, ekonomia, ruch, protokół, save/load, porządki i docs
  pozostają odłożone względem celu grywalnego MVP.
