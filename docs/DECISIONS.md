# DECISIONS — jednoliniowe rozstrzygnięcia projektowe

| id | tytuł | rozstrzygnięcie |
|----|-------|-----------------|
| C1.3 | Geometria heksów | Rdzeń używa współrzędnych axial `(q, r)` z konwersją do cube `(x, y, z)`, `x+y+z=0`, do dystansu i sąsiadów; offset tylko dla przyszłej prezentacji. |
| U3.1 | Mapowanie filar→statystyka | `Unit` niemutowalny: `hp=10+training`, `accuracy=training+experience`, `damage=equipment`, `defense=equipment+experience` (wagi liniowe placeholder). |
| U3.2 | Krzywa nakład→poziom | Poziom filaru z nakładu: `T(n)=n·(n+1)/2`, `level(inv)=(isqrt(8·inv+1)−1)//2`; dotyczy treningu i uzbrojenia; doświadczenie tylko z walki. |
| U3.3 | Rekrutacja do garnizonu | `Settlement.recruit()` zajmuje 1 wolną populację (`occupy(1)`) i dokłada `Unit()` do garnizonu; brak wolnej populacji → `ValueError`. |
| U9.1 | Trening jednostki | `Unit.train(months)` dodaje miesiące do `T(training)+training_progress`, nowy poziom z U3.2; 0 = no-op, ujemne = błąd. |
| U9.2 | Uzbrojenie jednostki | `Unit.equip(investment)` analogicznie przez `equipment`/`equipment_progress` i U3.2; 0 = no-op, ujemne = błąd. |
| U9.3 | Miesięczny trening garnizonu | `Settlement.tick_training()` daje każdej jednostce `TRAINING_MONTHS_PER_TURN` (placeholder `1`) przez `Unit.train()`. |
| U9.4 | Miesięczne uzbrajanie garnizonu | `Settlement.tick_equipment()` przy Smith + garnizon + `EQUIP_GOLD_COST` złota uzbraja jednego żołnierza o najniższym `equipment` (remis: najwcześniejsza pozycja); placeholdery `1`. |
| U9.5 | Łańcuch miesięczny osad | `WorldMap.tick_settlements()`: `tick_economy → tick_growth → tick_immigration → tick_training → tick_equipment → tick_healing`. |
| E2.3 | Ekonomia miesięczna | Aktywny budynek produkuje `output`; konsumpcja 1 pszenica/mieszkaniec/miesiąc; bilans podłogowany na zero; Farm/Market/Smith jak w katalogu. |
| E2.4a | Urodzenia | `tick_growth()`: +1 populacji gdy `wheat>0` i poniżej `capacity`; głód (`wheat==0`) nie rośnie; nowi do puli wolnej. |
| E2.4b | Imigracja | `tick_immigration()` po `tick_growth`: +1 gdy `gold>0` i `wheat>0` i poniżej `capacity`; bez konsumpcji złota. |
| B4.1 | Katalog terenu | `Terrain(move_cost, defense_mod, accuracy_mod)`; Plains 1/0/0, Forest 2/+2/−1, Hills 2/+1/+1; `Battlefield` rzadkie `Hex→Terrain`, domyślnie Plains. |
| B4.2a | Deployment | `HexBattle.deploy(unit, position)` — max 1 jednostka/heks; zajęty heks → `ValueError`; jednostki identyfikowane pozycją. |
| B4.2b | Ruch na bitwie | `move(source, destination, move_points)` po najtańszej ścieżce; jednostki blokują; `reachable` = Dijkstra z budżetem. |
| B4.3a | Szansa trafienia | `clamp(50 + accuracy_att + accuracy_mod_att + morale − defense_def − defense_mod_def, 5, 95)`; morale podpisane; `accuracy_mod`/`defense_mod` terenu pozycji. |
| B4.3b1 | Bieżące HP | Deploy inicjalizuje HP = `Unit.hp`; obrażenia z podłogą 0; 0 HP = pokonana. |
| B4.3b2 | Walka wręcz | Strony ATTACKER/DEFENDER; atak tylko wrogowie na sąsiadach; 1 rzut RNG; pudło bez zmian HP, trafienie −`damage`. |
| B4.4a | Atak dystansowy | `Unit.ranged_range` (domyślnie 0); `≥2` → strzał na dystans 2…range; ten sam wzór trafienia i `damage`; bez kontrataku. |
| B4.4b1 | Linia heksów | `Hex.line_to(other)` — sekwencja długości `distance+1`, cube-interpolacja, deterministyczna reguła remisu na granicy. |
| B4.4b2 | Przeszkody LOS | Jednostka na heksie pośrednim linii blokuje strzał przed RNG; heksy atakującego i celu nie są przeszkodami. |
| B4.5a | Model ran | Rana: mod `accuracy`/`defense`, `duration_months` lub trwała (`None`); Bruise 2m −1/−1, Maimed trwała −2/−2; sumowanie, podłoga 0. |
| B4.5b | Rozstrzygnięcie 0 HP | `resolve_defeat`: 50% śmierć (usunięcie), 50% `stunned=True` + Bruise; ogłuszona nie rusza się ani nie atakuje. |
| B4.6a | Koniec bitwy | Aktywna = HP>0 i nie ogłuszona; wygrywa strona z jedynymi aktywnymi; brak aktywnych obu → remis. |
| B4.6b | Raport bitwy | Niemutowalny: wynik + poległe/ogłuszone/zdolne per strona; rejestr poległych w `HexBattle`; kolejność deterministyczna. |
| B4.6c | XP za udział | Ocalali (aktywni + ogłuszeni) +1 doświadczenia; polegli bez nagrody; czyste przejście nad raportem. |
| BD.1 | Wybór celu | `nearest_enemy(position)` — najbliższa aktywna wroga; remis: `_deployment_order`; brak → `None`. |
| BD.2 | Tura jednostki | Sąsiad → 1 atak wręcz (+ resolve 0 HP); inaczej ruch ku celowi `(dist,q,r)`; albo atak albo ruch. |
| BD.3 | Auto-rozgrywka | `auto_resolve(move_points, rng, attacker_morale=0, defender_morale=0)` do wyniku lub `max_rounds=1000`; snapshot kolejności na rundę. |
| B12.1a | Morale per strona | `auto_resolve` bierze `attacker_morale`/`defender_morale` zamiast jednolitego `morale`. |
| B12.1b-1 | Morale w resolve mapy | `resolve_party_battle` / `resolve_settlement_battle` przyjmują `attacker_morale`/`defender_morale` (domyślnie 0/0). |
| B12.1b-2a | Szturm AI z morale | `assault_nearest_enemy_settlement(..., morale_by_owner=None)` mapuje owner→morale stron. |
| B12.1b-2b | Morale w polityce AI | `take_duchy_military_action` / `take_duchy_turn` przyjmują i przekazują `morale_by_owner`. |
| B12.1b-2 | Morale z GameState | `run_headless_game` buduje `{duchy_id: morale}` przed każdym `take_duchy_turn`. |
| B12.1b-2c | Mapa morale w driverze | Driver buduje `morale_by_owner` z bieżącego `GameState` przed polityką tury. |
| M5.1a | Graf regionów | `WorldMap`: skończony niemutowalny graf; `Region` po `name`; połączenia dwukierunkowe; max 1 `Settlement`/region; kolejność regionów deterministyczna. |
| M5.1b | Pozycje party | `Region → Party`; max 1 party/region; party może stać w regionie z osadą; `party_at` / `place_party`. |
| M5.2a | Skład party | `Party`: wymagany `hero` + ≤12 `units`; bohater poza limitem 12. |
| M5.2b | Ruch party | `move_party` do wolnego sąsiada, koszt 1 MP, budżet ≥1; wejście na zajęty region odrzucane. |
| M5.3a | Kontakt party↔party | `start_battle`: sąsiednie party → `HexBattle` (atakujący = inicjator); kolejność hero+units; rzędy na Plains; bez mutacji mapy. |
| M5.3b1 | Kontakt party↔osada | `start_settlement_battle`: party vs garnizon sąsiada → `HexBattle`; bez mutacji mapy/osady/garnizonu. |
| M5.3b2 | Własność strategiczna | `owner_id` na `Party`/`Settlement`; bitwa wymaga jawnych różnych ownerów; równe/brak → blokada. |
| M5.4a | Kalendarz | Start rok 1 / miesiąc 1; tura = +1 miesiąc; po 13 → miesiąc 1 kolejnego roku; tylko rok+miesiąc. |
| M5.4b | tick_settlements | Aktualizuje osady w kolejności regionów łańcuchem ekonomii/wzrostu/U9.5; bez kalendarza. |
| M5.4c1 | StrategicTurn | Fazy osady→ruch→bitwy→zakończona; wejście w ruch = 1×`tick_settlements`; kalendarz +1 przy końcu bitew. |
| M5.4c2 | Bramkowanie fazą | `move_party` tylko w fazie ruchu; `start_battle`/`start_settlement_battle` tylko w fazie bitew. |
| BW.1 | Wynik party↔party | `apply_party_battle_result`: ATTACKER_WIN → atakujący zajmuje destination; DEFENDER_WIN → atakujący znika; DRAW → oba znikają. |
| BW.2 | Wynik party↔osada | `apply_settlement_battle_result`: ATTACKER_WIN = podbój owner + party na destination; DEF/DRAW = atakujący znika, owner bez zmian. |
| BW.3a | side_survivors | `HexBattle.side_survivors(side)` — ocalali na planszy w `_deployment_order` (przeplatani). |
| BW.3b | reconstruct | `Party.reconstruct(original, survivors)`: slot 0 = hero, reszta units; `owner_id` z original; pusta sekwencja odrzucona. |
| BW.3c | Rekonstrukcja w apply | Opcjonalny `battle` w apply_*: gdy podany — reconstruct ocalałych; `None` = placeholderowy skład. |
| W11.1 | Upływ ran | `Unit.tick_wounds(months=1)` zmniejsza duration ran czasowych; trwałe bez zmian. |
| W11.2 | Ocalali bez stunned | Ocalali zachowują rany/XP, wracają z `stunned=False` (reconstruct i absorb_defenders). |
| W11.3 | Leczenie garnizonu | `Settlement.tick_healing()` po tick_equipment w tick_settlements. |
| W12.2 | Leczenie party | `WorldMap.tick_parties()` → `Party.tick_wounds(1)` w kolejności regionów; driver po tick_settlements. |
| BM.1 | resolve_party_battle | Składa start→auto_resolve→apply; ocalali w składzie; MP placeholder 1; morale per strona. |
| BM.2 | resolve_settlement_battle | Składa szturm→auto_resolve→apply; podbój przy ATTACKER_WIN; ocalali; morale per strona. |
| K16.1b | Nagrana wersja szturmu | `resolve_settlement_battle_recorded(...) -> (WorldMap, HexBattle)`; `resolve_settlement_battle` deleguje i zwraca tylko mapę. |
| K18.1a | Nagrana bitwa party↔party | `resolve_party_battle_recorded(...) -> (WorldMap, HexBattle)`; `resolve_party_battle` deleguje i zwraca tylko mapę. |
| K18.1b | Auto-starcie party↔party z nagraniem | `engage_duchy_party_recorded → (WorldMap, HexBattle\|None)`; pierwszy sąsiad z wrogim jawnym `owner_id` → recorded; no-op → (world, None) bez RNG. |
| K18.1c | POST /order/engage | `_apply_player_assault_order` + `engage_duchy_party_recorded`; bare form GET; last_battle jak szturm. |
| K19.1a | Starcie na wskazany cel | `engage_duchy_party_to_recorded → (WorldMap, HexBattle\|None)`; jawny sąsiedni wrogi `target` → recorded; no-op → (world, None) bez RNG. |
| K19.1b | POST /order/engage?target= | Routing jak szturm: znany `target` → `engage_duchy_party_to_recorded`, brak/nieznany → auto `engage_duchy_party_recorded`. |
| K19.1c | Formularze celu engage w GET / | `_engage_targets` = sąsiedzi party gracza z wrogim jawnym `owner_id`; `_engage_forms` emituje po jednym `?target=` lub bare `_ENGAGE_FORM`. |
| G10.1 | absorb_defenders | `Settlement.absorb_defenders(survivors)` zastępuje garnizon; polegli −population i −occupied; sekwencja > garnizon odrzucona. |
| G10.2a | Garnizon po obronie | apply_settlement DEF/DRAW + battle → absorb_defenders(DEFENDER); bez battle garnizon nietknięty. |
| G10.2b | Garnizon po podboju | ATTACKER_WIN + battle → absorb_defenders potem zmiana owner; bez battle owner się zmienia, garnizon nietknięty. |
| G10.3 | Koszt rekrutacji | `RECRUIT_GOLD_COST` (placeholder `1`); niedobór złota/populacji → `ValueError`. |
| G10.4 | Rozwój osady AI | `develop_duchy_settlement`: pierwszy brakujący budynek Farm→Smith→Market przy wolnej populacji; max 1 budynek. |
| G10.5 | Polityka tury AI | `take_duchy_turn`: develop → recruit → military action; wynik łańcuchowany. |
| Kamień 10 | Realne straty i koszty | Domknięte: straty garnizonu (G10.1–2), koszt rekrutacji (G10.3), rozwój AI (G10.4–5). |
| D6.1a | Model Duchy | Niemutowalny: niepusty `duchy_id`, wymagany `hero`, `morale: int` (domyślnie 0); `duchy_id` = `owner_id` party/osad. |
| D6.1b1 | Dziedzic | Opcjonalny `heir: Unit \| None`; nie ten sam obiekt co `hero`. |
| D6.1b2 | Listy księstwa | `settlements`/`parties` — krotki kopiowane; każdy `owner_id == duchy_id`. |
| D6.2a | Sukcesja z dziedzicem | `succeed()`: heir→hero, heir=None, morale −`SUCCESSION_MORALE_PENALTY` (placeholder `2`). |
| D6.2b | Sukcesja bez dziedzica | `succeed()` bez heir → `hero=None`, ta sama kara morale; `has_hero`; konstruktor odrzuca heir bez hero. |
| D6.3a | is_defeated | `True` iff `has_hero is False` i `settlements == ()`; party nie wpływają. |
| D6.3b | GameState | `GameState(duchies)` unikalne `duchy_id`; `contenders` / `is_over` (≤1 pretendent) / `winner`. |
| D11.4a | raise_hero | `Settlement.raise_hero()` → (osada, świeży Unit); population−1, `HERO_GOLD_COST` (placeholder `2`); nie do garnizonu. |
| D11.4b | raise_duchy_hero | AI: bez hero → pierwsza własna osada stać na koszt → raise_hero; driver przed take_duchy_turn. |
| D12.3 | designate_duchy_heir | AI: ma hero, brak heir → raise_hero z pierwszej własnej osady jako heir; driver po raise, przed take_duchy_turn. |
| MU.1 | muster | `Settlement.muster(hero)`: garnizon→Party, population/occupied −liczba żołnierzy. |
| MU.2 | muster_party | `WorldMap.muster_party(region, hero)` atomowo muster + place_party w regionie. |
| A7.1a | nearest_enemy_settlement | Najbliższa wroga osada (różny owner_id); dystans grafu; remis: kolejność regionów. |
| A7.1b1 | next_march_step | Sąsiad na najkrótszej drodze; omija zajęte regiony; None gdy sąsiad celu lub brak drogi. |
| A7.1b2 | march_toward_nearest_enemy | 1 krok MP=1 ku najbliższej wrogiej osadzie; błąd bez party/owner. |
| A7.1b3 | assault_nearest_enemy_settlement | resolve_settlement_battle gdy cel sąsiad; opcjonalne morale_by_owner. |
| A7.1b4 | muster_duchy_party | Max 1 party/księstwo; pierwsza własna osada z wolnym slotem; no-op gdy party istnieje lub brak hero. |
| A7.1b5a | take_duchy_military_action | muster → marsz → szturm; morale_by_owner do szturmu. |
| A7.1b5b1 | recruit_duchy_unit | 1 rekrut w pierwszej własnej osadzie z free≥1, złoto≥koszt, garnizon<12. |
| A7.1b5b2 | take_duchy_turn | develop → recruit → military (G10.5). |
| A7.2a | create_headless_game | Stały setup: 2 księstwa player/ai, po 1 bohaterze i osadzie z zapasami; party puste; bez RNG. |
| A7.2b1 | sync_from_world | `GameState.sync_from_world(world)` odtwarza settlements/parties po owner_id w kolejności regionów. |
| A7.2b2 | resolve_hero_survival | Party było przed, brak po → `succeed()`; obecność po owner_id. |
| A7.2b3a | run_headless_game szkielet | `(world, game, rng, max_turns=1000, calendar=Calendar(), player_duchy_id=None) → (WorldMap, GameState, Calendar)`. |
| A7.2b3b1 | Akcje księstw | Kolejność `game.duchies`; niepokonane → take_duchy_turn na wspólnej mapie. |
| A7.2b3b2 | Sync po akcji | raise_duchy_hero → designate_duchy_heir → take_duchy_turn; sync po każdym; migawka niepokonanych z początku tury. |
| A7.2b3b3 | Hero survival w turze | Po take_duchy_turn: resolve_hero_survival, podmiana duchy przed sync. |
| A7.2b3c | Pętla do max_turns | Kończy przy is_over; seed 73 + default max_turns → remis na bezpieczniku (rok 77, m. 13) z sukcesją. |
| A7.2b4 | CLI headless | `python -m tbb`: create + run + wypis winner/draw; exit 0. |
| M8.1 | Ekonomia w driverze | Na start tury: tick_settlements → tick_parties → sync; skip gdy is_over lub max_turns=0. |
| M8.2 | Kalendarz w driverze | Po ukończonej turze `calendar.end_turn` (+1 miesiąc); zwrot trójki z Calendar. |
| M8.3 | Data w CLI | CLI raportuje rok/miesiąc z końcowego kalendarza. |
| K13 | Stack prezentacji | Pakiet `tbbui/`: SVG/HTML + http.server stdlib; tryb obserwatora; tbb nie importuje tbbui. |
| V13.2a | SVG mapy — węzły | `render_world_svg`: `g[data-region]` + etykieta; layout_world pitch. |
| V13.2b | SVG mapy — krawędzie | Jeden `<line>` na connection z data-from/to. |
| V13.2c | Znaczniki osada/party | data-settlement/data-party + data-owner przy środku węzła. |
| V13.2d | Paleta właścicieli | `owner_palette(world)`: owner_id→hex cyklicznie; fill znaczników; None→neutralny. |
| V13.3a | Hexgeom | pointy-top `hex_to_pixel` / `hex_corners`. |
| V13.3b | SVG bitwy | `render_battle_svg`: heksy obwiedni ±1, znaczniki data-side/hp/stunned. |
| V13.4a | Strona partii | `render_game_page(world, game, calendar, battle=None)`: SVG mapy, kalendarz, panel duchies, result. |
| K16.1a | Slot SVG bitwy | `render_game_page(..., battle=None)` osadza `render_battle_svg` gdy podano HexBattle. |
| K16.1c | Szturm z nagraniem | `assault_duchy_party_to_recorded → (WorldMap, HexBattle\|None)`; no-op → (world, None) bez RNG. |
| K16.1d-1 | Auto-szturm z nagraniem | `assault_duchy_party_recorded → (WorldMap, HexBattle\|None)`; nearest adjacent → recorded; no-op → (world, None) bez RNG. |
| K16.1d-2 | GameApp last_battle | `GameApp.last_battle`; szturm przez `*_recorded`; `_render` → `render_game_page(..., battle=last_battle)`. |
| K16.1d-3 | Clear last_battle | `/turn` i rozkazy nie-szturmowe (`recruit`/`muster`/`develop`/`march`) zerują `self.last_battle`. |
| K14.1a | Pomijanie tury gracza | `player_duchy_id` na run_headless_game: bez take_duchy_turn dla tego id; tick/sync/raise/heir zostają. |
| K14.1b | GameApp player | `GameApp(..., player_duchy_id=None)`; POST /turn max_turns=1; data-player; serve z `"player"`. |
| K14.2a | POST /order/recruit | `_apply_player_order` → recruit_duchy_unit + sync; formularz GET. |
| K14.2b | POST /order/muster | → muster_duchy_party + sync; formularz GET. |
| K14.2c | POST /order/develop | → develop_duchy_settlement + sync; formularz GET. |
| K14.2d1 | march_duchy_party | Party księstwa → march_toward_nearest_enemy; brak party = no-op. |
| K14.2d2 | POST /order/march | → march_duchy_party (auto cel) lub per-target UI K15. |
| K14.2e1 | assault_duchy_party | Party → assault_nearest_enemy_settlement z morale_by_owner; brak party = no-op bez RNG. |
| K14.2e2 | POST /order/assault | → assault_duchy_party / assault_duchy_party_to z morale z game.duchies. |
| K15.1a | march_duchy_party_to | Jawny target: next_march_step + move_party(…, 1); None step = no-op. |
| K15.1b | march?target= | parse_qs target → Region; znany → march_duchy_party_to; brak → march_duchy_party. |
| K15.1c | UI celów marszu | Przy party gracza: form per obca osada `?target=`; inaczej bare /order/march. |
| K15.2a | assault_duchy_party_to | Jawny sąsiedni wrogi target → resolve_settlement_battle; inaczej no-op bez RNG. |
| K15.2b | assault?target= | Jak K15.1b; fallback assault_duchy_party. |
| K15.2c | UI celów szturmu | Jak K15.1c dla /order/assault; cele z `_march_targets`. |
| K17.1a | HTML raport bitwy | `tbbui.battlereport.render_battle_report(battle) -> str`: fragment `data-battle-report` z `data-battle-result` i per-stroną `data-battle-side`/`data-fallen`/`data-stunned`/`data-active` z `HexBattle.report()`. |
| K17.1b | Raport w stronie partii | `render_game_page(..., battle=…)` osadza kanoniczny `render_battle_report(battle)` w `<body>` obok SVG bitwy; bez `battle` wynik bajt-w-bajt jak wcześniej. |
| K20.1a | Banner wyniku | `render_game_page` zawsze osadza `<p data-result-text>` (`Gra w toku` / `Remis` / `Zwycięstwo: <duchy_id>`) z `_result_text`; `data-result` bez zmian. |
| K20.1b | Wiersz statusu księstwa | Każdy `data-duchy` ma widoczny tekst `<duchy_id>: osady N, party M, morale K` zgodny z atrybutami; atrybuty `data-*` bez zmian. |
| K21.1a | Tekst kalendarza | Element `data-calendar` ma widoczny tekst `Rok N, miesiąc M` z `Calendar`; atrybuty `data-year`/`data-month` bez zmian. |
| K21.1b | Tekst wyniku bitwy | `render_battle_report` ma widoczny tekst `Zwycięstwo atakującego`/`Zwycięstwo broniącego`/`Remis` wg `report.result`; `data-battle-result` bez zmian. |
| K21.1c | Tekst strat bitwy | Każdy `data-battle-side` ma widoczny tekst `Atakujący/Broniący: polegli N, ogłuszeni M, zdolni K` zgodny z atrybutami; `data-*` bez zmian. |
| K21.2 | Nagłówki sekcji rozkazów | `GET /` ma po jednym `<h2 data-order-section="march\|assault\|engage">Marsz\|Szturm\|Starcie</h2>` przed grupą formularzy danej akcji; formularze/routing bez zmian. |
| R21.1 | Emiter formularzy celu | Wspólna pętla formularzy `?target=` w jednym helperze `GameApp`, reużyta przez marsz/szturm/starcie; zachowanie GET `/` bez zmian. |
| K22.1a | Panel osad — zasoby | `tbbui.settlementpanel.render_settlement_panel(world)`: `data-settlement-panel` z wierszem `data-settlement-row`/`data-owner`/`data-wheat`/`data-gold` na osadę (kolejność `world.regions`) + tekst `<name> (<owner>): pszenica W, złoto G`. |
| K22.1b | Panel osad — populacja/garnizon | Wiersz osady dokłada `data-population`/`data-free`/`data-garrison` i tekst `· populacja P (wolne F), garnizon N`. |
| K22.1c | Panel osad w stronie | `render_game_page` osadza kanoniczny `render_settlement_panel(world)` w `<body>`. |
| K22.2a | Panel party — siła | `tbbui.partypanel.render_party_panel(world)`: `data-party-panel` z wierszem `data-party-row`/`data-owner`/`data-size` na party + tekst `<region> (<owner>): bohater + N podkomendnych`. |
| K22.2b | Panel party w stronie | `render_game_page` osadza kanoniczny `render_party_panel(world)` w `<body>`. |
| K23.1a | Legenda właścicieli | `tbbui.ownerlegend.render_owner_legend(world)`: fragment `data-owner-legend` z wierszem `data-owner-legend-row`/`data-owner`/`data-color` na właściciela (kolejność `owner_palette`) + tekst `<owner>: <kolor>`. |
| K23.1b | Legenda w stronie | `render_game_page` osadza kanoniczny `render_owner_legend(world)` w `<body>`. |
| K23.2a | Oznaczenie gracza w stronie | `render_game_page(..., player_duchy_id=None)`: dopasowane `data-duchy` dostaje `data-player-duchy=""` + prefiks `» `; `None` → bajt-w-bajt jak wcześniej. |
| K23.2b | Przewleczenie gracza z GameApp | `GameApp._render` woła `render_game_page(..., player_duchy_id=self.player_duchy_id)`; `data-player`/routing bez zmian. |
| K23.3a | Panel osad — osady gracza | `render_settlement_panel(world, player_duchy_id=None)`: wiersze z `owner_id == player_duchy_id` dostają `data-player-owned=""`; `None` → bajt-w-bajt jak wcześniej; atrybuty/tekst K22.1 bez zmian. |
| K23.3b | Panel osad w stronie z graczem | `render_game_page` woła `render_settlement_panel(world, player_duchy_id)`; `None` → bajt-w-bajt jak wcześniej. |
| K24.1a | Panel party — party gracza | `render_party_panel(world, player_duchy_id=None)`: wiersze z `owner_id == player_duchy_id` dostają `data-player-owned=""`; `None` → bajt-w-bajt jak wcześniej; atrybuty/tekst K22.2 bez zmian. |
| K24.1b | Panel party w stronie z graczem | `render_game_page` woła `render_party_panel(world, player_duchy_id)`; `None` → bajt-w-bajt jak wcześniej. |
| K24.2a | Legenda — kolor gracza | `render_owner_legend(world, player_duchy_id=None)`: wiersz z `owner_id == player_duchy_id` dostaje `data-player-owner=""` + prefiks `» `; `None` → bajt-w-bajt jak wcześniej; paleta/kolejność/atrybuty K23.1a bez zmian. |
| K24.2b | Legenda w stronie z graczem | `render_game_page` woła `render_owner_legend(world, player_duchy_id)`; `None` → bajt-w-bajt jak wcześniej. |
| K25.0 | Siła bojowa w panelach | Panele prezentacji agregują siłę bojową sekwencji `Unit` jako HP=Σ`hp`, atak=Σ`damage`, obrona=Σ`defense`; party po bohaterze+podkomendnych, osada po garnizonie. |
| K25.1a | Panel party — HP | `render_party_panel`: wiersz party dokłada `data-hp` (Σ`Unit.hp` po `[hero, *units]`) + sufiks tekstu ` · siła: HP H`. |
| K25.1b | Panel party — atak/obrona | Wiersz party dokłada `data-attack` (Σ`damage`) / `data-defense` (Σ`defense`) + sufiks `, atak A, obrona D`. |
| K25.2a | Panel osad — HP garnizonu | `render_settlement_panel`: wiersz osady dokłada `data-garrison-hp` (Σ`Unit.hp` po garnizonie; pusty → 0) + sufiks ` · siła garnizonu: HP H`. |
| K25.2b | Panel osad — atak/obrona garnizonu | Wiersz osady dokłada `data-garrison-attack` (Σ`damage`) / `data-garrison-defense` (Σ`defense`) + sufiks `, atak A, obrona D`. |
| R25.1 | Helper agregacji siły | Wspólny czysty helper `tbbui` liczący `(hp, attack, defense)` sekwencji `Unit`, reużyty przez panel party i osad; HTML bez zmian. |
| K26.1a | Panel osad — liczba budynków | `render_settlement_panel`: wiersz osady dokłada `data-buildings` (`len(active_buildings)`) + sufiks ` · budynki: N`. |
| K26.1b | Panel osad — nazwy budynków | Wiersz osady dokłada `data-building-names` (nazwy `active_buildings` złączone `", "`, pusty → `""`); przy N>0 tekst dostaje ` (nazwa1, nazwa2)`. |
| K26.2a | Wiersz księstwa — bohater | `render_game_page`: element `data-duchy` dokłada `data-hero` (`"true"`/`"false"` z `duchy.has_hero`) + tekst `, bohater tak|nie` po `morale K`. |
| K26.2b | Wiersz księstwa — dziedzic | Element `data-duchy` dokłada `data-heir` (`"true"`/`"false"` z `duchy.heir is not None`) + tekst `, dziedzic tak|nie` po części o bohaterze. |
| K27.1a | Panel party — ranni | `render_party_panel`: wiersz party dokłada `data-wounded` (liczba jednostek spośród `(hero, *units)` z niepustą `wounds`) + sufiks tekstu ` · ranni: W`. |
| K27.2a | Panel osad — ranni w garnizonie | `render_settlement_panel`: wiersz osady dokłada `data-garrison-wounded` (liczba jednostek garnizonu z niepustą `wounds`) + sufiks tekstu ` · ranni: W` po budynkach. |
| R27.1 | Helper licznika rannych | Wspólny czysty helper `tbbui.unitstrength.wounded_count` liczący jednostki z niepustą `wounds`; reużyty przez panel party i osad; HTML bez zmian. |
| K27.3a | Nagłówek sekcji osad | `render_game_page` emituje `<h2 data-panel-section="settlements">Osady</h2>` bezpośrednio przed osadzonym panelem osad; panele i reszta strony bez zmian w treści. |
| K27.3b | Nagłówki sekcji party i księstw | `render_game_page` emituje `<h2 data-panel-section="parties">Oddziały</h2>` bezpośrednio przed panelem party oraz `<h2 data-panel-section="duchies">Księstwa</h2>` bezpośrednio przed pierwszym wierszem `data-duchy`; kolejność nagłówków: settlements, parties, duchies. |
| K28.1a | Slot komunikatu rozkazu | `GameApp.last_notice: str = ""`; `_render` dokłada do extras `<p data-notice="{escape(last_notice)}"></p>`; świeży GET → pusty atrybut; treść z rozkazów w kolejnych kamieniach. |
| K28.1b | Skutek recruit/muster/develop | `_apply_player_order(transition, label=None)` przy podanym `label` ustawia `last_notice` na `{label}: wykonano` / `{label}: brak zmian` (w tym guardy); etykiety: Rekrutacja / Zebranie oddziału / Rozbudowa; marsz bez `label` — `last_notice` bez zmian (K28.1c). |
| K28.1c | Skutek marszu z celem | `POST /order/march` przez `_apply_player_order`: znany `target` → etykieta `Marsz do {region.name}`, brak/pusty/nieznany → `Marsz`; prymitywy bez zmian. |
| K28.1d | Skutek szturmu/starcia | `_apply_player_assault_order(transition, label)` ustawia `last_notice` na `{label}: bitwa` / `{label}: brak zmian` (w tym guardy); assault: `Szturm na {name}` / `Szturm`; engage: `Starcie z {name}` / `Starcie`. |
| K28.1e | Komunikat następnej tury | `POST /turn` ustawia `last_notice` na `Następna tura: rok Y, miesiąc M` (data kalendarza po turze) albo `Następna tura: gra zakończona` gdy `is_over` przed żądaniem; `last_battle` zerowane jak dotąd. |
| K29.1a | Widoczny komunikat rozkazu | `GameApp._render` renderuje tę samą escapowaną wartość `last_notice` w atrybucie i w ciele akapitu (`<p data-notice="…">…</p>`); pusty komunikat → puste ciało. |
| K29.2a | Polskie przyciski tury/rozwoju | Etykiety `<button>` formularzy `/turn` i `/order/recruit|muster|develop` zlokalizowane: `Następna tura` / `Rekrutuj` / `Zbierz oddział` / `Rozbuduj osadę`; `action` i routing bez zmian. |
| K29.2b | Polskie bare przyciski walki | Etykiety bare `<button>` formularzy `/order/march|assault|engage` zlokalizowane: `Marsz` / `Szturm` / `Starcie`; przyciski celów nadal pokazują `region.name`. |
| R29.1 | Wspólny guard gracza | `GameApp._resolve_player_duchy() -> Duchy | None` scala guard is_over/brak id/nieobecne księstwo; reużyty przez oba `_apply_*`; zachowanie bez zmian. |
| K30.1a | Sekcja „Rozwój" nad rozkazami | `GameApp._render` emituje `<h2 data-order-section="develop">Rozwój</h2>` bezpośrednio przed formularzem `/order/recruit`; kolejność sekcji develop→march→assault→engage; formularze/routing bez zmian. |
| K30.2a | Koszt złota na przycisku rekrutacji | Etykieta przycisku `/order/recruit` = `Rekrutuj (koszt złota: N)`, gdzie N z `tbb.settlement.RECRUIT_GOLD_COST` (import stałej, bez literału w szablonie); routing bez zmian. |
| K30.3a | Podsumowanie księstwa — gospodarka | `tbbui.playersummary.render_player_summary(game, player_duchy_id=None)` → `<div data-player-summary>` z `data-settlements`/`data-parties`/`data-gold`/`data-wheat` (sumy po księstwie gracza) + tekst `Twoje księstwo: osady N, oddziały M · pszenica W, złoto G`; brak gracza / spoza `game.duchies` → pusty korzeń. |
| K30.3b | Podsumowanie księstwa — siła | `render_player_summary` dokłada `data-hp`/`data-attack`/`data-defense` z `combat_totals` po wszystkich party gracza + sufiks ` · siła oddziałów: HP H, atak A, obrona D`; brak gracza → pusty korzeń jak K30.3a. |
| K30.3c | Podsumowanie w stronie partii | `render_game_page` przy `player_duchy_id is not None` osadza kanoniczny `render_player_summary(game, player_duchy_id)` w `<body>`; `None` → wynik bajt-w-bajt jak dotąd. |
| K31.1a | Restart partii `POST /new` | `GameApp` z opcjonalnym `seed`; `POST /new` przy `seed` buduje świeżą `create_headless_game()` + `Rng(seed)` + `Calendar()`, zeruje `last_battle`, `last_notice` = `Nowa gra: rok 1, miesiąc 1`; `seed None` → no-op, `last_notice` = `Nowa gra: brak zmian`. |
| K31.1b | Przycisk „Nowa gra" | `GET /` emituje `<form action="/new">` z przyciskiem „Nowa gra" przed `/turn`, niezależnie od stanu gry i gracza. |
| K31.1c | Seed w CLI serve | `python -m tbbui serve` konstruuje `GameApp(..., seed=HEADLESS_SEED)`, by `POST /new` odtwarzał deterministyczną partię. |
| K31.2a | Wynik z perspektywy gracza | `render_game_page` przy `player_duchy_id is not None` dokłada `<p data-player-result-text>`: `Gra w toku` / `Zwycięstwo Twojego księstwa` / `Porażka Twojego księstwa` / `Remis`; `None` → nieobecny (bajt-w-bajt jak dotąd). |
| K32.1a | Tytuł dokumentu strony partii | `render_game_page` emituje `<head><title>Total Battle Brothers</title></head>` bezpośrednio przed `<body>`; tytuł stały, niezależny od `player_duchy_id` / `battle`. |
| K32.1b | Widoczny nagłówek strony | `render_game_page`: pierwszym dzieckiem `<body>` jest `<h1 data-page-title="">Total Battle Brothers</h1>` (przed SVG mapy); stały, niezależny od `player_duchy_id` / `battle`. |
| K32.1c | Linia celu gry | `render_game_page` po h1 i przed SVG mapy emituje stały `<p data-objective="…">…</p>` (`_OBJECTIVE_TEXT`; atrybut = ciało); niezależny od `player_duchy_id` / `game` / `battle`. |
| K32.2a | Ukrycie tury i rozkazów po końcu | Przy `game.is_over` `GET /` (`_render`) emituje tylko `data-player`, `data-notice` i formularz `/new`; bez `/turn`, bez `/order/*` i bez `data-order-section`; routing POST bez zmian. |
| K33.1a | Panel postępu do celu (licznik wrogów) | `tbbui.victoryprogress.render_victory_progress(game, player_duchy_id=None)` → `<div data-victory-progress>`; przy graczu w `game.duchies` niesie `data-enemies-remaining="N"` (`N` = wrogowie z `not is_defeated`) + tekst „Wrogów do pokonania: N"; `None`/spoza gry → pusty korzeń. |
| K33.1b | Wiersze per-wróg | `render_victory_progress` dokłada dziecko `<div data-enemy-duchy="<id>" data-settlements data-hero>` na wrogie księstwo (kolejność `game.duchies`) + tekst „`<id>`: osady N, bohater tak\|nie". |
| K33.1c | Osadzenie postępu w stronie | `render_game_page` przy `player_duchy_id is not None` osadza jeden `render_victory_progress(game, player_duchy_id)` (zaraz po `render_player_summary`); `None` → bajt-w-bajt jak dotąd. |
| K33.2a | Oznaczenie pokonanego wroga | Wiersz `data-enemy-duchy` niesie `data-defeated="true\|false"` (z `is_defeated`); tekst pokonanego wroga ma sufiks „ — pokonany". |
| K34.1a | Podpowiedź następnego kroku | `tbbui.nextobjective.render_next_objective(game, player_duchy_id=None)` → `<p data-next-objective="TEXT">TEXT</p>` (atrybut=ciało, `html.escape(quote=True)`); `None`/spoza gry → pusty; inaczej: wszyscy wrogowie pokonani / pozostałe osady S / dobicie bohaterów H. |
| K34.1b | Osadzenie podpowiedzi w stronie | `render_game_page` przy `player_duchy_id is not None` osadza jeden `render_next_objective(game, player_duchy_id)` zaraz po `render_victory_progress`; `None` → bajt-w-bajt jak dotąd. |
| K35.1a | Lokator wrogiego bohatera | `tbbui.herolocator.render_enemy_hero_locator(world, game, player_duchy_id=None)` → `<div data-hero-locator>`; przy graczu w grze: `data-heroes-on-map` + wiersze `data-enemy-duchy`/`data-hero-region` per wróg z `has_hero` (region z `world.regions`+`party_at`, inaczej „niewystawiony"); `None`/spoza gry → pusty korzeń. |
| K35.1b | Osadzenie lokatora w stronie | `render_game_page` przy `player_duchy_id is not None` osadza jeden `render_enemy_hero_locator(world, game, player_duchy_id)` zaraz po `render_next_objective`; `None` → bajt-w-bajt jak dotąd. |
| K36.1a | Dystans w grafie regionów | `tbb.ai.region_distance(world, start, target)` → liczba krawędzi najkrótszej ścieżki BFS po `world.neighbors` (surowy dystans, nie omija party); `start==target`→0, brak drogi→`None`, region spoza mapy→`ValueError`; nie mutuje. |
| K36.1b | Panel pościgu za bohaterem | `tbbui.herochase.render_hero_chase(world, game, player_duchy_id=None)` → `<div data-hero-chase>`; przy graczu w grze `data-player-on-map` + wiersze `data-enemy-duchy`/`data-distance` (z `ai.region_distance` od party gracza) na wroga z `has_hero` i party na mapie; `None`/spoza gry → pusty korzeń. |
| K36.1c | Osadzenie pościgu w stronie | `render_game_page` przy `player_duchy_id is not None` osadza jeden `render_hero_chase(world, game, player_duchy_id)` zaraz po `render_enemy_hero_locator`; `None` → bajt-w-bajt jak dotąd. |
| K36.2a | Oznaczenie celu w zasięgu | `render_hero_chase`: wiersz o `data-distance="1"` dostaje `data-in-reach=""` i sufiks „ — w zasięgu"; inne dystanse bez oznaczenia. |
| K37.1a | Podgląd siły celu szturmu | `tbbui.engagementpreview.render_engagement_preview(world, game, player_duchy_id=None)` → `<div data-engagement-preview>`; przy party gracza `data-player-on-map` + `data-own-*` (siła party) + wiersze per sąsiednia wroga osada (`data-target-kind="settlement"`, `data-enemy-*` = siła garnizonu); brak gracza/party → pusty korzeń / `data-player-on-map="false"`. |
| K37.1b | Flaga przewagi celu | Wiersz podglądu starcia dostaje `data-advantage="true"` gdy suma własnych statystyk ≥ suma statystyk celu, inaczej `"false"`; sufiks tekstowy „ — przewaga" / „ — niekorzystnie". |
| K37.1c | Osadzenie podglądu starcia | `render_game_page` przy `player_duchy_id is not None` osadza jeden `render_engagement_preview(world, game, player_duchy_id)` zaraz po `render_hero_chase`; `None` → bajt-w-bajt jak dotąd. |
| K37.2a | Sąsiednie wrogie party jako cele | `render_engagement_preview` dokłada wiersze `data-target-kind="party"` (siła = `combat_totals(hero+units)`); w regionie z osadą i party wiersz osady poprzedza party; reguła przewagi wspólna z osadami. |
| R37.1 | Wspólny helper lokalizacji party | `tbbui.maplookup.first_party_region(world, owner_id) -> Region | None` (pierwszy region z `party_at.owner_id == owner_id`); reużyty przez `herolocator`/`herochase`/`engagementpreview`; refaktor bez zmiany zachowania. |
| R38.1 | Wspólny helper lokalizacji księstwa gracza | `tbbui.gamelookup.player_duchy(game, player_duchy_id) -> Duchy | None` (`None` gdy id `None`/brak w `game.duchies`); reużyty przez `playersummary`/`nextobjective`/`victoryprogress`/`herolocator`/`herochase`/`engagementpreview`; refaktor bez zmiany zachowania. |
| K38.1a | Prymityw flagi zmian po turze | `tbbui.turnsummary.render_turn_summary(before, after)` → `<div data-turn-summary>`; `before is None` → pusty korzeń; przy `GameState` `data-changed="true|false"` (różnica `len(settlements)`/`has_hero` po `duchy_id`) + tekst „Zmiany w tej turze: tak|nie"; bez wierszy per-księstwo. |
| K38.1b | Wiersze per-księstwo w podsumowaniu tury | Przy `before` = `GameState` korzeń dostaje `data-change-count` i po jednym `<div data-turn-duchy>` na zmienione księstwo (kolejność `after.duchies`: osady/bohater przed→po); bez zmian → count 0, bez dzieci; `before is None` nadal sam pusty korzeń. |
| K38.1c | Osadzenie podsumowania tury w stronie | `render_game_page(..., previous_game=None)` przy `previous_game is not None` osadza jeden `render_turn_summary(previous_game, game)` zaraz po `data-calendar` (niezależnie od `player_duchy_id`); `None` → bajt-w-bajt jak dotąd. |
| K38.2a | GameApp previous_game | `GameApp.previous_game`; `POST /turn` (nie is_over) = stan sprzed tury; `/new`, `/order/*`, no-op turn → `None`; `_render` → `render_game_page(..., previous_game=...)`. |
| K39.1a | Prymityw alertu zagrożeń (korzeń + licznik) | `tbbui.threatalert.render_threat_alert(world, game, player_duchy_id=None)` → `<div data-threat-alert="">`; `player_duchy(...) is None` → pusty korzeń; przy znanym graczu `data-threats="N"` i tekst „Zagrożone pozycje: N” (osada/party osobno, sąsiad z jawnym wrogim `owner_id`; bez dzieci). |
| K39.1b | Wiersze per zagrożona pozycja | Przy znanym graczu po jednym `<div data-threatened-region data-threatened-kind data-enemy-region data-enemy-owner>` (kolejność `world.regions`, osada przed party; wróg = pierwsze sąsiednie party z jawnym `owner_id != player`; tekst Osada/Oddział; `data-threats` = liczba wierszy). |
| K39.1c | Osadzenie panelu zagrożeń w stronie | `render_game_page` przy `player_duchy_id is not None` osadza jeden `render_threat_alert(world, game, player_duchy_id)` zaraz po `render_engagement_preview` (przed wierszami `data-duchy`); `None` → bajt-w-bajt jak dotąd. |
| K39.2a | Siła obronna i wroga w wierszu zagrożenia | Wiersz `data-threatened-region` dostaje `data-own-*` / `data-enemy-*` z `combat_totals` (garnizon / party / wróg) oraz sufiks tekstu „ · siła obronna: … · siła wroga: …”; reużycie `tbbui.unitstrength.combat_totals`. |
| K39.2b | Flaga obrony pozycji (defensible) | Po `data-enemy-defense`: `data-defensible="true|false"` gdy own_sum (Ho+Ao+Do) ≥ enemy_sum; tekst kończy się „ — obronisz się” / „ — przewaga wroga”. |
| R39.1 | Wspólny predykat wrogiego party | `tbbui.maplookup.is_hostile_owner(owner_id, player_duchy_id) -> bool` = `owner_id is not None and owner_id != player_duchy_id`; reużyty przez `threatalert`/`engagementpreview`; refaktor bez zmiany zachowania/HTML. |
| K40.1a | Prymityw skrótu sytuacji | `tbbui.situationreport.render_situation_report(world, game, player_duchy_id=None)` → `<div data-situation-report>`; `player_duchy(...) is None` → pusty korzeń; przy graczu `data-threatened-count="N"` (przez `threatalert.threatened_position_count`, wspólne źródło z `render_threat_alert`) + tekst „Sytuacja: zagrożone pozycje N". |
| K40.1b | Licznik korzystnych celów | `render_situation_report` dokłada `data-opportunity-count="M"` = liczba sąsiednich wrogich celów party gracza z przewagą (`engagementpreview.advantageous_target_count`, reguła `own_sum >= enemy_sum`); tekst „Sytuacja: zagrożone pozycje N, korzystne cele M". |
| K40.1c | Osadzenie skrótu sytuacji | `render_game_page` przy `player_duchy_id is not None` osadza jeden `render_situation_report(world, game, player_duchy_id)` zaraz po `render_threat_alert`; `None` → bajt-w-bajt jak dotąd. |
| K40.2a | Flaga postawy w skrócie | `render_situation_report` dokłada `data-net-posture`: `"offensive"` gdy M>N, `"defensive"` gdy N>M, `"balanced"` gdy M==N; sufiks tekstu „ — postawa: ofensywna\|defensywna\|zrównoważona". |
| K41.1a | Prymityw zalecanego rozkazu | `tbbui.recommendedaction.render_recommended_action` → `<div data-recommended-action>`; `player_duchy(...) is None` → pusty korzeń; przy graczu `data-posture` z publicznego `situationreport.net_posture(M, N)` + tekst „Zalecany rozkaz: atakuj|broń się|rozwijaj księstwo". |
| K41.1b | Ofensywa wskazuje cel | `first_advantageous_target` → `(region, kind)` pierwszego korzystnego sąsiada (kolejność jak `advantageous_target_count`); przy `data-posture="offensive"` tekst „szturmuj osadę <region>" / „zaatakuj oddział <region>". |
| K41.1c | Defensywa wskazuje pozycję | `first_threatened_region` → nazwa regionu pierwszej zagrożonej własnej pozycji (kolejność jak `threatened_position_count`); przy `data-posture="defensive"` tekst „broń pozycji <region>". |
| K41.2a | Maszynowa flaga rozkazu | `render_recommended_action` dokłada `data-action` zaraz po `data-posture`: ofensywna+settlement → `assault`, ofensywna+party → `engage`, defensywna → `defend`, zrównoważona → `develop`. |
| K41.3a | Osadzenie zalecanego rozkazu | `render_game_page` przy `player_duchy_id is not None` osadza jeden `render_recommended_action(world, game, player_duchy_id)` zaraz po `render_situation_report`; `None` → bajt-w-bajt jak dotąd. |
| K42.1a | Prymityw `recommended_order` | `tbbui.recommendedaction.recommended_order(world, game, player_duchy_id)` → `(action, target_region\|None)` \| `None`; maszynowe źródło decyzji rady (assault/engage/defend/develop), `render_recommended_action` deleguje (bajt-w-bajt jak dotąd). |
| K42.1b | Mapa akcji→ścieżka rozkazu | `tbbui.serve.recommended_order_path(action)`: assault→`/order/assault`, engage→`/order/engage`, defend→`/order/march` (obrona = marsz party do zagrożonej pozycji), develop→`/order/develop`; reużywa istniejące trasy. |
| K42.1c | Formularz zalecenia w `GET /` | GameApp osadza jeden `<form data-recommended-order>` (przed `data-order-section="develop"`) z `action=recommended_order_path` + `?target=quote(region)` gdy region; brak przy `player_duchy_id=None`/`is_over`/`recommended_order=None`. |
| K42.2a | Etykieta przycisku zalecenia | `recommendedaction.recommended_order_text(action, target)` = opisowa część rady; przycisk niesie `Wykonaj zalecenie: <opis>`, `render_recommended_action` używa go jako źródła tekstu (bajt-w-bajt jak dotąd). |
| R43.1 | Kompaktacja DESIGN §11 | `docs/DESIGN.md` §11 opisuje warstwę wizualną wyłącznie na poziomie produktu; per-funkcyjne kontrakty `data-*`/render/routing kanonicznie w `docs/ARCHITECTURE.md` (sekcja `tbbui`). |
