extends SceneTree


## G116.1f measurement: targeted economic orders route through live persisted
## bridge sessions and remain visible after a serve --resume process.

const BridgeClient = preload("res://scripts/bridge_client.gd")
const MeasurementBattle = preload("res://tests/measurement_battle_helpers.gd")
const PREFIX := "TARGETED_ECONOMIC_MEASUREMENT "
const PLAYER_LANDS := "player lands"
const PLAYER_OUTPOST := "player outpost"
const FOREIGN_REGION := "border"


func _init() -> void:
	call_deferred("_run")


func _run() -> void:
	var args: PackedStringArray = OS.get_cmdline_user_args()
	if args.size() != 4:
		_fail("expected command prefix, state path, request path and seed")
		return

	var first := _measure_target(args, PLAYER_LANDS, "lands")
	var second := _measure_target(args, PLAYER_OUTPOST, "outpost")
	var foreign := _measure_foreign(args)
	var regressions := _measure_regressions(args)
	var growth := _measure_growth(args)
	if (
		first.is_empty()
		or second.is_empty()
		or foreign.is_empty()
		or regressions.is_empty()
		or growth.is_empty()
	):
		return

	print(PREFIX, JSON.stringify({
		"first": first,
		"second": second,
		"foreign": foreign,
		"regressions": regressions,
		"growth": growth,
	}))
	quit(0)


func _measure_target(args: PackedStringArray, target: String, suffix: String) -> Dictionary:
	var client := BridgeClient.create_persistent(
		args[0], args[1] + "-" + suffix + ".json", args[3].to_int(),
		args[2] + "-" + suffix + ".jsonl"
	)
	var first_model := client.send_order("recruit", target)
	var first_result: Variant = client.last_order_result()
	var second_model := client.send_order("recruit", target)
	var second_result: Variant = client.last_order_result()
	var resumed_model := client.snapshot_model()
	if first_model == null or second_model == null or resumed_model == null:
		_fail("targeted live bridge snapshot unavailable for " + target)
		return {}

	return {
		"target": target,
		"first_result": first_result,
		"second_result": second_result,
		"after": _settlements(second_model),
		"resumed": _settlements(resumed_model),
		"resumed_command": client.session_command(),
	}


func _measure_foreign(args: PackedStringArray) -> Dictionary:
	var client := BridgeClient.create_persistent(
		args[0], args[1] + "-foreign.json", args[3].to_int(),
		args[2] + "-foreign.jsonl"
	)
	var model := client.send_order("recruit", FOREIGN_REGION)
	var result: Variant = client.last_order_result()
	if model == null:
		_fail("foreign live bridge snapshot unavailable")
		return {}

	return {
		"target": FOREIGN_REGION,
		"ok": result != null,
		"result": result,
		"after": _settlements(model),
	}


func _measure_regressions(args: PackedStringArray) -> Dictionary:
	var passive := BridgeClient.create_persistent(
		args[0], args[1] + "-passive.json", args[3].to_int(),
		args[2] + "-passive.jsonl"
	)
	var passive_model: Variant = passive.snapshot_model()
	var passive_turns := 0
	while passive_model != null and passive_model.player_result == "ongoing" and passive_turns < 13:
		passive_model = passive.advance_turn()
		passive_turns += 1
	if passive_model == null:
		_fail("passive live bridge snapshot unavailable")
		return {}

	var active := BridgeClient.create_persistent(
		args[0], args[1] + "-active.json", args[3].to_int(),
		args[2] + "-active.jsonl"
	)
	var active_commands: Array = [
		{"kind": "order", "order": "recruit", "target": ""},
		{"kind": "order", "order": "recruit", "target": ""},
		{"kind": "order", "order": "muster", "target": ""},
		{"kind": "order", "order": "march", "target": ""},
		{"kind": "turn"},
		{"kind": "order", "order": "engage", "target": "border"},
		{"kind": "turn"},
		{"kind": "order", "order": "assault", "target": "ai outpost"},
		{"kind": "turn"},
		{"kind": "order", "order": "assault", "target": "ai lands"},
	]
	var active_states: Array = []
	var active_model: Variant = null
	for command: Dictionary in active_commands:
		var model: Variant
		if command.get("kind") == "turn":
			model = active.advance_turn()
		else:
			model = active.send_order(command["order"], str(command.get("target", "")))
			model = MeasurementBattle.resolve_pending_battle(active, model)
		if model == null:
			_fail("active live bridge snapshot unavailable")
			return {}
		active_model = model
		active_states.append({
			"kind": command.get("kind"),
			"order": command.get("order", "next_turn"),
			"date": _date(model),
			"result": model.player_result,
		})

	return {
		"passive": {
			"turns": passive_turns,
			"date": _date(passive_model),
			"result": passive_model.player_result,
			"resumed_command": passive.session_command(),
		},
		"active": {
			"states": active_states,
			"date": _date(active_model),
			"result": active_states[-1]["result"],
			"resumed_command": active.session_command(),
		},
	}


func _measure_growth(args: PackedStringArray) -> Dictionary:
	var client := BridgeClient.create_persistent(
		args[0], args[1] + "-growth.json", args[3].to_int(),
		args[2] + "-growth.jsonl"
	)
	for _step in 2:
		var developed: Variant = client.send_order("develop")
		if developed == null or client.last_order_result() == null:
			_fail("growth develop snapshot unavailable")
			return {}

	var drained_model: Variant = client.snapshot_model()
	if drained_model == null:
		_fail("growth drained snapshot unavailable")
		return {}
	var turn_states: Array = []
	for _step in 5:
		var model: Variant = client.advance_turn()
		if model == null:
			_fail("growth turn snapshot unavailable")
			return {}
		turn_states.append({
			"date": _date(model),
			"settlements": _settlements(model, "player"),
		})

	var after_growth: Variant = client.snapshot_model()
	var develop_after: Variant = client.send_order("develop")
	var result_after: Variant = client.last_order_result()
	if after_growth == null or develop_after == null or result_after == null:
		_fail("growth post-turn snapshot unavailable")
		return {}

	return {
		"drained": _settlements(drained_model, "player"),
		"turns": turn_states,
		"after": _settlements(after_growth, "player"),
		"order_result": result_after,
	}


func _date(model: Variant) -> Dictionary:
	return {"year": model.year, "month": model.month}


func _settlements(model: SnapshotModel, owner: String = "") -> Dictionary:
	var states := {}
	for region: Variant in model.regions:
		if not region is Dictionary:
			continue
		var name: Variant = region.get("name")
		if name != PLAYER_LANDS and name != PLAYER_OUTPOST:
			continue
		var settlement: Variant = region.get("settlement")
		if not settlement is Dictionary:
			continue
		if not owner.is_empty() and settlement.get("owner") != owner:
			continue
		states[name] = {
			"population": settlement.get("population"),
			"free": settlement.get("free"),
			"garrison": settlement.get("garrison"),
		}
	return states


func _fail(message: String) -> void:
	printerr("targeted_economic_measurement_probe: ", message)
	quit(1)
