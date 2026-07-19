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
> **A7.2b3** rozbite na trzy mniejsze przyrosty (`b3a`–`b3c`). Powód: w poprzednim
> wsadzie cały `run_headless_game` dało się napisać w ~2 cyklach, przez co mikro-TDD
> zapętlił się na cyklach `no_test` (brak czerwonego testu) i wsad porzucono bez
> commita. Drobniejsze kroki dają każdemu cyklowi jeden, wyraźnie failujący test.
- [ ] **A7.2b3a** Szkielet drivera i bezpiecznik. *(task-005)*
  - AC: `run_headless_game(world, game, rng, max_turns=1000) -> (WorldMap, GameState)`
    istnieje; `game.is_over` na wejściu → zwraca dokładnie wejścia; `max_turns == 0`
    → zwraca wejścia niezmienione; czyste (bez mutacji wejść).
- [ ] **A7.2b3b** Jedna tura: polityki, przeżycie bohatera, synchronizacja. *(task-006)*
  - AC: przy `max_turns >= 1` wykonuje dokładnie jedną turę — każde niepokonane
    księstwo w kolejności `game.duchies` woła `take_duchy_turn`, a po jego akcji
    `resolve_hero_survival` + `GameState.sync_from_world` aktualizują stan gry.
- [ ] **A7.2b3c** Pętla do rozstrzygnięcia i determinizm. *(task-007)*
  - AC: powtarza tury aż `GameState.is_over` albo do `max_turns`; ten sam seed →
    ten sam wynik; pełna pętla na `create_headless_game()` osiąga `is_over` przed
    bezpiecznikiem i wskazuje zwycięzcę.
- [ ] **A7.2b4** Headless CLI wypisuje wynik całej partii. *(task-008)*
  - AC: `run.sh` uruchamia driver A7.2b3, wypisuje zwycięzcę albo remis; test smoke
    obejmuje pełną pętlę i kod wyjścia 0.

## Później (poza MVP)
- [ ] Prezentacja/UI (pygame lub most do innego silnika) nad rdzeniem.
- [ ] Bogatszy model ran, terenu, budynków; więcej typów jednostek.
- [ ] Balans ekonomii i krzywych progresji; strojenie AI.
- [ ] Kalendarz/fazy `StrategicTurn` w headless driverze (obecnie MVP używa
      bezpośrednio `take_duchy_turn`); spięcie z ekonomią miesięczną per tura.
