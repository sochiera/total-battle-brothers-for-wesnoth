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

Kryterium pomocnicze, po którym poznajemy postęp: **da się grać patrząc, a nie
czytając logi**. Widok mapy i widok bitwy mają nieść stan gry wizualnie. **[W]**

**Assety są częścią kryterium, nie polishem po MVP.** Feedback autora briefu
(2026-07-27): *„prawdziwe MVP będzie wtedy, kiedy będą assety i tekstury. Nie
musi być dużo budynków/rodzajów jednostek/terenu itp, ale żeby były jakieś
sensowne prawdziwe assety."* Czyli: widoki mają rysować **realne pliki
graficzne**, nie jednolite prostokąty z etykietą tekstową. Zakres świadomie
mały — po kilka kafli terenu, sylwetek jednostek i budynków — ale prawdziwych.
**[W]**

## Stan faktyczny (aktualizowany przy przeglądach)
- Rdzeń `tbb` (Python): kampania, ekonomia (pszenica/złoto, populacja, budynki),
  kalendarz 13×4 tygodnie, jednostki i trzy filary progresji, morale, bitwa na
  heksach, AI księstw, sukcesja — **działa headless, pokryty TDD**.
- Most `tbbbridge`: snapshot JSON (OUT), komendy i rozkazy gracza (IN), protokół
  JSON Lines na stdio, `serve` / `serve --resume`, round-trip persystencji
  (save/load całej sesji łącznie z RNG i `last_battle`) — **gotowe**.
- Klient Godot 4 w `game/`: `SnapshotModel`, `BridgeClient` (jedno-strzałowe
  wywołania procesu mostu + plik stanu), scena z datą, listą regionów, statusem
  księstwa, położeniem oddziału, statusem ostatniego rozkazu oraz przyciskami
  „Następna tura", „Rozwiń osadę", „Rekrutuj jednostkę", „Zbierz oddział",
  „Wyrusz w pole", „Szturmuj osadę".
- **Start bez terminala działa w drzewie źródeł** (K82): bez żadnej zmiennej
  `TBB_*` klient sam składa komendę mostu, ścieżkę stanu i ziarno, a gdy most nie
  wstanie — pokazuje komunikat zamiast martwej sceny. Repo gry posprzątane
  (R82.1); układ ekranu czytelny, kontrolki w kontenerach (K83).
- **Oba widoki działają** (K84/K85): `MapView` rysuje kafel na region po
  `col`/`row` z rozróżnialnym właścicielem i przesuwającym się oddziałem gracza;
  `BattleView` rysuje heksy po `(q, r)` z rozróżnialnymi stronami i czytelnym
  wynikiem po kliknięciu „Szturmuj osadę".
- **Zapis/odczyt z UI działa** (K86): konfiguracja niesie `save_path`, scena ma
  przyciski „Zapisz partię"/„Wczytaj partię", a klik przywraca zapisany stan na
  ekranie i utrwala partię między procesami.
- **Prawdziwe assety w repo — DOMKNIĘTE** (K87): `game/assets/` niesie 10 plików
  PNG z dwóch paczek CC0 (Kenney Hexagon Pack — kafle mapy i terenu; Kenney „RTS
  Pack: Medieval" — sylwetki stron) z atrybucją **per plik** w `CREDITS.md`;
  `.godot/` poza gitem. `MapView` rysuje grunt/osadę/oddział teksturami,
  `BattleView` teren heksu i sylwetkę strony; R87.1 scalił warstwę tekstury
  kafla w jedno źródło dla obu widoków.
- **Pakiet na Linuksa — DOMKNIĘTY** (K88, 7 z 7): preset „Linux/X11" x86-64 w
  repo + szablony 4.2.2 poza gitem (G88.1a), `src/` mostu rozwiązywane odpornie
  na eksport (G88.1b), `scripts/package.sh <cel>` składa katalog dystrybucyjny
  (G88.1c), `.pck` bez sond testowych (G88.1d), sam start gry utrwala partię
  (G88.1e), **e2e na wyeksportowanym pakiecie dowodzi startu bez terminala**
  (G88.1f), wpis `.desktop` daje uruchomienie jednym kliknięciem (G88.1g).
  Formalne kryterium „natywna aplikacja bez terminala" jest odhaczone.
- **Bitwa zawsze daje wynik — w połowie** (K89): K89.1 domknięte (rdzeń traktuje
  bitwę bez rozstrzygnięcia jako legalny wynik, most zwraca ją z własnym
  `outcome`, scena pokazuje „szturm nierozstrzygnięty" ze stratami, e2e na żywym
  moście). Z K89.2 zrobiony jest rdzeń (G89.2a-1: jednostka przechodzi przez
  własnego ogłuszonego sojusznika); w kolejce planisty zostają dwa plasterki.
- `tbbui` (HTML/SVG) — **wyłącznie narzędzie diagnostyczne**, nie docelowy klient.

**Czego brakuje do celu (nazwane wprost, bo tu jest cała reszta pracy):**
1. **K89 do domknięcia** — dwa plasterki w kolejce planisty: szturm z repro ma
   kończyć się realnym rozstrzygnięciem, a gracz ma zobaczyć rozstrzygniętą
   bitwę na żywym moście. Kontrakt wyniku (K89.1) i reguła ruchu (G89.2a-1) są
   już w rdzeniu.
2. **Gracz przegrywa całą partię po pierwszym kliknięciu „Następna tura" —
   i nikt mu tego nie mówi.** Odtworzone uruchomieniem kodu 2026-07-28: start
   jest **asymetryczny** (`tbb.game.create_headless_game`) — AI Keep dostaje
   `garrison=(Unit(training=5, equipment=12),)`, Player Keep **pustą załogę** —
   więc AI w jednej turze robi muster → march → assault na bezbronną osadę
   gracza i ją przejmuje. Rekrutacja przed turą nie ratuje: rekrut ma
   `equipment=0`, a `Unit.damage == equipment`, czyli **zadaje zero obrażeń**
   (sprawdzone dla 1, 2 i 3 rekrutów — osada pada tak samo). Od drugiej tury
   księstwo gracza ma 0 osad i 0 oddziałów, a każdy rozkaz jest no-opem.
3. **Koniec gry jest nieosiągalny dla gracza.** `driver.resolve_hero_survival`
   jest wołany **wyłącznie dla księstw AI** (`driver.py` robi `continue` dla
   `player_duchy_id` przed akcją militarną), a `session.apply_command` po
   rozkazach gracza robi tylko `sync_from_world`. Bohater gracza nigdy nie
   ginie → `Duchy.is_defeated` nigdy nie jest prawdą → `game.is_over` zostaje
   `False`, a klient w nieskończoność pokazuje `Wynik: ongoing` (surowy token
   angielski w polskim UI, `game/scripts/main.gd:164`). Sprawdzone symulacją 150
   tur: gracz bez osad i oddziałów gra dalej „w nic".

Punkty 2 i 3 to **realny stan grywalności**, nie hipoteza: pełny pythonowy
zestaw testów jest zielony (4 s), a mimo to partia jest rozstrzygnięta przeciw
graczowi zanim zdąży cokolwiek zrobić. Rozplanowane jako **K90**.

## Ograniczenia i priorytety
- **[W]** Rdzeń `tbb` jest **jedynym źródłem reguł gry**. Godot nie duplikuje
  logiki; Python nie zależy od Godota ani żadnego UI.
- **[W]** Komunikacja Godot↔Python przez jawny, testowalny interfejs (stan gry
  jako JSON). Transport i kształt API wybiera i uzasadnia agent — obecnie:
  proces `python -m tbbbridge serve`, JSON Lines po stdio, stan w pliku.
- **[W]** Budowa klienta Godota jest **bieżącym priorytetem**. Nie wolno w
  nieskończoność dokładać mechaniki kosztem widocznej, grywalnej gry.
- **[W]** Determinizm: seedowalny RNG, testy bez losowości.
- **[W]** TDD, małe przyrosty; każde zadanie ma kryteria akceptacji. Trudność
  `simple|standard|complex` + flagi ryzyka; bootstrap/toolchain/integracja
  Godot↔Python idą jako `complex` i przechodzą review pętli agentowej.
- **[P]** Rdzeń przed prezentacją **wewnątrz jednego plasterka** — ale plasterek
  ma kończyć się czymś widocznym na ekranie, nie samą regułą.
- **[W]** Widoki mają rysować **prawdziwe assety graficzne** (patrz kryterium
  sukcesu). Ilość jest mała i negocjowalna; *istnienie* assetów nie jest.
- **[P]** Źródłem assetów są gotowe paczki open source (CC0: Kenney,
  OpenGameArt) zamiast rysowania własnych; licencja i atrybucja zapisane w repo.
  Grafika ma być czytelna, nie ładna.
- **[P]** Pakiet na Linuksa zakłada **systemowy `python3`**; nie wnosimy własnego
  runtime'u Pythona (patrz wniosek 10). Bundling CPythona: **[O]**.
- **[O]** Wykorzystanie kodu/zasobów z Battle for Wesnoth.

**Wnioski z dotychczasowej pracy, które zmieniają kierunek:**
1. K75–K81 to była seria „kolejny przycisk rozkazu"; ścieżka rozkazu jest
   sparametryzowana, więc szósty przycisk nie zbliża do celu. Cała ta kolejka
   (start bez terminala → układ ekranu → mapa → bitwa → pakiet) jest wykonana.
2. Godot 4.2.2 nie ma `OS.execute_with_pipe`, więc most wołamy jedno-strzałowo,
   a ciągłość partii daje plik stanu (`serve --resume`). To zadziałało i zostaje.
3. Odchudzanie kontraktu na liście (jedno pole / jedna grupa pól na zadanie)
   ratuje mikro-TDD tam, gdzie „cały słownik naraz" wcześniej wykładał kodera.
4. **Start bez terminala trzeba było udowodnić dwa razy — i to zadziałało.**
   Po eksporcie `res://` wskazuje wnętrze PCK, więc domyślna komenda mostu z K82
   przestawała działać; K88 rozwiązał `src/` względem binarium i **powtórzył
   dowód startu na wyeksportowanym pakiecie** (G88.1b, G88.1f). Wzorzec zostaje:
   dowód „działa" jest ważny tylko dla tego artefaktu, na którym go zrobiono.
5. Snapshot bitwy (`battle.hexes`) niesie **wyłącznie heksy zajęte przez
   jednostki**, bez wymiarów pola i terenu pustych heksów. Pierwszy widok bitwy
   rysuje więc jednostki, nie całą planszę; pełna siatka to osobna, późniejsza
   zmiana mostu.
6. **Kolorowy prostokąt wystarczył na „widać stan gry", ale nie na MVP.** K84/K85
   domknęły to kryterium strukturalnie, brakującym elementem były assety (K87);
   podmiana nośnika nie ruszyła geometrii ani testów rozmieszczenia.
7. **Prerekwizyt toolchainu idzie w osobną bramkę, przed treścią.** Import
   tekstur (G87.1a) i eksport binarium (G88.1a) rozstrzygnięto tak zanim
   ktokolwiek ruszył widoki i zawartość pakietu — w obu kamieniach reszta
   plasterków poszła potem bez niespodzianek. Wzorzec zostaje.
8. **Teren istnieje tylko w warstwie bitwy — mapa strategiczna go nie zna.**
   `tbb.world.Region` ma samo `name`, więc `map_state` daje `name`, `col`, `row`,
   `owner`, `settlement`, `party`; kafle mapy teksturujemy po właścicielu i
   obecności osady. Teren regionu to **osobna zmiana rdzenia i mostu**,
   świadomie odłożona; klientowi nie wolno wymyślić go u siebie.
9. **Podmiana nośnika nie kosztowała czytelności.** Kafle są dziś teksturą
   przyciemnianą `modulate` w kolorze właściciela/strony, więc kryteria
   rozróżnialności z K84/K85 przeszły bez jednej zmiany. Wniosek na przyszłość:
   warstwa tekstury + tint zamiast osobnego assetu na każdy wariant — mała
   paczka wystarcza, a testy geometrii zostają w mocy.
10. **Pakiet nie wnosi własnego Pythona.** Odbiorcą jest jeden użytkownik na
    Linuksie x86-64, który ma `python3` w systemie (zweryfikowane: 3.14.4).
    Bundling CPythona podwoiłby zakres K88 i nie wynika z briefu, więc pakiet
    zakłada systemowy `python3`, a jego brak daje czytelny komunikat w scenie
    (ścieżka błędu istnieje od K82). To decyzja zakresowa, nie ograniczenie
    techniczne — jeśli okaże się za wąska, wraca jako osobny plasterek.
11. **Bramka „plik się ładuje" nie sprawdza, *co* jest na obrazku — i to nas
    kosztowało plasterek.** G87.1a przyjęło jako „sylwetki stron" dwa budynki z
    Hexagon Packa tylko dlatego, że nazwa pliku brzmiała `side_*.png`, a `load()`
    zwracał `Texture2D`. **Wniosek na każdy kolejny plasterek assetowy:**
    kryterium akceptacji wiąże plik z jego *źródłem* w `CREDITS.md` (konkretna
    ścieżka w paczce, nie sama nazwa paczki) i z maszynowo sprawdzalnym kształtem
    (przezroczyste tło, rozmiar mniejszy od kafla, obie strony różne bajtowo), a
    człowiek ogląda obrazek przy review. Dobór paczki sprawdzamy po **liście
    plików**, zanim wejdzie do repo. To szczególny przypadek wniosku 13.
12. **Jedna paczka nie wystarczy — świadome odstępstwo od [P].** Hexagon Pack nie
    ma postaci, więc sylwetki przyszły z drugiej paczki CC0 (RTS Pack: Medieval).
    Lepiej mieszany styl z prawdziwą figurą niż spójny styl z budynkiem
    udającym żołnierza. Rozróżnialność stron wzięła się z **dwóch różnych
    plików**, nie z `modulate` (tint zaszarza już pokolorowaną figurkę);
    „tekstura + tint" z wniosku 9 zostaje dla kafli terenu.
13. **Zielony zestaw testów nie znaczy, że dało się zagrać — defekt szturmu
    znalazło dopiero uruchomienie gry ręką.** Rdzeń jest pokryty TDD, most też,
    klient ma e2e przez dwa procesy — a mimo to najbardziej naturalna sekwencja
    gracza (dorekrutuj → zbierz → wyrusz → szturmuj) kończy się błędem rozkazu.
    Testy bitwy sprawdzały składy, które *rozstrzygają się*; pat, w którym własny
    ogłuszony blokuje jedyne dojście, nie miał testu, bo nikt go nie wymyślił
    przy biurku. **Wniosek na kierunek:** od teraz każdy przegląd (i najlepiej
    każdy plasterek domykający kamień) kończy się **przejściem pełnej sekwencji
    gracza na żywym moście**, nie samym `pytest`. Po K88 ta sekwencja idzie na
    wyeksportowanym pakiecie, nie w drzewie źródeł — bo to jest artefakt, który
    dostaje odbiorca.
14. **Kontrakt „wynik bitwy" był niepełny, nie tylko zabugowany.** `HexBattle`
    dopuszcza stan „nikt nie wygrał po wyczerpaniu rund" (`result() is None`), a
    `WorldMap` nie ma dla niego przypadku i rzuca `ValueError`. Naprawa reguły
    ruchu (żeby akurat ten pat nie występował) **nie zamyka klasy problemu** —
    inny pat wróci tą samą ścieżką. Dlatego K89 najpierw domyka kontrakt
    (nierozstrzygnięta bitwa = legalny wynik, świat spójny, gracz widzi tekst),
    a dopiero potem rusza reguły ruchu. Kolejność jest tu decyzją, nie wygodą.
15. **Pozycja startowa to reguła gry, nie balans — i dziś jest wywrotowa.**
    Player Keep startuje bez garnizonu, AI Keep z weteranem
    (`training=5, equipment=12`). To nie jest „za trudno": to znaczy, że gracz
    traci jedyną osadę w pierwszej turze, cokolwiek zrobi. Sprawdzone
    prototypem: **symetryczny start** (obie osady z takim samym garnizonem)
    utrzymuje osadę gracza przez ≥10 tur biernej gry, a AI traci przy tym własny
    garnizon na szturmach — czyli powstaje realna sytuacja do rozegrania.
    Wyrównanie startu **nie** jest odłożonym „balansem ekonomii i AI": bez niego
    pętla sandboxa nie ma jak się zacząć.
16. **Warunek końca gry jest opisany, ale nieosiągalny — bo śmierć bohatera
    rozstrzygamy tylko za AI.** `resolve_hero_survival` żyje w pętli drivera,
    którą księstwo gracza omija z definicji (gracz ma grać rozkazami, nie
    polityką AI), a ścieżka rozkazów w moście nigdy jej nie woła. Skutek:
    gracz może stracić wszystko i nie przegrać, więc `Wynik:` nie zmienia się
    nigdy. **Wniosek na kierunek:** każda reguła świata, którą wykonuje driver
    za AI, musi mieć swój odpowiednik na ścieżce rozkazów gracza — inaczej
    gracz i AI grają w dwie różne gry. Do sprawdzenia przy kolejnych regułach.

## Klimat, ton, kierunek wizualny
Średniowiecze **bez magii i fantastyki**, surowy i realistyczny ton. **[W]**
Interfejs i teksty po polsku (tak jest w kliencie i tak zostaje). **[P]**

Wizualnie: prosta grafika 2D w Godocie — mapa regionów/osad/party oraz siatka
heksów z jednostkami i terenem. Nie celujemy w AAA ani dźwięk; celem jest
czytelność stanu gry na ekranie. **[W]** dla istnienia obu widoków **oraz dla
tego, że niosą prawdziwe tekstury**; **[P]** dla stylu i doboru paczki.

Kierunek doboru assetów: płaskie, czytelne kafle terenu i sylwetki jednostek w
średniowiecznej, nie-fantastycznej stylistyce (bez smoków, magów, elfów) —
spójna paczka bije zlepek najładniejszych pojedynczych obrazków. **[P]**

## Sugestie autora briefu
- `godot-notes.md` (przykładowe node'y, szkic API, podział scen, kolejność prac)
  jest **niewiążące** — inspiracja, nie specyfikacja.
- Klient HTML/SVG `tbbui` zostaje jako narzędzie diagnostyczne; nie rozwijamy go
  jako produktu (patrz wstrzymany K62).
- Autor prosi też o **posprzątanie repo gry** — sondy testowe wymieszane z kodem
  produkcyjnym w `game/scripts/`, wersjonowane artefakty w `out/`. **[P]**
  *(zrobione: R82.1)*
- **Assety i tekstury przesądzają o tym, czy MVP jest prawdziwe** (feedback
  2026-07-27). Autor nie żąda bogactwa treści — „nie musi być dużo budynków /
  rodzajów jednostek / terenu" — tylko żeby to, co jest, było narysowane
  sensownymi, prawdziwymi assetami. Traktujemy to jako **[W]**, nie sugestię.

## Kolejne prawdopodobne etapy
1. ~~Start bez terminala~~ (K82), ~~czytelny układ ekranu~~ (K83), ~~widok mapy~~
   (K84), ~~widok bitwy~~ (K85) i ~~zapis/odczyt z UI~~ (K86) — **zrobione**.
2. ~~Prawdziwe assety~~ (K87) — **domknięte**: obie paczki CC0 z atrybucją per
   plik, kafle mapy, teren heksów i sylwetki stron rysowane teksturami. Zakres
   został po stronie `game/`: mapa różnicuje właściciela i osadę, teren
   teksturujemy tam, gdzie most go niesie — na polu bitwy (wniosek 8).
3. ~~Pakiet na Linuksa~~ (K88) — **domknięty**, 7 z 7 plasterków, z dowodem
   startu bez terminala na samym pakiecie i wpisem `.desktop`. Bez własnego
   runtime'u Pythona (wniosek 10).
4. **Bitwa zawsze daje wynik** (K89) — kontrakt wyniku i reguła ruchu są w
   rdzeniu; zostają dwa plasterki w kolejce (realne rozstrzygnięcie szturmu z
   repro + e2e na żywym moście).
5. **Partia da się w ogóle rozegrać** (K90) — pierwsza tura nie może odbierać
   gracza z gry (wniosek 15), a przegrana i zwycięstwo muszą być osiągalne i
   widoczne po polsku (wniosek 16). To jest dziś **najkrótsza droga od
   „wszystko widać" do „da się grać"**.
6. **Klik na cel na mapie** zamiast globalnych przycisków „Rozwiń/Szturmuj" —
   czeka na większą mapę (dziś rozkaz celowany daje ten sam skutek co
   automatyczny; patrz nota przy K86 w `BACKLOG.md`).

## Świadomie odłożone
- Scenariuszowa kampania/fabuła, multiplayer, magia, oddziały masowe, grafika
  AAA i dźwięk, edytor map — **poza zakresem** (brief).
- Rozbudowa alertu gospodarczego w HTML (K62) — **wstrzymana**, klient HTML jest
  tylko diagnostyką.
- Bogatszy model ran/terenu/budynków, więcej typów jednostek, balans i strojenie
  AI, pełna maszyna faz `StrategicTurn` — po domknięciu widocznej, grywalnej gry.
  **Uwaga na granicę:** wyrównanie pozycji startowej i osiągalność warunku końca
  gry (K90) **nie** wchodzą w to odłożenie — bez nich nie ma czego balansować
  (wnioski 15 i 16).
- Podział przerośniętych dokumentów (`ARCHITECTURE.md` ~119 KB, `DECISIONS.md`
  ~74 KB, `DESIGN.md` ~28 KB) — dług dokumentacji, nie blokuje celu.
