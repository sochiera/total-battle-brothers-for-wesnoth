extends SceneTree

const OrderResult = preload("res://scripts/order_result.gd")
const EXPECTED := {
	"changed": {"order": "develop", "changed": true},
	"unchanged": {"order": "develop", "changed": false},
	# G91.2b: from_response musi przenieść game_over z mostu (UI może czytać flagę wprost).
	"game_over_order": {"order": "recruit", "changed": false, "game_over": true},
	# G114.1c: most (task-636) niesie pole ``reason`` z rdzenia — projekcja musi
	# je przenieść (wzorzec K111 / ``blocked_region``), żeby status_text miał z
	# czego czytać powód odmowy.
	"recruit_reason_transient": {"order": "recruit", "changed": false, "reason": "brak wolnej ludności"},
	"recruit_reason_permanent": {"order": "recruit", "changed": false, "reason": "brak wolnej ludności — osada nie wyżywi przyrostu"},
	"recruit_reason_unknown": {"order": "recruit", "changed": false, "reason": "nieznany defekt xyz"},
	# G114.1c: most niesie ``reason`` także dla ``develop`` i ``muster``
	# (test_protocol.py); ``_reason_status_text`` używa ``ORDER_REASON_STATUS_PL`` do
	# białej-listy wszystkich trzech rozkazów gospodarczych, więc probe musi
	# pilnować warunku.
	"develop_reason_transient": {"order": "develop", "changed": false, "reason": "brak wolnej ludności"},
	"muster_reason_transient": {"order": "muster", "changed": false, "reason": "brak wolnej ludności"},
	"battle": {"kind": "battle", "order": "assault", "outcome": "porażka", "attacker_losses": 0, "defender_losses": 0},
	"battle_from_wire": {"kind": "battle", "order": "assault", "outcome": "zwycięstwo", "attacker_losses": 0, "defender_losses": 2},
	"battle_unresolved": {"kind": "battle", "order": "assault", "outcome": "nierozstrzygnięta", "attacker_losses": 0, "defender_losses": 0},
	"engage_battle": {"kind": "battle", "order": "engage", "outcome": "porażka", "attacker_losses": 1, "defender_losses": 0},
	"engage_unchanged": {"order": "engage", "changed": false},
	"march_blocked": {"order": "march", "changed": false, "blocked_region": "border"},
	"move_blocked": {"order": "move", "changed": false, "blocked_region": "border"},
	"move_blocked_missing_region": {"order": "move", "changed": false},
	"move_blocked_invalid_region": {"order": "move", "changed": false},
	"move_blocked_unknown_region": {"order": "move", "changed": false, "blocked_region": "unknown-region"},
	"missing_ok": null,
	"not_ok": null,
	"missing_result": null,
	"turn_result": null,
	"save_result": null,
	"snapshot_result": null,
	"new_game_result": null,
	"missing_order": null,
	"invalid_order": null,
	"missing_changed": null,
	"invalid_changed": null,
	"battle_missing_outcome": null,
	"battle_missing_order": null,
	"battle_invalid_order": null,
	"battle_invalid_outcome": null,
	"battle_missing_attacker_losses": null,
	"battle_missing_defender_losses": null,
	"battle_invalid_attacker_losses": null,
	"battle_invalid_defender_losses": null,
	"battle_fractional_losses_from_wire": null,
}

func _init() -> void:
	var battle_from_wire: Variant = JSON.parse_string("{\"ok\":true,\"result\":{\"kind\":\"battle\",\"order\":\"assault\",\"outcome\":\"zwycięstwo\",\"attacker_losses\":0,\"defender_losses\":2}}")
	var battle_fractional_losses_from_wire: Variant = JSON.parse_string("{\"ok\":true,\"result\":{\"kind\":\"battle\",\"order\":\"assault\",\"outcome\":\"remis\",\"attacker_losses\":1.5,\"defender_losses\":0}}")
	var cases := {
		"changed": {"ok": true, "result": {"kind": "order", "order": "develop", "changed": true}},
		"unchanged": {"ok": true, "result": {"kind": "order", "order": "develop", "changed": false}},
		"game_over_order": {
			"ok": true,
			"result": {"kind": "order", "order": "recruit", "changed": false, "game_over": true},
		},
		"recruit_reason_transient": {"ok": true, "result": {"kind": "order", "order": "recruit", "changed": false, "reason": "brak wolnej ludności"}},
		"recruit_reason_permanent": {"ok": true, "result": {"kind": "order", "order": "recruit", "changed": false, "reason": "brak wolnej ludności — osada nie wyżywi przyrostu"}},
		"recruit_reason_unknown": {"ok": true, "result": {"kind": "order", "order": "recruit", "changed": false, "reason": "nieznany defekt xyz"}},
		"develop_reason_transient": {"ok": true, "result": {"kind": "order", "order": "develop", "changed": false, "reason": "brak wolnej ludności"}},
		"muster_reason_transient": {"ok": true, "result": {"kind": "order", "order": "muster", "changed": false, "reason": "brak wolnej ludności"}},
		"missing_ok": {"result": {"kind": "order", "order": "develop", "changed": true}},
		"not_ok": {"ok": false, "result": {"kind": "order", "order": "develop", "changed": true}},
		"missing_result": {"ok": true},
		"turn_result": {"ok": true, "result": {"kind": "turn", "date": {}}},
		"save_result": {"ok": true, "result": {"kind": "save", "path": "state.json"}},
		"snapshot_result": {"ok": true, "result": {"kind": "snapshot", "state": {}}},
		"new_game_result": {"ok": true, "result": {"kind": "new_game", "state": {}}},
		"missing_order": {"ok": true, "result": {"kind": "order", "changed": true}},
		"invalid_order": {"ok": true, "result": {"kind": "order", "order": 1, "changed": true}},
		"missing_changed": {"ok": true, "result": {"kind": "order", "order": "develop"}},
		"invalid_changed": {"ok": true, "result": {"kind": "order", "order": "develop", "changed": "yes"}},
		"battle": {"ok": true, "result": {"kind": "battle", "order": "assault", "outcome": "porażka", "attacker_losses": 0, "defender_losses": 0}},
		"battle_from_wire": battle_from_wire,
		"battle_unresolved": {"ok": true, "result": {"kind": "battle", "order": "assault", "outcome": "nierozstrzygnięta", "attacker_losses": 0, "defender_losses": 0}},
		"engage_battle": {"ok": true, "result": {"kind": "battle", "order": "engage", "outcome": "porażka", "attacker_losses": 1, "defender_losses": 0}},
		"engage_unchanged": {"ok": true, "result": {"kind": "order", "order": "engage", "changed": false}},
		"march_blocked": {"ok": true, "result": {"kind": "order", "order": "march", "changed": false, "blocked_region": "border"}},
		"move_blocked": {"ok": true, "result": {"kind": "order", "order": "move", "changed": false, "blocked_region": "border"}},
		"move_blocked_missing_region": {"ok": true, "result": {"kind": "order", "order": "move", "changed": false}},
		"move_blocked_invalid_region": {"ok": true, "result": {"kind": "order", "order": "move", "changed": false, "blocked_region": 42}},
		"move_blocked_unknown_region": {"ok": true, "result": {"kind": "order", "order": "move", "changed": false, "blocked_region": "unknown-region"}},
		"battle_missing_outcome": {"ok": true, "result": {"kind": "battle", "order": "assault", "attacker_losses": 0, "defender_losses": 0}},
		"battle_missing_order": {"ok": true, "result": {"kind": "battle", "outcome": "porażka", "attacker_losses": 0, "defender_losses": 0}},
		"battle_invalid_order": {"ok": true, "result": {"kind": "battle", "order": 1, "outcome": "porażka", "attacker_losses": 0, "defender_losses": 0}},
		"battle_invalid_outcome": {"ok": true, "result": {"kind": "battle", "order": "assault", "outcome": 1, "attacker_losses": 0, "defender_losses": 0}},
		"battle_missing_attacker_losses": {"ok": true, "result": {"kind": "battle", "order": "assault", "outcome": "porażka", "defender_losses": 0}},
		"battle_missing_defender_losses": {"ok": true, "result": {"kind": "battle", "order": "assault", "outcome": "porażka", "attacker_losses": 0}},
		"battle_invalid_attacker_losses": {"ok": true, "result": {"kind": "battle", "order": "assault", "outcome": "porażka", "attacker_losses": "0", "defender_losses": 0}},
		"battle_invalid_defender_losses": {"ok": true, "result": {"kind": "battle", "order": "assault", "outcome": "porażka", "attacker_losses": 0, "defender_losses": false}},
		"battle_fractional_losses_from_wire": battle_fractional_losses_from_wire,
	}
	var projected: Dictionary = {}
	for name: String in cases:
		projected[name] = OrderResult.from_response(cases[name])
	if projected != EXPECTED:
		printerr("order_result_probe: projection did not match the contract")
		call_deferred("quit", 1)
		return
	var status_cases: Dictionary = {
		"develop_changed": projected["changed"],
		"develop_unchanged": projected["unchanged"],
		"recruit_changed": OrderResult.from_response({"ok": true, "result": {"kind": "order", "order": "recruit", "changed": true}}),
		"recruit_unchanged": OrderResult.from_response({"ok": true, "result": {"kind": "order", "order": "recruit", "changed": false}}),
		"muster_changed": OrderResult.from_response({"ok": true, "result": {"kind": "order", "order": "muster", "changed": true}}),
		"muster_unchanged": OrderResult.from_response({"ok": true, "result": {"kind": "order", "order": "muster", "changed": false}}),
		"reinforce_changed": OrderResult.from_response({"ok": true, "result": {"kind": "order", "order": "reinforce", "changed": true}}),
		"reinforce_unchanged": OrderResult.from_response({"ok": true, "result": {"kind": "order", "order": "reinforce", "changed": false}}),
		"reinforce_exhausted": OrderResult.from_response({"ok": true, "result": {"kind": "order", "order": "reinforce", "changed": false}}, true),
		# The exhausted-month wording requires the bridge's explicit context.
		"assault_unchanged": OrderResult.from_response({"ok": true, "result": {"kind": "order", "order": "assault", "changed": false}}, true),
		"assault_unchanged_default": OrderResult.from_response({"ok": true, "result": {"kind": "order", "order": "assault", "changed": false}}),
		"assault_reason_no_own_party": OrderResult.from_response({"ok": true, "result": {"kind": "order", "order": "assault", "changed": false, "reason": "brak własnego oddziału"}}),
		"assault_reason_no_enemy_in_reach": OrderResult.from_response({"ok": true, "result": {"kind": "order", "order": "assault", "changed": false, "reason": "brak wrogiej osady w zasięgu"}}),
		"assault_reason_out_of_reach": OrderResult.from_response({"ok": true, "result": {"kind": "order", "order": "assault", "changed": false, "reason": "cel poza zasięgiem"}}),
		"assault_reason_no_enemy_at_target": OrderResult.from_response({"ok": true, "result": {"kind": "order", "order": "assault", "changed": false, "reason": "brak wrogiej osady w celu"}}),
		"assault_reason_already_acted": OrderResult.from_response({"ok": true, "result": {"kind": "order", "order": "assault", "changed": false, "reason": "oddział już działał w tym miesiącu"}}),
		"assault_reason_unknown": OrderResult.from_response({"ok": true, "result": {"kind": "order", "order": "assault", "changed": false, "reason": "nieznany wojskowy powód"}}),
		"assault_reason_empty": OrderResult.from_response({"ok": true, "result": {"kind": "order", "order": "assault", "changed": false, "reason": ""}}),
		"move_changed": OrderResult.from_response({"ok": true, "result": {"kind": "order", "order": "move", "changed": true}}),
		"move_unchanged": OrderResult.from_response({"ok": true, "result": {"kind": "order", "order": "move", "changed": false}}),
		"march_blocked": projected["march_blocked"],
		"move_blocked": projected["move_blocked"],
		"move_changed_with_blocker": {"order": "move", "changed": true, "blocked_region": "border"},
		"game_over_order": OrderResult.from_response({
			"ok": true,
			"result": {"kind": "order", "order": "recruit", "changed": false, "game_over": true},
		}),
		"recruit_reason_transient": projected["recruit_reason_transient"],
		"recruit_reason_permanent": projected["recruit_reason_permanent"],
		"recruit_reason_unknown": projected["recruit_reason_unknown"],
		"develop_reason_transient": projected["develop_reason_transient"],
		"muster_reason_transient": projected["muster_reason_transient"],
		"assault_battle": projected["battle"],
		"assault_battle_from_wire": projected["battle_from_wire"],
		"assault_battle_unresolved": projected["battle_unresolved"],
		"engage_battle": projected["engage_battle"],
		"engage_unchanged": OrderResult.from_response({"ok": true, "result": {"kind": "order", "order": "engage", "changed": false}}, true),
		"engage_reason_no_own_party": OrderResult.from_response({"ok": true, "result": {"kind": "order", "order": "engage", "changed": false, "reason": "brak własnego oddziału"}}),
		"engage_reason_no_enemy_in_reach": OrderResult.from_response({"ok": true, "result": {"kind": "order", "order": "engage", "changed": false, "reason": "brak wrogiego wojska w zasięgu"}}),
		"engage_reason_out_of_reach": OrderResult.from_response({"ok": true, "result": {"kind": "order", "order": "engage", "changed": false, "reason": "cel poza zasięgiem"}}),
		"engage_reason_no_enemy_at_target": OrderResult.from_response({"ok": true, "result": {"kind": "order", "order": "engage", "changed": false, "reason": "brak wrogiego wojska w celu"}}),
		"engage_reason_already_acted": OrderResult.from_response({"ok": true, "result": {"kind": "order", "order": "engage", "changed": false, "reason": "oddział już działał w tym miesiącu"}}),
		"engage_reason_unknown": OrderResult.from_response({"ok": true, "result": {"kind": "order", "order": "engage", "changed": false, "reason": "nieznany wojskowy powód"}}),
		"engage_reason_empty": OrderResult.from_response({"ok": true, "result": {"kind": "order", "order": "engage", "changed": false, "reason": ""}}),
		"engage_unchanged_default": projected["engage_unchanged"],
		"missing_result": null,
		"non_dictionary": [],
		"missing_order": {"changed": true},
		"invalid_changed": {"order": "develop", "changed": "yes"},
		"unknown_order": {"order": "trade", "changed": true},
		# from_response rejects this shape, so pass it to status_text directly.
		"unknown_kind": {"kind": "turn", "order": "assault"},
		"deterministic": projected["changed"],
		"deterministic_muster": {"order": "muster", "changed": true},
		"move_blocked_missing_region": projected["move_blocked_missing_region"],
		"move_blocked_invalid_region": projected["move_blocked_invalid_region"],
		"move_blocked_unknown_region": projected["move_blocked_unknown_region"],
	}
	var status_text: Dictionary = {}
	for name: String in status_cases:
		status_text[name] = OrderResult.status_text(status_cases[name])
	if OrderResult.status_text(status_cases["deterministic"]) != status_text["deterministic"]:
		printerr("order_result_probe: status text was not deterministic")
		call_deferred("quit", 1)
		return
	if OrderResult.status_text(status_cases["deterministic_muster"]) != status_text["deterministic_muster"]:
		printerr("order_result_probe: muster status text was not deterministic")
		call_deferred("quit", 1)
		return
	print("ORDER_RESULT ", JSON.stringify(projected))
	print("ORDER_STATUS_TEXT ", JSON.stringify(status_text))
	call_deferred("quit", 0)
