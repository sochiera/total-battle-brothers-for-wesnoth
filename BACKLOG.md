# BACKLOG — Total Battle Brothers

> **Kolejka zadań.** Każde zadanie = jeden mały, testowalny przyrost (TDD).
> Statusy: `[ ]` do zrobienia, `[~]` w toku, `[x]` zrobione.
> Bierz zadania z góry. Nie łącz wielu przyrostów w jeden. Aktualizuj status i
> dopisuj nowe zadania, gdy wizja się doprecyzowuje. Detale mechaniki → `docs/DESIGN.md`.

## Legenda
Każde zadanie ma **kryteria akceptacji** (co musi przejść jako test). Rdzeń przed
prezentacją. Determinizm (seedowalny RNG) jest wymogiem przekrojowym.

---

## Kamień milowy 0 — szkielet (bootstrap)
- [x] **B0.1** Szkielet projektu + pytest + jeden trywialny zielony test.
  - AC: `bash scripts/test.sh` przechodzi; `import tbb` działa; `python -m tbb` kończy 0.

## Kamień milowy 1 — fundament rdzenia
- [x] **C1.1** Seedowalny RNG (`tbb/rng.py`).
  - AC: ten sam seed → ta sama sekwencja; `randint`, `chance(p)` deterministyczne;
    dwa RNG z tym samym seedem dają identyczne wyniki, z różnym — różne.
- [x] **C1.2** `Resources` (pszenica, złoto) — dodawanie, odejmowanie, walidacja.
  - AC: nie da się zejść poniżej zera bez jawnej zgody; arytmetyka pokryta testami.
- [x] **C1.3** Współrzędne heksów (`tbb/hex.py`, axial/cube).
  - AC: dystans heksowy, sąsiedzi, konwersje axial↔cube; testy na znanych przypadkach.

## Kamień milowy 2 — osada i ekonomia
- [x] **E2.1** `Settlement` z pulą populacji (wolna vs zajęta).
  - AC: rekrutacja/obsada zajmuje populację; brak wolnej populacji blokuje akcję.
- [x] **E2.2** Budynki: uruchomienie wymaga wolnej populacji; zamknięcie ją zwalnia.
  - AC: za mała populacja → nie można uruchomić kowala; zamknięcie oddaje 1 pop.
- [x] **E2.3** Produkcja surowców per tura (pszenica/złoto z budynków) + konsumpcja.
  - AC: bilans miesięczny liczony deterministycznie; testy na przykładowej osadzie.
- [x] **E2.4a** Wzrost populacji — urodzenia + sufit (`capacity`).
  - AC: najedzona osada (nadwyżka pszenicy) rośnie o 1/turę; sufit blokuje wzrost;
    głodująca nie rośnie; faza wzrostu osobna od `tick_economy` (DESIGN §10 kolejność).
- [x] **E2.4b** Wzrost populacji — imigranci (dopływ zależny od dobrobytu).
  - AC: dobrobyt (nadwyżka złota) przyciąga +1 imigranta/turę do puli wolnej;
    sufit respektowany; głodująca/bez złota nie przyciąga; determinizm; osobne
    przejście `tick_immigration()` w fazie wzrostu (po urodzeniach).

## Kamień milowy 3 — jednostki i progresja
- [x] **U3.1** `Unit` z trzema filarami (trening/uzbrojenie/doświadczenie).
  - AC: statystyki pochodne = funkcja filarów; niezależność filarów pokryta testem.
    Mapowanie liniowe (placeholder, DESIGN §5); krzywe malejącego zysku → U3.2.
- [x] **U3.2** Malejący zysk treningu i uzbrojenia (czas/surowce → poziom filaru).
  - AC: przyrost maleje z poziomem; parametry z DESIGN; monotoniczność w teście.
    Wzór `level(inv) = (isqrt(8·inv+1)−1)//2` (progi trójkątne), deterministyczny.
- [x] **U3.3** Rekrutacja jednostki z populacji osady.
  - AC: rekrutacja zdejmuje pop z puli; brak pop blokuje; jednostka trafia do osady.

## Kamień milowy 4 — bitwa heksowa
- [x] **B4.1** Plansza heksowa + teren z modyfikatorami.
  - AC: pola mają typ terenu; modyfikatory (ruch/obrona/celność) odczytywalne.
    Katalog Plains/Forest/Hills, `Battlefield` z domyślnym terenem (DESIGN §3.2).
- [x] **B4.2a** Rozstawienie jednostek na planszy (deployment, bez ruchu).
  - AC: `HexBattle` trzyma teren + pozycje jednostek (`Hex→Unit`); rozstawienie na
    zajęty heks odrzucone; niemutowalne (deploy zwraca nowy stan); DESIGN §7.
- [x] **B4.2b** Ruch jednostki po punktach ruchu z kosztem terenu.
  - AC: legalne ruchy respektują koszt (`move_cost` terenu) i zasięg; wejście na
    zajęty heks odrzucone; nielegalne ruchy odrzucone; stan wejściowy pozostaje
    niezmieniony; `reachable()` zwraca wolne heksy w budżecie; determinizm.
    Ruch po heksach źródło→cel; koszt = najtańsza ścieżka (`move_cost` wchodzonych
    heksów); inne jednostki blokują; budżet `move_points` jako parametr (DESIGN §7).
- [x] **B4.3a** Walka wręcz: czyste wyliczenie szansy trafienia.
  - AC: wzór z DESIGN §3.2 uwzględnia celność atakującego, obronę celu, teren obu
    jednostek i morale; wynik jest całkowitym procentem ograniczonym do 5–95;
    funkcja nie używa RNG ani nie mutuje stanu.
- [x] **B4.3b1** Stan bieżącego HP jednostek w bitwie.
  - AC: rozstawiona jednostka zaczyna z `current_hp == Unit.hp`; obrażenia zmniejszają
    bieżące HP z podłogą na 0; ruch przenosi HP razem z jednostką; przejścia nie
    mutują stanu wejściowego; błędna pozycja i ujemne obrażenia są odrzucane.
- [x] **B4.3b2** Walka wręcz: strony, sąsiedztwo, rzut na trafienie i obrażenia.
  - AC: atak tylko na sąsiedni zajęty heks wroga; ustalony seed daje ten sam wynik;
    pudło nie zmienia HP, trafienie odejmuje obrażenia; stan wejściowy jest niemutowalny.
- [x] **B4.4a** Minimalny atak dystansowy: profil jednostki, zasięg i obrażenia.
  - AC: jednostka bez zdolności dystansowej nie może strzelać; cel w odległości
    2–`ranged_range` może zostać zaatakowany, a cel bliższy/dalszy jest odrzucony;
    atak wymaga wrogich stron, używa wzoru trafienia z B4.3a i dokładnie jednego
    rzutu RNG; trafienie zadaje `Unit.damage`, pudło nie zmienia HP; brak
    kontrataku; stan wejściowy pozostaje niemutowalny.
- [x] **B4.4b1** Deterministyczna linia heksów dla widoczności.
  - AC: `Hex.line_to()` zwraca oba końce i heksy linii wyznaczone między nimi
    w stabilnej kolejności; kolejne heksy są sąsiadami; odwrócenie końców odwraca
    wynik; testy obejmują linię prostą, ukośną i przypadek przechodzący po granicy.
- [x] **B4.4b2** Jednostki jako przeszkody dla ataku dystansowego.
  - AC: każda jednostka na heksie pośrednim wyznaczonym przez `Hex.line_to()`
    blokuje strzał; testy obejmują czystą i zablokowaną linię axial; sprawdzenie
    następuje przed rzutem RNG i nie zmienia stanu bitwy.
- [x] **B4.5a** Minimalny model ran czasowych i trwałych.
  - AC: niemutowalna rana określa kary do celności/obrony i czas trwania
    (`None` = trwała); `Unit` przechowuje rany, a efektywne statystyki uwzględniają
    ich sumę z podłogą na zero; katalog zawiera po jednej ranie czasowej i trwałej.
- [x] **B4.5b** Rozstrzygnięcie jednostki z 0 HP: śmierć albo ogłuszenie + rana.
  - AC: dokładnie jeden deterministyczny przy ustalonym RNG rzut 50/50 usuwa
    martwą jednostkę albo pozostawia ją ogłuszoną z `BRUISE`; rozstrzygać można
    tylko nierozstrzygniętą jednostkę z 0 HP; ogłuszona jednostka nie może działać;
    stan wejściowy pozostaje niemutowalny (DESIGN §3.2 i §7).
- [x] **B4.6a** Warunek końca bitwy i zwycięska strona.
  - AC: aktywna jednostka ma HP > 0 i nie jest ogłuszona; przy aktywnych obu
    stron bitwa trwa, przy aktywnej jednej stronie wygrywa ta strona, a przy braku
    aktywnych jednostek wynik jest remisem; zapytanie nie mutuje stanu.
- [x] **B4.6b** Raport wyniku bitwy: polegli, ogłuszeni i zdolni do działania.
  - AC: wynik zachowuje przynależność pokonanych jednostek i raportuje straty obu
    stron deterministycznie, także gdy martwa jednostka zniknęła z rozstawienia.
- [x] **B4.6c** Doświadczenie za udział w rozstrzygniętej bitwie.
  - AC: ocalałe jednostki dostają deterministyczny przyrost doświadczenia dopiero
    po końcu bitwy; aktywni i ogłuszeni dostają +1, polegli nie dostają nagrody;
    stan wejściowy pozostaje niemutowalny; zasady z DESIGN.

## Kamień milowy 5 — mapa strategiczna i tura
- [x] **M5.1a** `WorldMap`: niemutowalny graf regionów i rozmieszczenie osad.
  - AC: jawne regiony i dwukierunkowe połączenia; deterministyczne zapytanie
    o sąsiadów; najwyżej jedna osada w regionie; odrzucenie połączeń i osad spoza
    mapy; wejściowe kolekcje nie pozwalają zmutować utworzonej mapy.
- [x] **M5.2a** Party (bohater + ≤12 jednostek), bez mapy i ruchu.
  - AC: dokładnie jeden bohater; limit 12 jednostek; utworzenie party bez bohatera
    lub ponad limitem jest odrzucane; garnizon osady pozostaje odrębnym stanem.
- [x] **M5.1b** Pozycje party na `WorldMap` (po utworzeniu modelu `Party` w M5.2a).
  - AC: najwyżej jedno party na region; `party_at(region)` zwraca obsadę albo
    `None`; początkowe rozmieszczenie jest kopiowane i niemutowalne;
    `place_party()` tworzy nową mapę, a pozycjonowanie poza mapą i kolizja
    party są odrzucane. Party może współdzielić region z osadą.
- [x] **M5.2b** Ruch party między sąsiednimi regionami z punktami ruchu.
  - AC: `move_party(source, destination, move_points)` przenosi całe party wyłącznie
    po jednym istniejącym połączeniu, którego koszt wynosi 1 punkt; wymaga budżetu
    `>= 1` i wolnego celu; region niesąsiedni, cel zajęty i brak party w źródle są
    odrzucane; mapa wejściowa oraz garnizon osady pozostają niezmienione.
- [x] **M5.3a** Kontakt dwóch party tworzy minimalną bitwę heksową.
  - AC: jawne rozpoczęcie starcia wymaga dwóch party w sąsiednich regionach;
    bohater i podkomendni strony atakującej/broniącej trafiają na właściwe
    strony `HexBattle` w deterministycznym rozstawieniu; mapa świata pozostaje
    niezmieniona; brak party, ten sam/niesąsiedni region są odrzucane.
- [x] **M5.3b1** Kontakt party z garnizonem osady tworzy minimalną bitwę.
  - AC: jawne rozpoczęcie starcia wymaga party w regionie sąsiadującym z osadą;
    bohater i podkomendni party trafiają do `HexBattle` jako atakujący, a garnizon
    osady jako obrońcy, w deterministycznym rozstawieniu; mapa, party, osada
    i garnizon pozostają niezmienione; błędny kontakt jest odrzucany.
- [x] **M5.3b2** Własność strategiczna ogranicza kontakt do wrogich celów.
  - AC: party i osada przechowują opcjonalny, niepusty `owner_id`; rozpoczęcie
    bitwy wymaga jawnego właściciela obu stron i różnych identyfikatorów;
    kontakt z własną osadą/party oraz brak właściciela nie tworzą bitwy, a kontakt
    z wrogim celem zachowuje reguły rozstawienia z M5.3a–b1 i niemutowalność.
- [x] **M5.4a** Kalendarz strategiczny: 1 tura = 1 miesiąc, 13 miesięcy po 4 tygodnie.
  - AC: niemutowalny kalendarz startuje w roku 1, miesiącu 1; przejście tury
    zwiększa miesiąc o 1, po miesiącu 13 przechodzi do miesiąca 1 następnego roku;
    liczba upływających tygodni wynosi zawsze 4; stan wejściowy pozostaje bez zmian.
- [x] **M5.4b** Miesięczne przejście osad: produkcja → urodzenia → imigracja.
  - AC: wszystkie osady mapy przechodzą fazy w tej kolejności; wynik fazy jest
    wejściem następnej; mapa i osady wejściowe pozostają niezmienione.
- [x] **M5.4c1** Maszyna faz strategicznej tury: osady → ruch → bitwy → zakończona.
  - AC: niemutowalny stan tury trzyma mapę, kalendarz i jawną fazę; `advance_phase()`
    przechodzi fazy w tej kolejności; wejście do fazy ruchu wykonuje dokładnie jedno
    `WorldMap.tick_settlements()`; kalendarz przesuwa się o jeden miesiąc dopiero przy
    zakończeniu fazy bitew; przejście poza fazę zakończoną jest odrzucane; stan
    wejściowy pozostaje niezmieniony (DESIGN §10, plan M5.4c).
- [x] **M5.4c2** Bramkowanie akcji tury fazą (ruch i rozpoczęcie bitew).
  - AC: ruch party dostępny tylko w fazie ruchu, a rozpoczęcie bitew party↔party
    i party↔osada tylko w fazie bitew; akcje delegują do istniejących przejść mapy
    i zwracają nowy stan tury; akcja poza właściwą fazą jest odrzucana.

## Kamień milowy 6 — księstwa, następstwo, warunki gry
- [x] **D6.1a** `Duchy` minimalny: identyfikator + jeden bohater + morale.
  - AC: niemutowalny `Duchy` z niepustym `duchy_id` (= `owner_id` party/osad na
    mapie), dokładnie jednym wymaganym `hero: Unit` (inwariant 1 bohatera) oraz
    podpisanym `morale: int` (domyślnie 0); pusty/nietekstowy identyfikator i
    nie-`Unit` bohater są odrzucane; dziedzic, osady i party dochodzą w D6.1b.
- [x] **D6.1b1** `Duchy`: wyznaczony dziedzic (opcjonalny `heir`).
  - AC: niemutowalny `Duchy` trzyma opcjonalny `heir: Unit | None` (domyślnie
    `None` = brak dziedzica); podany dziedzic musi być `Unit` i nie może być tym
    samym obiektem co `hero`; brak dziedzica jest dozwolony; sukcesja i kara
    morale po śmierci bohatera dochodzą w D6.2.
- [x] **D6.1b2** `Duchy`: lista osad i party (spięcie z mapą).
  - AC: księstwo trzyma odwołania do swoich osad i party; własność spójna
    z `duchy_id` (`owner_id` każdej osady/party = `duchy_id`); niemutowalne
    kolekcje kopiowane przy tworzeniu; osada/party bez `owner_id` lub z innym
    `owner_id` jest odrzucana; niepoprawny typ członka odrzucany; puste kolekcje
    są dozwolone i domyślne.
- [x] **D6.2a** Śmierć bohatera z dziedzicem → sukcesja + kara morale.
  - AC: czyste przejście `Duchy.succeed()` wymaga wyznaczonego dziedzica; przy
    obecnym dziedzicu zwraca nowe księstwo, w którym dawny `heir` staje się `hero`,
    `heir` wraca do `None`, a `morale` spada o stałą karę sukcesji (DESIGN §7);
    `duchy_id`, osady i party pozostają bez zmian; wywołanie bez dziedzica jest
    odrzucane (wariant bez dziedzica → D6.2b/D6.3); stan wejściowy niemutowalny.
- [x] **D6.2b** Śmierć bohatera bez dziedzica → księstwo bez bohatera (sygnał).
  - AC: `hero` staje się `Unit | None`; księstwo bezhetmańskie (`hero=None`) to
    dozwolony stan przejściowy z jawnym sygnałem `has_hero`. `succeed()` bez
    dziedzica nie rzuca — zwraca nowe księstwo z `hero=None`, `heir=None`, karą
    `SUCCESSION_MORALE_PENALTY` na morale, zachowanym `duchy_id`/osadami/party;
    stan wejściowy niemutowalny. Konstruktor odrzuca dziedzica przy `hero=None`.
    Warunek przegranej (brak osad ORAZ bohatera) rozstrzyga D6.3.
- [x] **D6.3a** Predykat porażki księstwa (`Duchy.is_defeated`: brak osad ORAZ brak bohatera).
  - AC: `is_defeated` jest `True` dokładnie gdy księstwo nie ma bohatera
    (`has_hero is False`) **i** nie ma żadnej osady (`settlements == ()`); we
    wszystkich innych układach (jest bohater, jest osada, lub oba) jest `False`;
    party nie wpływają na predykat (bez bohatera i tak nie walczą); zapytanie
    nie mutuje stanu (DESIGN §3.1, §7).
- [x] **D6.3b** Rozstrzygnięcie wygranej/przegranej między księstwami (stan gry).
  - AC: nad zbiorem księstw gra sygnalizuje koniec dokładnie gdy pokonane są
    wszystkie księstwa poza jednym (`is_defeated`), a to jedno wygrywa; póki
    stoją co najmniej dwa niepokonane księstwa, gra trwa; determinizm.
    Niemutowalny `GameState(duchies)` z czystymi zapytaniami `contenders` /
    `is_over` / `winner`; wszyscy pretendenci = księstwa z `is_defeated == False`;
    `is_over` gdy pretendentów ≤ 1; `winner` = jedyny pretendent albo `None`
    (≥2 pretendentów: gra trwa; 0 pretendentów: koniec bez zwycięzcy). `duchy_id`
    księstw muszą być różne. Zapytania nie mutują stanu.

## Kamień milowy 6.5 — automatyczne rozegranie bitwy (driver)
> Bitwa ma już wszystkie prymitywy (ruch, walka wręcz/dystans, rozstrzygnięcie 0 HP,
> koniec/raport), ale nic nie rozgrywa jej do końca. Driver domyka ten szew i jest
> warunkiem koniecznym AI (A7.1) i pętli MVP (A7.2). Dzielimy go na małe kroki.
- [x] **BD.1** Wybór najbliższego wrogiego celu w bitwie (`HexBattle.nearest_enemy`).
  - AC: czyste zapytanie zwraca pozycję najbliższej **aktywnej** (HP>0, nieogłuszonej)
    jednostki po przeciwnej stronie względem jednostki na danym heksie; dystans wg
    `Hex.distance`, remis rozstrzygany deterministycznie kolejnością rozstawienia;
    brak wrogów → `None`; pusty heks źródłowy odrzucony; zapytanie nie mutuje stanu
    i nie używa RNG.
- [x] **BD.2** Tura pojedynczej jednostki: podejście do najbliższego wroga + atak wręcz.
  - AC: jednostka rusza się najtańszą ścieżką w budżecie ku sąsiedztwu celu z BD.1,
    a jeśli już sąsiaduje — wykonuje `melee_attack`; przy 0 HP celu rozstrzyga
    `resolve_defeat`; jeden rzut RNG na atak; determinizm; niemutowalność wejścia.
- [x] **BD.3** Pełna auto-rozgrywka bitwy do rozstrzygnięcia (`HexBattle.auto_resolve`).
  - AC: deterministyczna pętla tur (kolejność rozstawienia) doprowadza bitwę do
    `result` innego niż `None` przy ustalonym seedzie; zwraca końcowy stan/raport;
    limit tur chroni przed zapętleniem; niemutowalność wejścia.

## Kamień milowy 6.6 — skutki bitwy na mapie strategicznej
> Bitwa rozgrywa się do końca (BD.3), ale jej wynik nie wraca na `WorldMap`:
> zwycięzca nie zajmuje regionu, przegrany nie znika. Bez tego podbój jest niemożliwy
> i partia nie może się rozstrzygnąć — to twardy warunek pętli MVP (A7.2). Dzielimy
> zapis wyniku na małe kroki (party↔party, potem party↔osada).
- [x] **BW.1** Zapis wyniku bitwy party↔party na mapę (`WorldMap.apply_party_battle_result`).
  - AC: czyste przejście przyjmuje regiony atakującego (`source`) i broniącego
    (`destination`) oraz `BattleResult` i zwraca nową `WorldMap`. `ATTACKER_WIN`:
    party broniące znika, party atakujące przechodzi z `source` do `destination`.
    `DEFENDER_WIN`: party atakujące znika z `source`, broniące zostaje. `DRAW`:
    znikają oba party. Walidacja jak w `start_battle` (regiony na mapie, różne,
    sąsiednie, oba mają party); mapa i osady wejściowe pozostają niezmienione;
    determinizm. Rekonstrukcja ocalałych (straty/rany/doświadczenie) do party jest
    świadomie odłożona — party przenosi się jako placeholder bez zmian składu (BW.3).
- [x] **BW.2** Zapis wyniku bitwy party↔osada na mapę (`WorldMap.apply_settlement_battle_result`).
  - AC: czyste przejście przyjmuje regiony party (`source`) i osady (`destination`)
    oraz `BattleResult`, zwraca nową `WorldMap`; walidacja jak w
    `start_settlement_battle` (regiony na mapie, różne, sąsiednie, `source` z party,
    `destination` z osadą). `ATTACKER_WIN`: osada zmienia `owner_id` na `owner_id`
    party atakującej, a party przechodzi z `source` do `destination` (zajęty przez
    inne party `destination` jest odrzucany). `DEFENDER_WIN`: party atakujące znika
    z `source`, osada bez zmian. `DRAW`: party atakujące znika z `source`, osada bez
    zmian. Mapa, osady i garnizony wejściowe niezmienione; determinizm. Rekonstrukcja
    ocalałych i strat garnizonu świadomie odłożona do BW.3.
> **BW.3 — rekonstrukcja ocalałych.** Rozbite na małe kroki: najpierw uporządkowana
> kwerenda ocalałych strony (klocek), potem czyste odtworzenie składu party z zachowaniem
> bohatera, na końcu wpięcie w `apply_*_battle_result` na mapie.
- [x] **BW.3a** Uporządkowana kwerenda ocalałych strony bitwy (`HexBattle.side_survivors`).
  - AC: czyste zapytanie (bez RNG, bez mutacji) zwraca jednostki danej strony, które
    **pozostały na planszy** (aktywne + ogłuszone; polegli usunięci), w **kolejności
    rozstawienia** (`_deployment_order`) — aktywni i ogłuszeni **przeplatani** wg
    kolejności, nie grupowani; strona przeciwna pominięta; brak ocalałych → pusta krotka;
    stan bitwy pozostaje niezmieniony. Dzięki kolejności rozstawienia slot 0 strony to
    bohater, co domknie identyfikację bohatera w BW.3b.
- [x] **BW.3b** Czyste odtworzenie składu party z ocalałych (`Party.reconstruct`/helper).
  - AC: z party sprzed bitwy i uporządkowanych ocalałych jego strony powstaje nowe party
    tylko z ocalałych (bohater = ocalały ze slotu 0 rozstawienia, reszta jako `units`
    z zachowaną kolejnością); polegli usunięci; rany/doświadczenie z ocalałych zachowane;
    padnięcie bohatera (brak ocalałego w slocie 0) świadomie odłożone/odrzucone tu.
- [ ] **BW.3c** Wpięcie rekonstrukcji w `apply_party_battle_result` / `apply_settlement_battle_result`.
  - AC: przenoszone/pozostające party na mapie po bitwie zawiera tylko ocalałych
    z zachowanymi ranami/doświadczeniem; polegli usunięci (zastępuje placeholder z BW.1/BW.2).

## Kamień milowy 7 — AI i grywalna pętla MVP
- [ ] **A7.1** Proste AI księstwa (rozwijaj osadę → zbierz party → atakuj).
  - AC: AI wykonuje sensowną turę deterministycznie przy ustalonym seedzie.
- [ ] **A7.2** Headless przebieg całej pętli MVP (setup → tury → bitwa → wynik).
  - AC: `run.sh` symuluje partię do rozstrzygnięcia i wypisuje wynik; test smoke pętli.

## Później (poza MVP)
- [ ] Prezentacja/UI (pygame lub most do innego silnika) nad rdzeniem.
- [ ] Bogatszy model ran, terenu, budynków; więcej typów jednostek.
- [ ] Balans ekonomii i krzywych progresji; strojenie AI.
