# BACKLOG — Total Battle Brothers

## US-001 — Gracz widzi bitwę przed jej rozstrzygnięciem  [nowa]

Jako gracz chcę po rozpoczęciu szturmu lub starcia zobaczyć rozmieszczenie
walczących na planszy, żeby bitwa nie sprowadzała się do samego wyniku.

- Dlaczego teraz: PROJECT.md wskazuje brak agencji w taktycznej bitwie jako największą otwartą rozbieżność z briefem.
- Sprawdzenie: uruchom grę, doprowadź do szturmu lub starcia i potwierdź, że przed wynikiem pojawia się plansza z rozmieszczeniem jednostek.
- Poza zakresem: wybór celu, ręczny ruch jednostek, zmiany reguł walki i zmiany zachowania AI.

## US-002 — Gracz przechodzi jedną rundę bitwy  [nowa]

Jako gracz chcę przejść następną rundę trwającej bitwy, żeby obserwować jej
przebieg krok po kroku.

- Dlaczego teraz: PROJECT.md wyznacza przechodzenie rund jako najcieńszy krok od automatycznego wyniku do rozgrywanej bitwy.
- Sprawdzenie: na widoku trwającej bitwy wybierz następną rundę i potwierdź widoczną zmianę pozycji, PŻ lub ogłuszenia jednostek.
- Poza zakresem: wybór celu, ręczne wskazywanie ruchu, nowe obrażenia i nowe zasady tur jednostek.

## US-003 — Gracz może od razu dokończyć trwającą bitwę  [nowa]

Jako gracz chcę zlecić automatyczne rozegranie pozostałych rund, żeby nie
musieć krokować walki, której dalszy przebieg chcę tylko poznać.

- Dlaczego teraz: PROJECT.md zachowuje automatyczne rozstrzygnięcie jako część cienkiego pierwszego kroku ku taktycznej bitwie.
- Sprawdzenie: rozpocznij bitwę, wybierz rozstrzygnięcie od razu i potwierdź, że gra pokazuje końcowy baner oraz skutki bitwy w świecie.
- Poza zakresem: zmiana wyniku względem dotychczasowego automatycznego rozstrzygnięcia, balans walki i tempo AI.

## US-004 — Gracz dostaje jasną blokadę działań strategicznych podczas bitwy  [nowa]

Jako gracz chcę wiedzieć, że najpierw muszę zakończyć trwającą bitwę, żeby nie
próbować bezskutecznie wydawać rozkazów na mapie ani przesuwać miesiąca.

- Dlaczego teraz: PROJECT.md wymaga, by bezskuteczny rozkaz niósł powód, a stan bitwy w toku ma zatrzymać pozostałe działania gracza.
- Sprawdzenie: podczas trwającej bitwy spróbuj wydać rozkaz strategiczny i przejść do następnej tury; potwierdź brak zmiany świata i komunikat o bitwie w toku.
- Poza zakresem: nowe rozkazy strategiczne, zmiana kosztów akcji i równoległe rozgrywanie mapy oraz bitwy.

## US-005 — Gracz wznawia zapisaną bitwę w tym samym stanie  [nowa]

Jako gracz chcę zapisać grę podczas bitwy i po wczytaniu kontynuować ją od
tego samego układu, żeby zapis partii działał także w trakcie walki.

- Dlaczego teraz: PROJECT.md wymaga zapisu i wczytania stanu, a planowany stan bitwy w toku musi zachować tę obietnicę produktu.
- Sprawdzenie: rozpocznij bitwę, przejdź rundę, zapisz i wczytaj grę, a następnie potwierdź ten sam układ jednostek, PŻ i możliwość przejścia kolejnej rundy.
- Poza zakresem: wiele slotów zapisu, historia powtórek i zmiana istniejącego interfejsu zapisu poza obsługą bitwy w toku.
