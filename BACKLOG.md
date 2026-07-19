# BACKLOG — Total Battle Brothers

> **Kolejka zadań.** Każde zadanie = jeden mały, testowalny przyrost (TDD).
> Statusy: `[ ]` do zrobienia, `[~]` w toku, `[x]` zrobione.
> Bierz zadania z góry. Nie łącz wielu przyrostów w jeden. Aktualizuj status i
> dopisuj nowe zadania, gdy wizja się doprecyzowuje. Detale mechaniki → `docs/DESIGN.md`.
> Ukończone milestony przeniesione do `BACKLOG-ARCHIVE.md` (kamienie 0–6.8 oraz
> A7.1*/A7.2a) — tu zostaje wyłącznie żywy tail w stronę grywalnego MVP.

## Legenda
Każde zadanie ma **kryteria akceptacji** (co musi przejść jako test). Rdzeń przed
prezentacją. Determinizm (seedowalny RNG) jest wymogiem przekrojowym.

---

## Kamień milowy 7 — grywalna pętla MVP (headless przebieg A7.2b)
> Rdzeń, AI księstwa i deterministyczny setup (`A7.2a`) są gotowe. Zostaje spiąć je
> w headless partię end-to-end: synchronizacja stanu gry z mapą, rozpoznanie śmierci
> bohatera, pętla tur do rozstrzygnięcia i wypisanie wyniku. To domyka MVP z DESIGN §6.
- [x] **A7.2b1** Synchronizacja kolekcji księstw z mapą świata.
  - AC: czyste przejście `GameState.sync_from_world(world)` zwraca nowy stan gry,
    w którym `settlements` i `parties` każdego księstwa zawierają wyłącznie obiekty
    z bieżącej mapy o zgodnym `owner_id`, w kolejności regionów mapy; podbój usuwa
    osadę dawnemu właścicielowi i przypisuje ją zdobywcy. Identyfikator, bohater,
    dziedzic i morale pozostają bez zmian; wejściowe stany nie są mutowane.
- [x] **A7.2b2** Aktualizacja życia bohatera po wojskowej akcji tury.
  - AC: po utracie party prowadzonego przez bohatera stan księstwa przechodzi przez
    istniejącą sukcesję albo jawny stan bez bohatera; brak poległego party nie
    uśmierca bohatera pozostającego poza mapą; wynik jest spójny z `WorldMap`.
    Czyste `driver.resolve_hero_survival(duchy, world_before, world_after)`.
- [ ] **A7.2b3** Czysty driver tur headless do rozstrzygnięcia.
  - AC: deterministycznie wykonuje kolejne polityki księstw na setupie A7.2a,
    synchronizuje stan gry po akcjach (`sync_from_world` + `resolve_hero_survival`),
    kończy po `GameState.is_over` i ma bezpiecznik liczby tur. `driver.run_headless_game`.
- [ ] **A7.2b4** Headless CLI wypisuje wynik całej partii.
  - AC: `run.sh` uruchamia driver A7.2b3, wypisuje zwycięzcę albo remis; test smoke
    obejmuje pełną pętlę i kod wyjścia 0.

## Później (poza MVP)
- [ ] Prezentacja/UI (pygame lub most do innego silnika) nad rdzeniem.
- [ ] Bogatszy model ran, terenu, budynków; więcej typów jednostek.
- [ ] Balans ekonomii i krzywych progresji; strojenie AI.
- [ ] Kalendarz/fazy `StrategicTurn` w headless driverze (obecnie MVP używa
      bezpośrednio `take_duchy_turn`); spięcie z ekonomią miesięczną per tura.
