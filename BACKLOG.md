# BACKLOG — Total Battle Brothers

> **Kolejka zadań.** Każde zadanie = jeden mały, testowalny przyrost (TDD).
> Statusy: `[ ]` do zrobienia, `[~]` w toku, `[x]` zrobione.
> Bierz zadania z góry. Nie łącz wielu przyrostów w jeden. Aktualizuj status i
> dopisuj nowe zadania, gdy wizja się doprecyzowuje. Detale mechaniki → `docs/DESIGN.md`.
> Ukończone milestony przeniesione do `BACKLOG-ARCHIVE.md` (kamienie 0–8 oraz
> A7.1*/A7.2*) — tu zostaje wyłącznie żywy tail w stronę grywalnego MVP.

## Legenda
Każde zadanie ma **kryteria akceptacji** (co musi przejść jako test). Rdzeń przed
prezentacją. Determinizm (seedowalny RNG) jest wymogiem przekrojowym.

---

## Kamienie 7–8 — UKOŃCZONE (headless pętla MVP + ekonomia/kalendarz w driverze)
> `python -m tbb` uruchamia pełną, deterministyczną partię end-to-end: żywa
> miesięczna ekonomia i wzrost osad, płynący kalendarz, wypisany zwycięzca/remis
> wraz z końcową datą (kod wyjścia 0). Wszystkie pozycje w `BACKLOG-ARCHIVE.md`.
> To domyka **minimalną** pętlę z DESIGN §6 pkt 1,3,4,5. Otwarty zostaje pkt 2:
> jednostki są rekrutowane z filarami 0 i nigdy się nie „trenują ani wyposażają"
> — to domyka Kamień milowy 9.

## Kamień milowy 9 — rozwój jednostek w turze — UKOŃCZONE
> Krzywa malejącego zysku (U3.2) wpięta w `Unit` i miesięczne przejście osady:
> garnizon obserwowalnie mocnieje (trening = czas; uzbrojenie = złoto + kuźnia)
> w realnej headless partii. Wszystkie pozycje w `BACKLOG-ARCHIVE.md`.

## Kamień milowy 10 — realne straty i koszty w pętli strategicznej
> Headless pętla MVP działa end-to-end, ale trzy placeholdery czynią warstwę
> strategiczną płytką: (a) garnizon osady **nigdy nie ponosi strat** — po obronie
> zostaje pełny, a po podboju obrońcy zostają garnizonem zdobywcy (BW.3c/BM.2
> świadomie odłożone); (b) rekrutacja jest **darmowa** poza 1 populacją, więc AI
> spamuje żołnierzy bez związku z ekonomią (§7 „koszt … dochodzi później");
> (c) AI **nigdy nie otwiera budynków**, więc ekonomia jest statyczna, a uzbrojenie
> garnizonu (wymaga kuźni) w realnej partii nie postępuje. Ten kamień domyka te
> trzy luki, spinając straty, koszt rekrutacji i rozwój ekonomii AI z pętlą.
> Strojenie wartości (balans) pozostaje poza kamieniem.
- [x] **G10.1** Osada wchłania ocalałych obrońców po bitwie. *(task-022)* →
      `BACKLOG-ARCHIVE.md`
- [ ] **G10.2a** Straty garnizonu obrońcy przy `DEFENDER_WIN`/`DRAW`. *(task-027)*
  - AC: przy podanym `battle` i wyniku obronnym garnizon `destination` =
    `battle.side_survivors(DEFENDER)` (traci poległych), `owner_id` bez zmian;
    `battle is None` zachowuje zgodność wsteczną; walidacja bez zmian; niemutowalne.
  - Uwaga: rozbicie G10.2 po porażce 12-cyklowej (`.forge/failures.md`).
- [ ] **G10.2b** Garnizon zdobytej osady przy `ATTACKER_WIN`. *(task-028)*
  - AC: przy podanym `battle` i podboju `destination` zmienia `owner_id` na
    atakującego **i** garnizon = `battle.side_survivors(DEFENDER)`; party wchodzi
    jak w BW.3c; `battle is None` zachowuje zgodność wsteczną; niemutowalne.
- [ ] **G10.3** Koszt złota rekrutacji. *(task-029)*
  - AC: `Settlement.recruit()` pobiera `RECRUIT_GOLD_COST` ze `storage`; brak złota
    → `ValueError` (blokada, jak przy braku populacji); AI `recruit_duchy_unit`
    pomija osady bez dość złota; niemutowalne, deterministyczne.
- [ ] **G10.4** Polityka AI: otwieranie budynków ekonomii/kuźni. *(task-030)*
  - AC: czyste `ai.develop_duchy_settlement(world, duchy)` otwiera pierwszy brakujący
    korzystny budynek (priorytet `Farm` → `Smith` → `Market`) w pierwszej wg
    kolejności regionów własnej osadzie z dość wolną populacją; brak kandydata =
    no-op; niemutowalne, bez RNG.
- [ ] **G10.5** Wpięcie rozwoju budynków w turę AI + integracja. *(task-031)*
  - AC: `take_duchy_turn` wywołuje `develop_duchy_settlement` przed rekrutacją;
    test drivera pokazuje, że w realnej partii AI otwiera `Farm` (ekonomia
    samowystarczalna) i `Smith` (uzbrojenie garnizonu postępuje); determinizm
    end-to-end; cały pakiet testów zielony.

## Później (poza MVP)
- [ ] Prezentacja/UI (pygame lub most do innego silnika) nad rdzeniem.
- [ ] Bogatszy model ran, terenu, budynków; więcej typów jednostek.
- [ ] **Bramkowanie treningu budynkiem (§5 „odpowiednie budynki"):** katalog
      budynku treningowego i wymóg jego czynności w `tick_training` (dziś trening
      jest bezwarunkową funkcją czasu). Analogicznie polityka AI otwierania
      kuźni/budynków treningowych.
- [ ] Balans ekonomii, tempa rozwoju jednostek i krzywych progresji; strojenie AI.
- [ ] Pełna maszyna faz `StrategicTurn` w headless driverze (routing akcji AI przez
      fazy ruch/bitwy zamiast bezpośredniego `take_duchy_turn`). M8 reużywa tylko
      prymitywów `tick_settlements`/`end_turn`, bez wciągania phase-gatingu.
