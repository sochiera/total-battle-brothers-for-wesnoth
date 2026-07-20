# DECISIONS — jednoliniowe rozstrzygnięcia projektowe

| id | tytuł | rozstrzygnięcie |
|----|-------|-----------------|
| K15.1c | UI wyboru celu marszu | Gdy gracz ma party na mapie, `GET /` renderuje po jednym formularzu `POST /order/march?target=<quote(nazwa)>` na obcą osadę (bez bare `/order/march`); brak party / brak `player_duchy_id` / gra skończona → fallback bare. |
| K15.2a | Prymityw AI szturmu na wskazaną osadę | `ai.assault_duchy_party_to(world, duchy, target, rng, morale_by_owner=None)` szturmuje jawny sąsiedni wrogi `target` (morale jak `assault_nearest_enemy_settlement`); brak party / niesąsiad / brak obcej osady → no-op. |
| K15.2b | Rozkaz gracza: szturm na wskazaną osadę | `POST /order/assault?target=<region>` → `assault_duchy_party_to` z morale z `game.duchies`; brak/pusty/nieznany `target` → fallback `assault_duchy_party`; parsowanie `target` współdzielone z marszem (`_order_target_region`). |
