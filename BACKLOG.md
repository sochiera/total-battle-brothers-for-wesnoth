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

> **Kamień 56 — UKOŃCZONE.** Czytelna gotowość uzbrojenia garnizonu (Kuźnia) w
> panelu osady (flaga `data-equip-ready` + sufiks ` · uzbrojenie: …`) oraz
> refaktor R56.1 (wspólny helper gotowości bramkowanej budynkiem). Szczegóły w
> `BACKLOG-ARCHIVE.md`.

> **Kamień 57 — UKOŃCZONE.** Czytelny bilans ekonomiczny osady w panelu:
> atrybuty `data-wheat-production` / `data-gold-production` /
> `data-wheat-consumption` + flaga `data-wheat-surplus` i czytelne sufiksy
> ` · produkcja/mies.: … · konsumpcja: …` oraz ` · bilans pszenicy:
> nadwyżka|deficyt`. Szczegóły w `BACKLOG-ARCHIVE.md`.

## Kamień milowy 58 — zbiorcza gospodarka księstwa w podsumowaniu gracza
> DESIGN §11: po K57 (przepływ pojedynczej osady) gracz z kilkoma osadami
> potrzebuje zbiorczego zdrowia gospodarki. `render_player_summary` sumuje już
> zapasy — K58 dokłada zbiorczą miesięczną produkcję/konsumpcję, bilans i saldo
> pszenicy księstwa.
- [x] **K58.1a** `data-wheat-production` / `data-wheat-consumption` (sumy po osadach księstwa) w korzeniu `data-player-summary`, zaraz po `data-wheat`; tekst bez zmian. *(task-276)*
- [ ] **K58.1b** widoczny sufiks ` · produkcja/mies.: +Pw pszenicy · konsumpcja: Cw pszenicy` spójny z atrybutami; ARCHITECTURE, DESIGN §11, DECISIONS `K58.1b`. *(task-277)*
- [ ] **K58.2a** `data-wheat-surplus="true|false"` (= suma `production.wheat` `>=` suma `consumption.wheat`) w korzeniu `data-player-summary`, zaraz po `data-wheat-consumption`; tekst bez zmian. *(task-278)*
- [ ] **K58.2b** widoczny sufiks ` · bilans pszenicy: nadwyżka` / ` · bilans pszenicy: deficyt` spójny z flagą; ARCHITECTURE, DESIGN §11, DECISIONS `K58.2b`. *(task-279)*
- [ ] **K58.3a** `data-wheat-net="<int ze znakiem>"` (= suma `production.wheat` − suma `consumption.wheat`) w korzeniu `data-player-summary`, zaraz po `data-wheat-surplus`; tekst bez zmian. *(task-280)*
- [ ] **K58.3b** widoczny sufiks ` · saldo pszenicy/mies.: {net:+d}` spójny z atrybutem; ARCHITECTURE, DESIGN §11, DECISIONS `K58.3b`. *(task-281)*

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
