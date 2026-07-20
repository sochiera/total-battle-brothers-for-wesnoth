# BACKLOG — Total Battle Brothers

> **Kolejka zadań.** Każde zadanie = jeden mały, testowalny przyrost (TDD).
> Statusy: `[ ]` do zrobienia, `[~]` w toku, `[x]` zrobione.
> Bierz zadania z góry. Nie łącz wielu przyrostów w jeden. Aktualizuj status i
> dopisuj nowe zadania, gdy wizja się doprecyzowuje. Detale mechaniki → `docs/DESIGN.md`.
> Ukończone milestony przeniesione do `BACKLOG-ARCHIVE.md` (kamienie 0–10 oraz
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

## Kamień milowy 10 — realne straty i koszty w pętli strategicznej — UKOŃCZONE
> Garnizon ponosi straty po bitwie (G10.1–G10.2), rekrutacja kosztuje złoto
> (G10.3), AI otwiera budynki i rozwija ekonomię w pełnej polityce tury
> (G10.4–G10.5), a rekonstrukcja mapy po podmianie osady jest zdeduplikowana
> w `WorldMap.with_settlement` (R10.1). Wszystkie pozycje (task-022…035)
> w `BACKLOG-ARCHIVE.md`. Strojenie wartości pozostaje balansem.

## Kamień milowy 11 — regeneracja i ciągłość władzy — UKOŃCZONE
> Rany czasowe mijają (garnizon leczy się w łańcuchu miesięcznym), ogłuszenie
> nie wychodzi z bitwy na mapę, a bezhetmańskie księstwo z osadą wystawia
> nowego bohatera w turze (W11.1–W11.3, D11.4a–b; task-036…040). Wszystkie
> pozycje w `BACKLOG-ARCHIVE.md`. Balans kosztów/czasów pozostaje poza kamieniem.

## Kamień milowy 12 — morale w walce i ciągłość dynastii — UKOŃCZONE
> Morale księstw (w tym kara sukcesji) realnie steruje celnością stron bitwy
> w headless, party leczą rany w turze mapy, a bezhetmańskie księstwo wyznacza
> dziedzica prowadzącego do sukcesji. Wszystkie pozycje (task-056…064)
> w `BACKLOG-ARCHIVE.md`.

## Kamień milowy 13 — minimalna warstwa wizualna (obserwator) — UKOŃCZONY
> DESIGN §9a: osobny pakiet `src/tbbui/` w czystym stdlib (SVG/HTML +
> `http.server`) daje deterministyczny widok mapy strategicznej, pola bitwy
> heksowej, stronę partii oraz przeglądarkowy podgląd z „następną turą".
> Rdzeń `tbb` nie importuje `tbbui`. Wszystkie pozycje (task-065…075) w
> `BACKLOG-ARCHIVE.md`. Rozkazy gracza z przeglądarki — Kamień 14.

## Kamień milowy 14 — rozkazy gracza w podglądzie (single-player) — UKOŃCZONY
> DESIGN §9a/§6: podgląd K13 to obserwator AI-vs-AI. K14 dał graczowi realną
> sprawczość: steruje **jednym** księstwem (`player`), AI resztą. „Następna
> tura" rusza wyłącznie AI (K14.1), a gracz wydaje rozkazy przez `POST /order/*`
> reużywające istniejące czyste prymitywy `ai.*` — wybór celu automatyczny
> (placeholder), gracz decyduje *czy* wykonać akcję. Wszystkie pozycje
> (task-076…084) w `BACKLOG-ARCHIVE.md`. Wybór konkretnej osady/celu → Kamień 15.

## Kamień milowy 15 — wybór celu przez gracza (realna sprawczość)
> DESIGN §9a (PLAN K15): K14 dał decyzję *czy*, cel wybierał automat. K15
> **odwraca** ten placeholder: gracz wskazuje *dokąd* maszeruje i *którą* obcą
> osadę szturmuje. Nowe prymitywy AI biorą **jawny region docelowy**; podgląd
> czyta `?target=…`, brak/nieznany target zachowuje automatyczne prymitywy
> (zgodność wstecz). Wybór celu nie zmienia rozstrzygania bitwy ani morale.
- [x] **K15.1a** Prymityw AI marszu na wskazany region (`ai.march_duchy_party_to`). *(task-085)*
- [x] **K15.1b** Rozkaz gracza: marsz na wskazany region (`POST /order/march?target=`). *(task-086)*
- [x] **K15.1c** UI wyboru celu marszu (formularze per region-cel). *(task-087)*
- [x] **K15.2a** Prymityw AI szturmu na wskazaną osadę (`ai.assault_duchy_party_to`). *(task-088)*
- [x] **K15.2b** Rozkaz gracza: szturm na wskazaną osadę (`POST /order/assault?target=`). *(task-089)*
- [ ] **K15.2c** UI wyboru celu szturmu (formularze per obca osada). *(task-090)*
  - AC: gdy gracz ma party — po jednym `<form action="/order/assault?target=…">`
    na obcą osadę; brak party = pojedynczy fallbackowy formularz; reszta bez zmian.

## Kamień milowy 16 — obserwowalna bitwa gracza w podglądzie
> DESIGN §9a (PLAN K16): `render_battle_svg` istnieje (V13.3b), ale gracz nigdy
> nie *widzi* bitwy — rozkaz szturmu zmienia tylko mapę/panel. K16 wpina
> rozstrzygniętą bitwę w stronę partii: rdzeń nagrywa `HexBattle` obok mapy,
> prymityw AI szturmu na jawny cel go zwraca, a `GameApp` renderuje ostatnią
> bitwę. Prymitywy-pierwsze, każdy krok mały i testowalny.
- [ ] **K16.1a** Strona partii z opcjonalnym slotem SVG bitwy (`render_game_page(..., battle=None)`). *(task-091)*
  - AC: `battle: HexBattle` → osadza `render_battle_svg`; `None` = wynik bez zmian; czyste.
- [ ] **K16.1b** Rdzeń: nagrana wersja szturmu osady (`resolve_settlement_battle_recorded → (WorldMap, HexBattle)`). *(task-092)*
  - AC: składa start→auto_resolve→apply, zwraca mapę i bitwę; `resolve_settlement_battle`
    deleguje (tylko mapa); bez dodatkowego RNG; deterministyczne.
- [ ] **K16.1c** Prymityw AI szturmu na wskazaną osadę zwraca bitwę (`ai.assault_duchy_party_to_recorded`). *(task-093)*
  - AC: cel sąsiedni z obcą osadą → `(mapa, bitwa)` przez recorded; ścieżki no-op →
    `(world, None)` bez RNG; mapa identyczna z `assault_duchy_party_to`.
- [ ] **K16.1d** `GameApp` przechwytuje i renderuje ostatnią bitwę po rozkazie szturmu. *(następny wsad)*
  - AC: rozkaz `assault?target=` przez recorded ustawia `last_battle`; `_render`
    przekazuje ją do `render_game_page`; inne rozkazy / tura czyszczą `last_battle`.

## Dług/refaktor
- [ ] **R15.1 (refaktor)** Kompaktacja DESIGN.md do stanu obecnego; historia → DECISIONS.md. *(task-094)*
  - AC: bez nowych testów; bloki „ROZSTRZYGNIĘTE" → jednoliniowe wpisy DECISIONS
    lub proza stanu obecnego; anty-osłabianie reguł; DESIGN krótszy o ≥30%.

## Później (poza MVP)
- [ ] **R12.1 (opcjonalny dług)** Wspólna kwerenda własnych osad w `ai.py`:
      generator `_owned_settlements(world, duchy_id)` reużyty przez
      `develop_duchy_settlement`/`raise_duchy_hero`/`recruit_duchy_unit`/
      `muster_duchy_party`. Zdjęty z K12 po dwóch micro-cap porażkach refaktorów
      w pętli — duplikacja ~4 linii × 4 funkcje nie blokuje MVP. Podjąć tylko
      gdy pojawi się kolejny konsument tego wzorca.
- [ ] Bogatszy model ran, terenu, budynków; więcej typów jednostek.
- [ ] **Bramkowanie treningu budynkiem (§5 „odpowiednie budynki"):** katalog
      budynku treningowego i wymóg jego czynności w `tick_training` (dziś trening
      jest bezwarunkową funkcją czasu). Analogicznie polityka AI otwierania
      kuźni/budynków treningowych.
- [ ] Balans ekonomii, tempa rozwoju jednostek i krzywych progresji; strojenie AI.
- [ ] Pełna maszyna faz `StrategicTurn` w headless driverze (routing akcji AI przez
      fazy ruch/bitwy zamiast bezpośredniego `take_duchy_turn`). M8 reużywa tylko
      prymitywów `tick_settlements`/`end_turn`, bez wciągania phase-gatingu.
