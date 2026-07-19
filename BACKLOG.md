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
> **A7.2b1** i **A7.2b2** ukończone — przeniesione do `BACKLOG-ARCHIVE.md`.
>
> **A7.2b3a** ukończone — przeniesione do `BACKLOG-ARCHIVE.md`.
>
> **A7.2b3b** rozbite dalej na trzy mikro-klocki (`b3b1`–`b3b3`, task-009–011).
> Powód: monolityczne `b3b` (iteracja księstw + akcja + sukcesja + sync w jednym
> przyroście) dwukrotnie utknęło na limicie 12 cykli mikro-TDD (brak jednego,
> wyraźnie czerwonego testu na krok). Każdy klocek dodaje teraz dokładnie jedną
> obserwowalną warstwę: przewleczenie mapy → synchronizacja stanu gry → przeżycie
> bohatera. `b3c`/`b4` przenumerowane na task-012/013 (treść bez zmian).
- [ ] **A7.2b3b1** Jedna tura: akcje księstw na wspólnej mapie. *(task-009)*
  - AC: przy `max_turns >= 1` niepokonane księstwa w kolejności `game.duchies`
    wołają `take_duchy_turn`, karmiąc wynikiem następne; zwrócona `WorldMap`
    odzwierciedla akcje AI; `game` zwracany bez zmian; pominięcie pokonanych; czyste.
- [ ] **A7.2b3b2** Synchronizacja stanu gry po akcji księstwa. *(task-010)*
  - AC: po `take_duchy_turn` każdego księstwa `game = game.sync_from_world(world)`;
    iteracja bierze migawkę `duchy_id`, pobiera bieżące księstwo i pomija
    `is_defeated`; księstwo bez ostatniej osady odpada w tej samej turze; czyste.
- [ ] **A7.2b3b3** Przeżycie bohatera w akcji tury. *(task-011)*
  - AC: `resolve_hero_survival` (before/after wokół akcji) wpięte przed sync; utrata
    jedynego party w turze → sukcesja (dziedzic→bohater, `−SUCCESSION_MORALE_PENALTY`);
    przetrwanie party → bohater/morale bez zmian; czyste.
- [ ] **A7.2b3c** Pętla do rozstrzygnięcia i determinizm. *(task-012)*
  - AC: powtarza tury aż `GameState.is_over` albo do `max_turns`; ten sam seed →
    ten sam wynik; pełna pętla na `create_headless_game()` osiąga `is_over` przed
    bezpiecznikiem i wskazuje zwycięzcę.
- [ ] **A7.2b4** Headless CLI wypisuje wynik całej partii. *(task-013)*
  - AC: `run.sh` uruchamia driver A7.2b3, wypisuje zwycięzcę albo remis; test smoke
    obejmuje pełną pętlę i kod wyjścia 0.

## Później (poza MVP)
- [ ] Prezentacja/UI (pygame lub most do innego silnika) nad rdzeniem.
- [ ] Bogatszy model ran, terenu, budynków; więcej typów jednostek.
- [ ] Balans ekonomii i krzywych progresji; strojenie AI.
- [ ] Kalendarz/fazy `StrategicTurn` w headless driverze (obecnie MVP używa
      bezpośrednio `take_duchy_turn`); spięcie z ekonomią miesięczną per tura.
