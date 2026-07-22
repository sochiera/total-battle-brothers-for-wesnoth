# BACKLOG — Total Battle Brothers

> **Kolejka zadań.** Każde zadanie = jeden mały, testowalny przyrost (TDD).
> Statusy: `[ ]` do zrobienia, `[~]` w toku, `[x]` zrobione.
> Bierz zadania z góry. Nie łącz wielu przyrostów w jeden. Aktualizuj status i
> dopisuj nowe zadania, gdy wizja się doprecyzowuje. Detale mechaniki → `docs/DESIGN.md`.
> Ukończone milestony (kamienie 0–53 oraz A7.1*/A7.2*) przeniesione do
> `BACKLOG-ARCHIVE.md` — tu zostaje wyłącznie żywy tail w stronę grywalnego MVP.

## Legenda
Każde zadanie ma **kryteria akceptacji** (co musi przejść jako test). Rdzeń przed
prezentacją. Determinizm (seedowalny RNG) jest wymogiem przekrojowym.

---

> **Kamienie 0–53 — UKOŃCZONE.** Pełne streszczenia w `BACKLOG-ARCHIVE.md`
> (headless pętla MVP, ekonomia/kalendarz, rozwój jednostek, straty/koszty,
> regeneracja/sukcesja, morale, warstwa wizualna `tbbui` i cała seria rady
> w jeden klik K41–K52, trening party K53). Żywy tail zaczyna się od K54.

> **Kamienie 54–55 — UKOŃCZONE.** Bramkowanie treningu garnizonu Koszarami
> (katalog `BARRACKS`, AI otwierające je przed Market, no-op `tick_training`
> bez Koszar) oraz czytelna gotowość treningu w panelu osad (flaga
> `data-training-ready` + sufiks ` · trening: …`). Szczegóły w
> `BACKLOG-ARCHIVE.md`.

## Kamień milowy 56 — czytelna gotowość uzbrojenia garnizonu (Kuźnia) w panelu osady
> DESIGN §11: symetria do K55 dla uzbrojenia — `tick_equipment` od dawna wymaga
> czynnej Kuźni (`SMITH`), ale panel tego nie komunikuje. K56 dokłada flagę
> `data-equip-ready` i czytelny tekst gotowości uzbrojenia. Rdzeń `tbb` bez zmian.
- [ ] **K56.1a** `data-equip-ready="true|false"` (= `SMITH in active_buildings`) w każdym `data-settlement-row`, zaraz po `data-training-ready`; tekst bez zmian. *(task-269)*
- [ ] **K56.1b** widoczny sufiks ` · uzbrojenie: gotowe` / ` · uzbrojenie: wstrzymane (brak Kuźni)` spójny z flagą; ARCHITECTURE (panel osad), DESIGN §11 i DECISIONS `K56.1b`. *(task-270)*
- [ ] **R56.1 (refaktor)** wspólny lokalny helper gotowości bramkowanej budynkiem (flaga + sufiks) w `settlementpanel.py`, reużyty przez trening/`BARRACKS` i uzbrojenie/`SMITH`; bez nowych testów, wynik bajt-w-bajt. *(task-271)*

## Dług/refaktor
- [x] **R33.1 (refaktor)** Kompaktacja DESIGN.md §11: usunięcie bloków narracyjnych „PLAN K14…K33" (historia → git/DECISIONS.md); tylko stan obecny. *(task-169)*
- [x] **R21.1 (refaktor)** Wspólny emiter formularzy celu marsz/szturm/starcie w `serve.py`. *(task-113)*
- [x] **R15.1 (refaktor)** Kompaktacja DESIGN.md do stanu obecnego; historia → DECISIONS.md. *(task-094)*
- [x] **R16.1 (refaktor)** Wspólny generator formularzy celu marsz/szturm w `serve.py`. *(task-098)*

## Później (poza MVP)
- [ ] **R12.1 (opcjonalny dług)** Wspólna kwerenda własnych osad w `ai.py`:
      generator `_owned_settlements(world, duchy_id)` reużyty przez
      `develop_duchy_settlement`/`raise_duchy_hero`/`recruit_duchy_unit`/
      `muster_duchy_party`. Zdjęty z K12 po dwóch micro-cap porażkach refaktorów
      w pętli — duplikacja ~4 linii × 4 funkcje nie blokuje MVP. Podjąć tylko
      gdy pojawi się kolejny konsument tego wzorca.
- [ ] Bogatszy model ran, terenu, budynków; więcej typów jednostek.
- [ ] Balans ekonomii, tempa rozwoju jednostek i krzywych progresji; strojenie AI.
- [ ] Pełna maszyna faz `StrategicTurn` w headless driverze (routing akcji AI przez
      fazy ruch/bitwy zamiast bezpośredniego `take_duchy_turn`). M8 reużywa tylko
      prymitywów `tick_settlements`/`end_turn`, bez wciągania phase-gatingu.
