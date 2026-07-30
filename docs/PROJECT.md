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
- **Klient bez terminala, oba widoki, zapis/odczyt** (K82–K86): domyślna
  konfiguracja bez `TBB_*`, układ w kontenerach, `MapView` (kafel na region po
  `col`/`row`), `BattleView` (heksy po `(q, r)`), „Zapisz/Wczytaj partię".
- **Prawdziwe assety — DOMKNIĘTE** (K87): 10 plików PNG z dwóch paczek CC0
  (Kenney Hexagon Pack — kafle; Kenney „RTS Pack: Medieval" — sylwetki stron),
  atrybucja **per plik** w `CREDITS.md`, `.godot/` poza gitem.
- **Pakiet na Linuksa — DOMKNIĘTY** (K88, 7 z 7): preset „Linux/X11" x86-64,
  `src/` mostu rozwiązywane odpornie na eksport, `scripts/package.sh`, `.pck`
  bez sond, wpis `.desktop` i **e2e startu bez terminala na samym pakiecie** —
  formalne kryterium „natywna aplikacja bez terminala" odhaczone.
- **Bitwa zawsze daje wynik — DOMKNIĘTE** (K89): bitwa nierozstrzygnięta jest
  legalnym wynikiem rdzenia, most niesie własny `outcome`, scena mówi „szturm
  nierozstrzygnięty" ze stratami, a jednostka omija własnego ogłuszonego.
- **Partia da się rozegrać — DOMKNIĘTE** (K90): symetryczny start, los bohatera
  gracza rozstrzygany tą samą regułą co u AI, `is_over` osiągalne, wynik po
  polsku i wyróżniony na ekranie.
- **Naturalne ruchy i koniec partii — DOMKNIĘTE** (K91): rekrut wzmacnia
  obronę, zwycięstwo jest widoczne i trwałe, a dalsze kliknięcia po końcu gry
  dostają jednoznaczny polski komunikat.
- **Obrona osady — DOMKNIĘTA** (G92.1): oddział stojący w regionie osady walczy
  z garnizonem, ocalali wracają do właściwych składów, zwycięski szturm nie
  zakleszcza świata, a e2e na żywym moście przechodzi dwie kolejne tury.
- `tbbui` (HTML/SVG) — **wyłącznie narzędzie diagnostyczne**, nie docelowy klient.

**Najbliższa luka do celu: świat startowy jest za mały na sandbox.**
`create_headless_game` daje **jedną osadę na stronę** i po jednym oddziale
garnizonu, a `Duchy.is_defeated` to „brak osad **i** brak oddziałów"
(`duchy.py:72-74`). Pierwsza przegrana bitwa kończy księstwo; nie ma drugiej
osady, odwrotu ani odbudowy, więc zarządzanie i ekonomia nie zdążą nabrać
znaczenia. Naprawa obrony usunęła wcześniejszą blokadę skalowania. Następny
plasterek K92.2a daje po dwie osady w minimalnym świecie pięciu regionów i
wystawia go istniejącym widokiem mapy; dopiero potem mierzymy pełną sekwencję
gracza i wybieramy kolejną realną blokadę.

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
*(Wnioski 1–12 pochodzą z domkniętych kamieni K82–K88 i są tu w formie
skróconej; pełne uzasadnienia w `docs/DECISIONS.md` i w `BACKLOG.md`.)*
1. K75–K81 to była seria „kolejny przycisk rozkazu" — ścieżka rozkazu jest
   sparametryzowana, więc kolejny przycisk nie zbliża do celu.
2. Godot 4.2.2 nie ma `OS.execute_with_pipe`: most wołamy jedno-strzałowo, a
   ciągłość partii daje plik stanu (`serve --resume`). Zadziałało, zostaje.
3. Odchudzanie kontraktu (jedno pole na zadanie) ratuje mikro-TDD tam, gdzie
   „cały słownik naraz" wykładał kodera.
4. **Dowód „działa" jest ważny tylko dla tego artefaktu, na którym go
   zrobiono.** Po eksporcie `res://` wskazuje wnętrze PCK, więc start bez
   terminala (K82) trzeba było udowodnić drugi raz — już na pakiecie (G88.1b,
   G88.1f).
5. Snapshot bitwy (`battle.hexes`) niesie **tylko heksy zajęte przez
   jednostki**, bez wymiarów pola i terenu pustych heksów; pełna siatka to
   osobna, późniejsza zmiana mostu.
6. **Kolorowy prostokąt wystarczył na „widać stan gry", ale nie na MVP.**
   K84/K85 dały geometrię, K87 nośnik; podmiana nośnika nie ruszyła ani
   geometrii, ani testów rozmieszczenia.
7. **Prerekwizyt toolchainu idzie w osobną bramkę, przed treścią** (import
   tekstur G87.1a, eksport binarium G88.1a) — potem reszta plasterków szła bez
   niespodzianek. Wzorzec zostaje.
8. **Teren istnieje tylko w warstwie bitwy — mapa strategiczna go nie zna.**
   `tbb.world.Region` ma samo `name`, więc `map_state` daje `name`, `col`,
   `row`, `owner`, `settlement`, `party`, a kafle mapy teksturujemy po
   właścicielu i obecności osady. Teren regionu to **osobna zmiana rdzenia i
   mostu**; klientowi nie wolno wymyślić go u siebie.
9. Warianty kafla robimy **teksturą + `modulate`** zamiast osobnego pliku na
   wariant — mała paczka wystarcza, a testy geometrii zostają w mocy.
10. **Pakiet nie wnosi własnego Pythona** — odbiorca ma systemowy `python3`
    (zweryfikowane: 3.14.4), a jego brak daje czytelny komunikat w scenie.
    Decyzja zakresowa, nie techniczna; jeśli okaże się za wąska, wraca jako
    osobny plasterek.
11. **Bramka „plik się ładuje" nie sprawdza, *co* jest na obrazku** — G87.1a
    wpuściło dwa budynki jako „sylwetki stron". Każdy plasterek assetowy wiąże
    plik z jego *źródłem* w `CREDITS.md` (konkretna ścieżka w paczce) i z
    maszynowo sprawdzalnym kształtem, a człowiek ogląda obrazek przy review.
    Szczególny przypadek wniosku 13.
12. **Jedna paczka nie wystarczy — świadome odstępstwo od [P]:** Hexagon Pack
    nie ma postaci, więc sylwetki przyszły z RTS Packa: Medieval, a strony
    rozróżnia **para różnych plików**, nie tint (zaszarza pokolorowaną figurkę).
13. **Zielony zestaw testów nie dowodzi grywalności.** Każdy przegląd i
    plasterek domykający kamień kończymy pełną sekwencją gracza na żywym moście,
    a po K88 także na pakiecie, który dostaje odbiorca.
14. **Legalny wynik bitwy nie może docierać jako błąd rozkazu.** K89 domknął
    kontrakt wyniku przed zmianą ruchu; ten wzorzec rozdzielania kontraktu od
    reguły zostaje.
15. **Pozycja startowa jest regułą gry, nie odłożonym balansem.** Symetryczny
    start K90 był warunkiem rozpoczęcia pętli sandboxa.
16. **Gracz i AI muszą przechodzić przez te same reguły świata.** K90/K91
    ujednoliciły los bohatera i synchronizację po akcji; sprawdzamy ten warunek
    przy każdej kolejnej regule wykonywanej przez driver.
17. **Jedna osada na stronę jest za mała na opisany sandbox.** Pierwsza
    przegrana bitwa kończy księstwo, zanim ekonomia i decyzje nabiorą znaczenia.
    Następny krok to minimalne dwie osady na stronę w pięciu regionach, nie
    duża mapa ani strojenie liczb.
18. **Obrona osady była blokadą skalowania; G92.1 ją usunęło.** Oddział w
    regionie osady walczy po stronie jej garnizonu, ocalali zachowują
    pochodzenie, a sekwencja `muster` → dwie tury przechodzi na żywym moście.
    Skrajny stan z oddziałem niebędącym obrońcą pozostaje odłożony, dopóki nie
    pojawi się trzecie księstwo lub reprodukcja w normalnej partii.

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
4. ~~Bitwa zawsze daje wynik~~ (K89) i ~~partia da się rozegrać~~ (K90) —
   **domknięte**: szturm zawsze kończy się widocznym skutkiem, a zwycięstwo i
   przegrana są osiągalne i czytelne po polsku.
5. ~~Naturalne ruchy i koniec partii~~ (K91) — **domknięte**: rekrut wzmacnia,
   zwycięstwo jest widoczne i trwałe, a koniec gry ma jednoznaczny komunikat.
6. ~~Obrona własnej osady~~ (G92.1) — **domknięta** w rdzeniu i e2e na żywym
   moście; wcześniejsze zakleszczenie nie blokuje już skalowania świata.
7. **Minimalny wieloosadowy świat** (G92.2a) — pięć regionów i dwie osady na
   stronę, widoczne przez istniejący snapshot i `MapView`. Po tym plasterku
   mierzymy pełną sekwencję gracza i planujemy tylko ujawnioną blokadę.
8. **Klik na cel na mapie** zamiast globalnych przycisków „Rozwiń/Szturmuj" —
   odblokowuje się dopiero po K92: przy pięciu regionach i dwóch osadach na
   stronę rozkaz celowany **przestaje** dawać ten sam skutek co automatyczny
   (dziś daje — patrz nota przy K86 w `BACKLOG.md`).
9. **Nowa partia z UI po zakończonej grze** — most ma `new_game`, scena nie ma
   przycisku. Po K92 gracz kończy partię regularnie, więc brak restartu zacznie
   boleć. Cienki plasterek, nieplanowany jeszcze.

## Świadomie odłożone
- Scenariuszowa kampania/fabuła, multiplayer, magia, oddziały masowe, grafika
  AAA i dźwięk, edytor map — **poza zakresem** (brief).
- Rozbudowa alertu gospodarczego w HTML (K62) — **wstrzymana**, klient HTML jest
  tylko diagnostyką.
- Bogatszy model ran/terenu/budynków, więcej typów jednostek, balans i strojenie
  AI, pełna maszyna faz `StrategicTurn` — po domknięciu widocznej, grywalnej gry.
  **Uwaga na granicę:** minimalna skala świata K92.2 nie jest balansem; bez niej
  nie ma czego stroić.
- Obsługa szturmu na osadę zajętą przez oddział niebędący jej obrońcą (G92.1c)
  — wraca wraz z trzecim księstwem albo reprodukcją w normalnej partii.
- Podział przerośniętych dokumentów (`ARCHITECTURE.md` ~119 KB, `DECISIONS.md`
  ~74 KB, `DESIGN.md` ~28 KB) — dług dokumentacji, nie blokuje celu.
