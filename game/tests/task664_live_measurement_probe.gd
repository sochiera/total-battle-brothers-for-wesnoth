extends SceneTree


## G117.1b gate: live bridge measurements for the opening, regressions, and
## long defensive strategy.

const BridgeClient = preload("res://scripts/bridge_client.gd")
const PREFIX := "TASK664_LIVE_MEASUREMENT "
const PLAYER_LANDS := "player lands"


func _init() -> void:
	call_deferred("_run")


func _run() -> void:
	var args := OS.get_cmdline_user_args()
	if args.size() != 4:
		_fail("expected command prefix, state path, request path and seed")
		return

	var opening := _measure_opening(args)
	var passive := _measure_passive(args)
	var active := _measure_active(args)
	var defensive := _measure_defensive(args)
	if (
		opening.is_empty()
		or passive.is_empty()
		or active.is_empty()
		or defensive.is_empty()
	):
		return

	print(PREFIX, JSON.stringify({
		"opening": opening,
		"passive": passive,
		"active": active,
		"defensive": defensive,
	}))
	call_deferred("quit", 0)


func _client(args: PackedStringArray, suffix: String) -> BridgeClient:
	return BridgeClient.create_persistent(
		args[0], args[1] + "-" + suffix + ".json", args[3].to_int(),
		args[2] + "-" + suffix + ".jsonl"
	)


func _measure_opening(args: PackedStringArray) -> Dictionary:
	var client := _client(args, "opening")
	var commands: Array = [
		{"order": "develop", "target": ""},
		{"order": "develop", "target": ""},
		{"order": "recruit", "target": ""},
		{"order": "recruit", "target": ""},
		{"order": "recruit", "target": ""},
		{"order": "recruit", "target": ""},
	]
	for command: Dictionary in commands:
		if client.send_order(command["order"], command["target"]) == null:
			_fail("opening order snapshot unavailable")
			return {}

	if client.send_order("muster", PLAYER_LANDS) == null:
		_fail("opening muster snapshot unavailable")
		return {}
	var after_muster := client.snapshot_model()
	if after_muster == null:
		_fail("opening resume snapshot unavailable")
		return {}
	var after_turn := client.advance_turn()
	if after_turn == null:
		_fail("opening next-turn snapshot unavailable")
		return {}
	var after_turn_resume := client.snapshot_model()
	if after_turn_resume == null:
		_fail("opening post-turn resume snapshot unavailable")
		return {}

	return {
		"commands": commands,
		"after_muster": _settlement(after_muster, PLAYER_LANDS),
		"after_turn": _settlement(after_turn, PLAYER_LANDS),
		"after_turn_resume": _settlement(after_turn_resume, PLAYER_LANDS),
	}


func _measure_passive(args: PackedStringArray) -> Dictionary:
	var client := _client(args, "passive")
	var model := client.snapshot_model()
	var turns := 0
	while model != null and model.player_result == "ongoing" and turns < 20:
		model = client.advance_turn()
		turns += 1
	if model == null:
		_fail("passive snapshot unavailable")
		return {}
	var result := _result(client.send({"type": "snapshot"}))
	if result.is_empty():
		_fail("passive result snapshot unavailable")
		return {}
	return {
		"turns": turns,
		"date": {"year": model.year, "month": model.month},
		"player_result": model.player_result,
		"winner": result["winner"],
	}


func _measure_active(args: PackedStringArray) -> Dictionary:
	var client := _client(args, "active")
	var commands: Array = [
		{"kind": "order", "order": "recruit"},
		{"kind": "order", "order": "recruit"},
		{"kind": "order", "order": "recruit"},
		{"kind": "order", "order": "recruit"},
		{"kind": "order", "order": "recruit"},
		{"kind": "order", "order": "muster"},
		{"kind": "order", "order": "march"},
		{"kind": "turn"},
		{"kind": "order", "order": "reinforce"},
		{"kind": "turn"},
		{"kind": "order", "order": "march"},
		{"kind": "turn"},
		{"kind": "order", "order": "assault"},
		{"kind": "turn"},
		{"kind": "order", "order": "assault"},
		{"kind": "turn"},
		{"kind": "order", "order": "assault"},
	]
	var model: SnapshotModel = null
	for command: Dictionary in commands:
		if command["kind"] == "turn":
			model = client.advance_turn()
		else:
			model = client.send_order(command["order"])
		if model == null:
			_fail("active snapshot unavailable")
			return {}

	var result := _result(client.send({"type": "snapshot"}))
	if result.is_empty():
		_fail("active result snapshot unavailable")
		return {}
	return {
		"commands": commands,
		"date": {"year": model.year, "month": model.month},
		"player_result": model.player_result,
		"winner": result["winner"],
	}


func _measure_defensive(args: PackedStringArray) -> Dictionary:
	var client := _client(args, "defensive")
	var commands: Array = [
		{"kind": "order", "order": "develop"},
		{"kind": "order", "order": "develop"},
		{"kind": "order", "order": "recruit"},
		{"kind": "order", "order": "recruit"},
		{"kind": "order", "order": "recruit"},
		{"kind": "order", "order": "recruit"},
	]
	for command: Dictionary in commands:
		if client.send_order(command["order"]) == null:
			_fail("defensive order snapshot unavailable")
			return {}

	var model: SnapshotModel = null
	var turns := 0
	while turns < 20:
		model = client.advance_turn()
		if model == null:
			_fail("defensive next-turn snapshot unavailable")
			return {}
		turns += 1
		if model.player_result != "ongoing":
			break

	var result := _result(client.send({"type": "snapshot"}))
	if model == null or result.is_empty():
		_fail("defensive result snapshot unavailable")
		return {}
	return {
		"commands": commands + _turn_commands(turns),
		"turns": turns,
		"date": {"year": model.year, "month": model.month},
		"player_result": model.player_result,
		"winner": result["winner"],
		"settlements": {
			"player lands": _settlement(model, "player lands"),
			"player outpost": _settlement(model, "player outpost"),
		},
	}


func _turn_commands(turns: int) -> Array:
	var commands: Array = []
	for _step in turns:
		commands.append({"kind": "turn"})
	return commands


func _settlement(model: SnapshotModel, name: String) -> Dictionary:
	for region: Variant in model.regions:
		if not region is Dictionary or region.get("name") != name:
			continue
		var settlement: Variant = region.get("settlement")
		if settlement is Dictionary:
			return {
				"population": settlement.get("population"),
				"free": settlement.get("free"),
				"garrison": settlement.get("garrison"),
			}
	return {}


func _result(response: Variant) -> Dictionary:
	if not response is Dictionary or not response.get("ok", false):
		return {}
	var snapshot: Variant = response.get("snapshot")
	if not snapshot is Dictionary:
		return {}
	var result: Variant = snapshot.get("result")
	if not result is Dictionary or not result.has("winner"):
		return {}
	return {"winner": result.get("winner")}


func _fail(message: String) -> void:
	printerr("task664_live_measurement_probe: ", message)
	call_deferred("quit", 1)
