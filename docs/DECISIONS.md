# DECISIONS — jednoliniowe rozstrzygnięcia projektowe

| id | tytuł | rozstrzygnięcie |
|----|-------|-----------------|
| K15.1c | UI wyboru celu marszu | Gdy gracz ma party na mapie, `GET /` renderuje po jednym formularzu `POST /order/march?target=<quote(nazwa)>` na obcą osadę (bez bare `/order/march`); brak party / brak `player_duchy_id` / gra skończona → fallback bare. |
