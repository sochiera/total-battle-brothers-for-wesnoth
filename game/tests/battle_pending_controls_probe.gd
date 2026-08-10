extends SceneTree


const MAIN_SCENE_PATH := "res://scenes/main.tscn"
const SnapshotModel = preload("res://scripts/snapshot_model.gd")
const BridgeClient = preload("res://scripts/bridge_client.gd")
const PREFIX := "BATTLE_PENDING_CONTROLS "
const ROUND_ORDERS := ["battle_advance", "battle_auto"]
const REGULAR_ORDER_BUTTONS := [
	"NextTurnButton",
	"DevelopButton",
	"RecruitButton",
	"MusterButton",
	"ReinforceButton",
	"MarchButton",
	"AssaultButton",
	"EngageButton",
]


func _init() -> void:
	call_deferred("_run")


func _run() -> void:
	var args := OS.get_cmdline_user_args()
	if args.size() == 5:
		await _run_live(args)
		return
	_run_fixture()


func _run_fixture() -> void:
	var scene := ResourceLoader.load(MAIN_SCENE_PATH) as PackedScene
	if scene == null:
		_fail("cannot load main scene")
		return
	var scene_root := scene.instantiate() as Control
	if scene_root == null:
		_fail("cannot instantiate main scene")
		return
	root.add_child(scene_root)
	await process_frame
	await process_frame

	var pending_model := SnapshotModel.from_response(_pending_response())
	var model_has_battle := pending_model != null and pending_model.battle is Dictionary
	if pending_model != null:
		scene_root.apply_model(pending_model)
	await process_frame
	await process_frame

	var battle_view := scene_root.find_child("BattleView", true, false) as Control
	var result_label := scene_root.find_child("BattleResultLabel", true, false) as Label
	var status_label := scene_root.find_child("LastOrderStatusLabel", true, false) as Label
	var pending_battle_view_visible := battle_view != null and battle_view.visible
	var pending_battle_tile_count := _battle_tile_count(battle_view)
	var pending_battle_result_text := "" if result_label == null else result_label.text
	var round_buttons := {}
	for order_name: String in ROUND_ORDERS:
		round_buttons[order_name] = _button_for_order(scene_root, order_name)

	var regular_buttons := {}
	for button_name: String in REGULAR_ORDER_BUTTONS:
		var button := scene_root.find_child(button_name, true, false) as Button
		regular_buttons[button_name] = {
			"found": button != null,
			"disabled": button != null and button.disabled,
			"text": "" if button == null else button.text,
		}

	var no_battle_model := SnapshotModel.from_response(_no_battle_response())
	if no_battle_model != null:
		scene_root.apply_model(no_battle_model)
	await process_frame
	await process_frame
	var outside_round_buttons := {}
	for order_name: String in ROUND_ORDERS:
		outside_round_buttons[order_name] = _button_state_for_order(scene_root, order_name)

	print(PREFIX, JSON.stringify({
		"pending_model_has_battle": model_has_battle,
		"battle_view_visible": pending_battle_view_visible,
		"battle_tile_count": pending_battle_tile_count,
		"battle_result_text": pending_battle_result_text,
		"pending_model_battle_hexes": pending_model.battle.get("hexes", []) if pending_model != null and pending_model.battle is Dictionary else [],
		"round_buttons": round_buttons,
		"regular_order_buttons": regular_buttons,
		"outside_round_buttons": outside_round_buttons,
		"order_status": "" if status_label == null else status_label.text,
	}))
	call_deferred("quit", 0)


func _pending_response() -> Dictionary:
	return {
		"ok": true,
		"snapshot": {
			"calendar": {"year": 1, "month": 1},
			"map": {"regions": []},
			"result": {"player_result": "ongoing"},
			"battle": {
				"result": null,
				"hexes": [
					{"q": 0, "r": 0, "terrain": "Plains", "side": "attacker", "hp": 10, "stunned": true},
					{"q": 1, "r": 0, "terrain": "Forest", "side": "defender", "hp": 8, "stunned": false},
				],
			},
		},
	}


func _no_battle_response() -> Dictionary:
	return {
		"ok": true,
		"snapshot": {
			"calendar": {"year": 1, "month": 1},
			"map": {"regions": []},
			"result": {"player_result": "ongoing"},
		},
	}


func _button_for_order(scene_root: Control, order_name: String) -> Dictionary:
	var order_bar := scene_root.find_child("OrderBarContent", true, false)
	if order_bar == null:
		return {"found": false, "text": "", "order_name": ""}
	for node: Node in order_bar.find_children("", "Button", true, false):
		var button := node as Button
		if button != null and str(button.get_meta("order_name", "")) == order_name:
			return {
				"found": true,
				"disabled": button.disabled,
				"text": button.text,
				"order_name": str(button.get_meta("order_name", "")),
			}
	return {"found": false, "disabled": false, "text": "", "order_name": ""}


func _battle_tile_count(battle_view: Control) -> int:
	if battle_view == null:
		return 0
	var count := 0
	for child: Node in battle_view.get_children():
		if child is Control and str(child.name).begins_with("HexTile_"):
			count += 1
	return count


func _fail(message: String) -> void:
	printerr("battle_pending_controls_probe: ", message)
	call_deferred("quit", 1)


func _run_live(args: PackedStringArray) -> void:
	root.size = Vector2i(1152, 648)
	var scene_root := _instantiate_scene()
	if scene_root == null:
		return
	scene_root.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	scene_root.size = Vector2(1152, 648)
	for _i in 8:
		await process_frame

	var client := BridgeClient.create_persistent(args[0], args[1], args[3].to_int(), args[2])
	scene_root.bind_client(client)
	for _i in 4:
		await process_frame

	var phase: String = args[4]
	if phase == "resume_pending":
		await _run_resumed_pending(scene_root, client, args[1])
		return

	if phase == "resume":
		print(PREFIX, JSON.stringify({
			"phase": phase,
			"state_exists": FileAccess.file_exists(args[1]),
			"resumed": _battle_observation(scene_root),
			"session_command": client.session_command(),
		}))
		quit(0)
		return
	if phase != "play" and phase != "start_pending" and phase != "continuous":
		_fail("unknown live phase: %s" % phase)
		return

	var setup_buttons: Array[String] = [
		"RecruitButton", "RecruitButton", "RecruitButton", "RecruitButton",
		"MusterButton", "MarchButton", "NextTurnButton", "EngageButton",
		"BattleAutoButton", "NextTurnButton", "NextTurnButton", "AssaultButton",
	]
	var setup_ok := true
	var setup_failed_button := ""
	for button_name: String in setup_buttons:
		if not _press_button(scene_root, button_name):
			setup_ok = false
			setup_failed_button = button_name
			break
		for _i in 3:
			await process_frame

	var pending := _battle_observation(scene_root)
	if phase == "start_pending":
		print(PREFIX, JSON.stringify({
			"phase": phase,
			"state_exists": FileAccess.file_exists(args[1]),
			"pending": pending,
			"session_command": client.session_command(),
		}))
		quit(0)
		return

	var regular_buttons := {}
	for button_name: String in REGULAR_ORDER_BUTTONS:
		regular_buttons[button_name] = _button_state(scene_root, button_name)
	var round_buttons := {}
	for order_name: String in ROUND_ORDERS:
		round_buttons[order_name] = _button_state_for_order(scene_root, order_name)
	var persistence_buttons := {}
	for button_name: String in ["SaveGameButton", "LoadGameButton", "NewGameButton"]:
		persistence_buttons[button_name] = _button_state(scene_root, button_name)

	var advance_pressed := _press_button(scene_root, "BattleAdvanceButton")
	for _i in 4:
		await process_frame
	var advance_request_types := _request_types(args[2])
	var after_advance := _battle_observation(scene_root)
	var advance_status := _label_text(scene_root, "LastOrderStatusLabel")

	var auto_pressed := _press_button(scene_root, "BattleAutoButton")
	for _i in 4:
		await process_frame
	var auto_request_types := _request_types(args[2])
	var after_auto := _battle_observation(scene_root)
	var auto_status := _label_text(scene_root, "LastOrderStatusLabel")

	var next_turn_pressed := _press_button(scene_root, "NextTurnButton")
	for _i in 4:
		await process_frame
	var next_turn_request_types := _request_types(args[2])
	var after_next_turn := _battle_observation(scene_root)

	print(PREFIX, JSON.stringify({
		"phase": phase,
		"setup_ok": setup_ok,
		"setup_failed_button": setup_failed_button,
		"state_exists": FileAccess.file_exists(args[1]),
		"pending": pending,
		"regular_buttons": regular_buttons,
		"round_buttons": round_buttons,
		"persistence_buttons": persistence_buttons,
		"pending_status": _label_text(scene_root, "LastOrderStatusLabel"),
		"advance_pressed": advance_pressed,
		"advance_request_types": advance_request_types,
		"advance_status": advance_status,
		"after_advance": after_advance,
		"auto_pressed": auto_pressed,
		"auto_request_types": auto_request_types,
		"auto_status": auto_status,
		"after_auto": after_auto,
		"next_turn_pressed": next_turn_pressed,
		"next_turn_request_types": next_turn_request_types,
		"after_next_turn": after_next_turn,
	}))
	quit(0)


func _run_resumed_pending(scene_root: Control, client: BridgeClient, state_path: String) -> void:
	var pending_before := _battle_observation(scene_root)
	var pending_model: Variant = client.snapshot_model()
	if pending_model == null or not pending_model.battle is Dictionary:
		_fail("resumed pending battle snapshot unavailable")
		return

	var blocked_before_date := {
		"year": pending_model.year,
		"month": pending_model.month,
	}
	var blocked_model: Variant = client.send_order("develop")
	var blocked_order_result: Variant = client.last_order_result()
	var blocked_next_turn_responses: Array = client.send_many([
		{"type": "next_turn"},
		{"type": "save", "path": state_path},
	])
	var blocked_next_turn_model: Variant = null
	var blocked_next_turn_result: Variant = {}
	if not blocked_next_turn_responses.is_empty() and blocked_next_turn_responses[0] is Dictionary:
		var next_turn_response: Dictionary = blocked_next_turn_responses[0]
		blocked_next_turn_model = SnapshotModel.from_response(next_turn_response)
		var result: Variant = next_turn_response.get("result")
		if result is Dictionary:
			blocked_next_turn_result = result
	var blocked_before_regions: Array = pending_model.regions
	var blocked_after_regions: Array = []
	var blocked_after_date := {
		"year": -1,
		"month": -1,
	}
	if blocked_next_turn_model != null:
		blocked_after_regions = blocked_next_turn_model.regions
		blocked_after_date = {
			"year": blocked_next_turn_model.year,
			"month": blocked_next_turn_model.month,
		}

	var advance_pressed := _press_button(scene_root, "BattleAdvanceButton")
	for _i in 4:
		await process_frame
	var after_advance := _battle_observation(scene_root)

	var auto_pressed := _press_button(scene_root, "BattleAutoButton")
	for _i in 4:
		await process_frame
	var after_auto := _battle_observation(scene_root)

	print(PREFIX, JSON.stringify({
		"phase": "resume_pending",
		"state_exists": FileAccess.file_exists(state_path),
		"session_command": client.session_command(),
		"pending_before": pending_before,
		"blocked_order_model_available": blocked_model != null,
		"blocked_order_result": blocked_order_result if blocked_order_result != null else {},
		"blocked_next_turn_model_available": blocked_next_turn_model != null,
		"blocked_next_turn_result": blocked_next_turn_result,
		"blocked_before_regions": blocked_before_regions,
		"blocked_after_regions": blocked_after_regions,
		"blocked_before_date": blocked_before_date,
		"blocked_after_date": blocked_after_date,
		"advance_pressed": advance_pressed,
		"after_advance": after_advance,
		"auto_pressed": auto_pressed,
		"after_auto": after_auto,
	}))
	quit(0)


func _instantiate_scene() -> Control:
	var scene := ResourceLoader.load(MAIN_SCENE_PATH) as PackedScene
	if scene == null:
		_fail("cannot load main scene")
		return null
	var scene_root := scene.instantiate() as Control
	if scene_root == null:
		_fail("cannot instantiate main scene")
		return null
	root.add_child(scene_root)
	return scene_root


func _press_button(scene_root: Control, button_name: String) -> bool:
	var button := scene_root.find_child(button_name, true, false) as Button
	if button == null or button.disabled:
		return false
	button.emit_signal("pressed")
	return true


func _label_text(scene_root: Control, label_name: String) -> String:
	var label := scene_root.find_child(label_name, true, false) as Label
	return "" if label == null else label.text


func _request_types(path: String) -> Array:
	if not FileAccess.file_exists(path):
		return []
	var file := FileAccess.open(path, FileAccess.READ)
	if file == null:
		return []
	var types: Array = []
	for line in file.get_as_text().split("\n"):
		var parsed: Variant = JSON.parse_string(line.strip_edges())
		if parsed is Dictionary:
			types.append(str(parsed.get("type", "")))
	file.close()
	return types


func _button_state(scene_root: Control, button_name: String) -> Dictionary:
	var button := scene_root.find_child(button_name, true, false) as Button
	return {
		"found": button != null,
		"disabled": button != null and button.disabled,
		"text": "" if button == null else button.text,
	}


func _button_state_for_order(scene_root: Control, order_name: String) -> Dictionary:
	var order_bar := scene_root.find_child("OrderBarContent", true, false)
	if order_bar == null:
		return {"found": false, "disabled": false, "text": "", "order_name": order_name}
	for node: Node in order_bar.find_children("", "Button", true, false):
		var button := node as Button
		if button != null and str(button.get_meta("order_name", "")) == order_name:
			return {
				"found": true,
				"disabled": button.disabled,
				"text": button.text,
				"order_name": order_name,
			}
	return {"found": false, "disabled": false, "text": "", "order_name": order_name}


func _battle_observation(scene_root: Control) -> Dictionary:
	var battle_view := scene_root.find_child("BattleView", true, false) as Control
	var tiles: Array = []
	if battle_view != null:
		for child: Node in battle_view.get_children():
			if not child is Control or not str(child.name).begins_with("HexTile_"):
				continue
			var coordinates := str(child.name).trim_prefix("HexTile_").split("_")
			var hp_marker := child.find_child("HpMarker", true, false) as Label
			tiles.append({
				"q": int(coordinates[0]),
				"r": int(coordinates[1]),
				"hp_text": "" if hp_marker == null else hp_marker.text,
				"visible": child.is_visible_in_tree(),
			})
	var model_battle_result: Variant = null
	var model_hexes: Array = []
	var client: Variant = scene_root.get("_client")
	if client != null and client.has_method("snapshot_model"):
		var model: Variant = client.snapshot_model()
		if model != null and model.battle is Dictionary:
			model_battle_result = model.battle.get("result")
			model_hexes = model.battle.get("hexes", [])
	return {
		"visible": battle_view != null and battle_view.is_visible_in_tree(),
		"tile_count": tiles.size(),
		"tiles": tiles,
		"result_text": _label_text(scene_root, "BattleResultLabel"),
		"model_battle_result": model_battle_result,
		"model_hexes": model_hexes,
		"order_status": _label_text(scene_root, "LastOrderStatusLabel"),
	}
