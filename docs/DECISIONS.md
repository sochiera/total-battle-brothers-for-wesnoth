# DECISIONS — jednoliniowe rozstrzygnięcia projektowe

| id | tytuł | rozstrzygnięcie |
|----|-------|-----------------|
| K16.1b | Nagrana wersja rozstrzygnięcia szturmu osady | `WorldMap.resolve_settlement_battle_recorded(...) -> (WorldMap, HexBattle)` składa start→auto_resolve→apply i zwraca mapę wraz z rozstrzygniętą bitwą; `resolve_settlement_battle` deleguje i zwraca tylko mapę. |
| K16.1a | Opcjonalny slot SVG bitwy na stronie partii | `render_game_page(..., battle=None)` osadza `render_battle_svg(battle)` w `<body>` gdy podano `HexBattle`; `battle=None` / brak argumentu → wynik bajt-w-bajt jak dotychczas. |
| K15.1c | UI wyboru celu marszu | Gdy gracz ma party na mapie, `GET /` renderuje po jednym formularzu `POST /order/march?target=<quote(nazwa)>` na obcą osadę (bez bare `/order/march`); brak party / brak `player_duchy_id` / gra skończona → fallback bare. |
| K15.2a | Prymityw AI szturmu na wskazaną osadę | `ai.assault_duchy_party_to(world, duchy, target, rng, morale_by_owner=None)` szturmuje jawny sąsiedni wrogi `target` (morale jak `assault_nearest_enemy_settlement`); brak party / niesąsiad / brak obcej osady → no-op. |
| K15.2b | Rozkaz gracza: szturm na wskazaną osadę | `POST /order/assault?target=<region>` → `assault_duchy_party_to` z morale z `game.duchies`; brak/pusty/nieznany `target` → fallback `assault_duchy_party`; parsowanie `target` współdzielone z marszem (`_order_target_region`). |
| K15.2c | UI wyboru celu szturmu | Gdy gracz ma party na mapie, `GET /` renderuje po jednym formularzu `POST /order/assault?target=<quote(nazwa)>` na obcą osadę (bez bare `/order/assault`); brak party / brak `player_duchy_id` / gra skończona → fallback bare; cele jak marsz (`_march_targets`). |
