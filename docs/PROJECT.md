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

**Assety i osiągnięty wygląd są częścią kryterium, nie polishem po MVP.**
Feedback autora briefu
(2026-07-27): *„prawdziwe MVP będzie wtedy, kiedy będą assety i tekstury. Nie
musi być dużo budynków/rodzajów jednostek/terenu itp, ale żeby były jakieś
sensowne prawdziwe assety."* Czyli: widoki mają rysować **realne pliki
graficzne**, nie jednolite prostokąty z etykietą tekstową. Zakres świadomie
mały — po kilka kafli terenu, sylwetek jednostek i budynków — ale prawdziwych.
Od 2026-07-30 K87 jest tylko minimum technicznym: rozwój oprawy trwa do
osiągnięcia jawnego progu jakości i akceptacji człowieka na screenshotach.
**[W]**

Próg jest osiągnięty dopiero, gdy mapa, osady i armie używają spójnych assetów,
bitwa ma czytelne kafle/jednostki/strony, UI nie opiera się na przypadkowych
placeholderach, licencje są kompletne, człowiek akceptuje screenshoty, a
`docs/PROJECT.md` i `BACKLOG.md` jawnie zapisują ten stan. **[W]**

## Stan faktyczny (aktualizowany przy przeglądach)
- Rdzeń `tbb` (Python): kampania, ekonomia (pszenica/złoto, populacja, budynki),
  kalendarz 13×4 tygodnie, jednostki i trzy filary progresji, morale, bitwa na
  heksach, AI księstw, sukcesja — **działa headless, pokryty TDD**.
- Most `tbbbridge`: snapshot JSON (OUT), komendy i rozkazy gracza (IN), protokół
  JSON Lines na stdio, `serve` / `serve --resume`, round-trip persystencji
  (save/load całej sesji łącznie z RNG i `last_battle`) — **gotowe**.
- Klient Godot 4 w `game/`: `SnapshotModel`, trwały przez plik `BridgeClient`,
  oba widoki, statusy oraz komplet bieżących rozkazów gracza.
- **Klient bez terminala, oba widoki, zapis/odczyt** (K82–K86): domyślna
  konfiguracja bez `TBB_*`, układ w kontenerach, `MapView` (kafel na region po
  `col`/`row`), `BattleView` (heksy po `(q, r)`), „Zapisz/Wczytaj partię".
- **Minimum assetów — GOTOWE, próg wizualny — NIEOSIĄGNIĘTY** (K87): jeden
  bazowy heks plus dekoracje drzewa/skały; import Kenney CC0 to tylko minimum.
- **Pakiet Linuksa — DOMKNIĘTY** (K88): x86-64, `.desktop`, `package.sh` i e2e
  startu bez terminala na artefakcie odbiorcy.
- **Pętla partii — DOMKNIĘTA** (K89–K91): bitwa zawsze ma legalny, widoczny
  wynik; symetryczny start prowadzi do zwycięstwa/przegranej; koniec jest trwały.
- **Obrona osady — DOMKNIĘTA** (G92.1): armia w osadzie walczy z garnizonem,
  a zwycięski szturm nie zakleszcza świata.
- **Minimalny wieloosadowy świat — DOMKNIĘTY** (G92.2a): pięć połączonych
  regionów, pusty region graniczny i po dwie osady na stronę są wystawione
  istniejącym snapshotem i rysowane przez `MapView`. Utrata jednej osady nie
  kończy księstwa.
- **Strategiczna kompozycja — DOMKNIĘTA** (K94): pięć stykających się heksów,
  trzy dekoracyjne podłoża, osobne keep/outpost, pergaminowe tło i układ
  mieszczący wszystkie przyciski przy 1152×648.
- **Ikony rozkazów — DOMKNIĘTE** (K95): tura, rozkazy osady i pola oraz
  zapis/odczyt mają odrębne ikony z jednej rodziny Game-icons.
- **Armie na mapie — DOMKNIĘTE** (G96.1a): snapshotowe `region.party.owner`
  wybiera odrębne sylwetki gracza i AI; aktualny komplet armii jest widoczny.
- **Wybór celu — FUNDAMENT GOTOWY, SKUTEK RUCHU W KOLEJCE** (K97): most i
  klient niosą `move(target)`, kafle mają hover/ramkę, panel opisuje cel po
  polsku, a przycisk pokazuje jego nazwę. Task-555…557 domykają legalny krok,
  blokadę wrogiej osady i pozycję po wznowieniu.
- `tbbui` (HTML/SVG) — **wyłącznie narzędzie diagnostyczne**, nie docelowy klient.

**Najbliższa luka do celu: K97 ma wybór, lecz jeszcze nie dowód pełnego ruchu.**
Zaplanowane task-555…557 słusznie kończą tę ścieżkę i nie wymagają
przeplanowania. Po nich `BattleView` wymaga spójności: prostokątny układ
rozciąga drzewo i skałę jak heksy, tintuje teren i nakłada angielskie nazwy.
K98 zbuduje geometrię z bazowego heksu, a drzewo/skałę nałoży jako dekoracje,
bez zmian snapshotu i mechaniki.

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
- **[W] Stała bramka planowania oprawy:** do osiągnięcia progu wizualnego każde
  wywołanie planisty i każdy batch Forge ma co najmniej 4 zadania graficzne,
  najwyżej 2 mechaniczne i najwyżej 6 łącznie. Mechanika jest dopuszczalna
  wyłącznie jako bezpośrednia,
  niezbędna zależność aktualnego efektu graficznego. Brak czterech zadań
  graficznych oznacza dopisanie małych zadań, nigdy `no_more_tasks`.
- **[W]** Zadanie graficzne wskazuje asset/element i miejsce użycia, daje
  widoczny efekt w natywnym Godocie, kończy się screenshotem lub ludzkim review
  i utrzymuje źródła/licencje per plik w `game/assets/CREDITS.md`. Sam test,
  dokumentacja lub refaktor nie liczy się jako grafika.
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
19. **Pięć regionów wystarczyło, by odsłonić brak sterowania, nie defekt
    skalowania.** G92.2a przechodzi testy rdzenia i e2e Godota; na seedzie 73
    naturalna sekwencja zdobywa pierwszą z dwóch osad AI, pokazuje trwającą
    partię i wznawia ją z pliku. Następna wartość leży w wyborze celu na
    istniejącej mapie, nie w dalszym powiększaniu świata.
20. **Istniejące `target` marszu nie jest kontraktem wyboru kafla — i nie wolno
    go na taki kontrakt przepisać.** `march_duchy_party_to` zatrzymuje się obok
    celu, więc odwrót na sąsiedni własny region jest no-opem; to jednak
    utrwalona semantyka marszu ku odległej osadzie, używana przez `tbbui` oraz
    K15.1a/K49.1d. G93.1a dodaje obok niej odrębny prymityw i rozkaz `move`:
    dokładnie jeden krok do wskazanego sąsiada, bez wejścia do wrogiej osady.
    Stary celowany i automatyczny `march` oraz celowane `assault`/`engage`
    zachowują swoje reguły; celowanie rozwoju, rekrutacji i zbiórki pozostaje
    poza tym plasterkiem.
21. **Obecność tekstur nie dowodzi osiągniętego wyglądu.** Screenshot 1152×648
    ujawnił, że K87 zostawił rozłączne kafle, napisy na budynkach, dominującą
    szarą pustkę i sterowanie poza ekranem. Od teraz każdy przyrost oprawy ma
    dowód wizualny; test `Texture2D` pozostaje tylko bramką techniczną.
22. **K94–G96 potwierdziły, że oprawę można poprawiać bez ruszania reguł.**
    Siatka, osady, ikony i sylwetki obu armii wykorzystały istniejący snapshot.
    Kolejna wartość wymaga już wejścia użytkownika, ale reguła bezpiecznego
    kroku istnieje; rozszerzamy tylko najwęższą ścieżkę most→wybór→feedback.
23. **K97 potwierdziło najwęższą ścieżkę celu.** `move(target)`, zaznaczenie,
    hover, panel i przycisk powstały bez zmiany reguł; task-555…557 kończą e2e.
24. **Rolę assetu potwierdza obraz/źródło, nie nazwa.**
    `terrain_plains.png` to heks 120×140, `terrain_forest.png` — drzewo 26×40,
    a `terrain_hills.png` — skała 74×92. Bazowy heks buduje siatkę; pozostałe
    pliki są dekoracjami bez rozciągania.

## Klimat, ton, kierunek wizualny
Średniowiecze **bez magii i fantastyki**, surowy i realistyczny ton. **[W]**
Interfejs i teksty po polsku (tak jest w kliencie i tak zostaje). **[P]**

Wizualnie: spójna grafika 2D w Godocie — mapa regionów/osad/armii oraz siatka
heksów z jednostkami i terenem. Nie celujemy w AAA ani dźwięk; celem jest
czytelna, wyraźnie mniej prototypowa gra o średniowiecznym, realistycznym
charakterze. Oba widoki, prawdziwe tekstury i spójność/czytelność są **[W]**;
konkretna technika i paczka są **[P]**.

Kierunek doboru assetów: czytelne kafle terenu, osady, ikony i sylwetki w
średniowiecznej, nie-fantastycznej stylistyce (bez smoków, magów, elfów).
Realistyczny ton jest ważniejszy niż kreskówkowość; spójna rodzina bije zlepek
ładnych pojedynczych obrazków. Obecne Kenney jest przejściowym minimum
technicznym i może być wymieniane etapami. **[P]**

Obowiązująca kolejność poprawy: (1) spójność/różnorodność kafli mapy,
(2) osady i budynki, (3) tło/kompozycja mapy, (4) ikony rozkazów,
(5) sylwetki i strony, (6) zaznaczenie celu/stan gry, (7) spójność obu widoków.
**[W]**

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
- Zmiana briefu 2026-07-30 ustanawia bezwyjątkową bramkę 4 zadań graficznych
  na batch aż do ludzkiej akceptacji screenshotów. K87 nie kończy rozwoju
  oprawy. **[W]**

## Kolejne prawdopodobne etapy
1. ~~Start bez terminala~~ (K82), ~~czytelny układ ekranu~~ (K83), ~~widok mapy~~
   (K84), ~~widok bitwy~~ (K85) i ~~zapis/odczyt z UI~~ (K86) — **zrobione**.
2. **Techniczne minimum assetów** (K87) — gotowe: obie paczki CC0 z atrybucją
   per plik, kafle mapy, teren heksów i sylwetki stron. Nie jest to zakończenie
   grafiki ani spełnienie progu jakości.
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
7. ~~Minimalny wieloosadowy świat~~ (G92.2a) — **domknięty**: pięć regionów,
   dwie osady na stronę, trwająca partia po utracie pierwszej osady oraz e2e
   naturalnego szturmu na żywym moście.
8. ~~Strategiczna mapa przestaje wyglądać jak prototyp~~ (K94) — **zrobione**:
   siatka, podłoża, keep/outpost oraz tło i kompozycja.
9. ~~Ikony rozkazów~~ (K95) — **zrobione** dla tury, osady, pola i zapisu.
10. ~~Sylwetki obu armii na mapie~~ (G96.1a) — **zrobione** z istniejącego
    `region.party.owner`.
11. **Pierwszy celowany rozkaz z mapy** (K97) — fundament gotowy; task-555…557
    domykają widoczny legalny krok, blokadę i wznowienie.
12. **Spójny widok bitwy** (K98) — cztery zadania graficzne na obecnym
    snapshotcie: bazowy heks + dekoracje, jednostki z PŻ, polski panel wyniku.
13. **Nowa partia z UI po zakończonej grze** — most ma `new_game`, scena nie ma
   przycisku. Po K92 gracz kończy partię regularnie, więc brak restartu zacznie
   boleć. Odłożone do zakończenia priorytetu graficznego.

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
- Do osiągnięcia progu wizualnego: niezależne nowe reguły, AI, ekonomia, walka,
  ruch, rozkazy, protokół/snapshot/most, rdzeń Python, save/load, porządki repo
  i dokumentacja niezwiązana z oprawą. Wyjątek tylko dla niezbędnej zależności
  konkretnego zadania graficznego w granicach batcha.
