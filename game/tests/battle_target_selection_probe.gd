extends SceneTree


const MAIN_SCENE_PATH := "res://scenes/main.tscn"
const SnapshotModel = preload("res://scripts/snapshot_model.gd")
const PREFIX := "BATTLE_TARGET_SELECTION "
const VIEWPORT_W := 1152.0
const VIEWPORT_H := 648.0


class RecordingClient extends RefCounted:
	var current_model: SnapshotModel
	var target_calls: Array = []
	var advance_calls := 0
	var auto_calls := 0
	var last_target_result: Variant = null
	var _last_battle_result: Variant = null

	func _init(model: SnapshotModel) -> void:
		current_model = model

	func snapshot_model() -> SnapshotModel:
		return current_model

	func battle_target(attacker: Dictionary, target: Dictionary) -> SnapshotModel:
		target_calls.append({"attacker": attacker, "target": target})
		if attacker == {"q": 0, "r": 0} and target == {"q": 2, "r": 0}:
			last_target_result = {"kind": "battle_target", "changed": true}
			current_model = _model(null, [{
				"attacker": attacker,
				"target": target,
			}])
		else:
			last_target_result = {
				"kind": "battle_target",
				"changed": false,
				"reason": "cel nie jest aktywnym wrogiem",
			}
		return current_model

	func battle_advance() -> SnapshotModel:
		advance_calls += 1
		_last_battle_result = null
		current_model = _model(null, [])
		current_model.battle["hexes"] = [
			{"q": 1, "r": 0, "terrain": "Plains", "side": "attacker", "hp": 9, "stunned": false},
			{"q": 2, "r": 0, "terrain": "Forest", "side": "defender", "hp": 8, "stunned": false},
			{"q": 0, "r": 1, "terrain": "Plains", "side": "attacker", "hp": 10, "stunned": false},
		]
		return current_model

	func battle_auto() -> SnapshotModel:
		auto_calls += 1
		_last_battle_result = {
			"kind": "battle",
			"order": "engage",
			"outcome": "zwycięstwo",
			"attacker_losses": 0,
			"defender_losses": 1,
		}
		current_model = _model("attacker_win", [])
		return current_model

	func last_battle_target_result() -> Variant:
		return last_target_result

	func last_battle_result() -> Variant:
		return _last_battle_result

	func reset_pending() -> void:
		current_model = _model(null, [])
		last_target_result = null
		_last_battle_result = null

	func _model(result: Variant, targets: Array) -> SnapshotModel:
		var model := SnapshotModel.new()
		model.year = 1
		model.month = 1
		model.player_result = "ongoing"
		model.regions = []
		model.battle = {
			"result": result,
			"hexes": [
				{"q": 0, "r": 0, "terrain": "Plains", "side": "attacker", "hp": 10, "stunned": false},
				{"q": 2, "r": 0, "terrain": "Forest", "side": "defender", "hp": 8, "stunned": false},
				{"q": 0, "r": 1, "terrain": "Plains", "side": "attacker", "hp": 10, "stunned": false},
			]
		}
		if not targets.is_empty():
			model.battle["attack_targets"] = targets.duplicate(true)
		return model

func _init() -> void:
	call_deferred("_run")


func _run() -> void:
	root.size = Vector2i(int(VIEWPORT_W), int(VIEWPORT_H))
	var scene := ResourceLoader.load(MAIN_SCENE_PATH) as PackedScene
	if scene == null:
		_fail("cannot load main scene")
		return
	var scene_root := scene.instantiate() as Control
	if scene_root == null:
		_fail("cannot instantiate main scene")
		return
	root.add_child(scene_root)
	scene_root.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	scene_root.size = Vector2(VIEWPORT_W, VIEWPORT_H)
	await process_frame
	await process_frame

	var client := RecordingClient.new(_model(null, []))
	scene_root.bind_client(client)
	scene_root.apply_model(client.current_model)
	await process_frame
	await process_frame

	var battle_view := scene_root.find_child("BattleView", true, false) as Control
	if battle_view == null or not battle_view.visible:
		_fail("pending battle view is not visible")
		return

	await _click_hex(battle_view, 0, 0)
	await _click_hex(battle_view, 2, 0)
	await process_frame
	await process_frame
	var valid_target_calls := client.target_calls.duplicate(true)
	var confirmed_targets := _attack_targets(client.current_model)

	var before_advance := _hexes(client.current_model)
	var advance_button := scene_root.find_child("BattleAdvanceButton", true, false) as Button
	if advance_button == null:
		_fail("missing BattleAdvanceButton")
		return
	advance_button.emit_signal("pressed")
	await process_frame
	await process_frame
	var after_advance := _hexes(client.current_model)
	var advance_target_state := _attack_targets(client.current_model)

	client.reset_pending()
	scene_root.apply_model(client.current_model)
	await process_frame
	await process_frame
	var auto_button := scene_root.find_child("BattleAutoButton", true, false) as Button
	if auto_button == null:
		_fail("missing BattleAutoButton")
		return
	auto_button.emit_signal("pressed")
	await process_frame
	await process_frame
	var auto_result: Variant = null
	if client.current_model != null and client.current_model.battle is Dictionary:
		auto_result = client.current_model.battle.get("result")
	var result_board_visible := battle_view.visible
	client.target_calls.clear()
	await _click_hex(battle_view, 0, 0)
	await _click_hex(battle_view, 2, 0)
	await process_frame
	await process_frame
	var result_board_target_calls := client.target_calls.duplicate(true)

	client.current_model = _no_battle_model()
	scene_root.apply_model(client.current_model)
	await process_frame
	await process_frame
	var no_battle_visible := battle_view.visible
	await _click_hex(battle_view, 0, 0)
	await _click_hex(battle_view, 2, 0)
	await process_frame
	await process_frame
	var no_battle_target_calls := client.target_calls.duplicate(true)

	client.reset_pending()
	scene_root.apply_model(client.current_model)
	await process_frame
	await process_frame
	client.target_calls.clear()
	await _click_hex(battle_view, 0, 0)
	await _click_hex(battle_view, 0, 1)
	await _click_hex(battle_view, 2, 0)
	await process_frame
	await process_frame
	var replacement_target_calls := client.target_calls.duplicate(true)

	client.reset_pending()
	scene_root.apply_model(client.current_model)
	await process_frame
	await process_frame
	client.target_calls.clear()
	var status_label := scene_root.find_child("LastOrderStatusLabel", true, false) as Label
	if status_label != null:
		status_label.text = ""
	await _click_hex(battle_view, 0, 0)
	await _click_hex(battle_view, 0, 1)
	await process_frame
	await process_frame

	print(PREFIX, JSON.stringify({
		"valid_target_calls": valid_target_calls,
		"confirmed_targets": confirmed_targets,
		"advance_calls": client.advance_calls,
		"before_advance": before_advance,
		"after_advance": after_advance,
		"advance_target_state": advance_target_state,
		"auto_calls": client.auto_calls,
		"auto_result": auto_result,
		"result_board_visible": result_board_visible,
		"result_board_target_calls": result_board_target_calls,
		"no_battle_visible": no_battle_visible,
		"no_battle_target_calls": no_battle_target_calls,
		"replacement_target_calls": replacement_target_calls,
		"invalid_target_calls": client.target_calls.duplicate(true),
		"invalid_status": _label_text(scene_root, "LastOrderStatusLabel"),
	}))
	quit(0)


func _model(result: Variant, targets: Array) -> SnapshotModel:
	var model := SnapshotModel.new()
	model.year = 1
	model.month = 1
	model.player_result = "ongoing"
	model.regions = []
	model.battle = {
		"result": result,
		"hexes": [
			{"q": 0, "r": 0, "terrain": "Plains", "side": "attacker", "hp": 10, "stunned": false},
			{"q": 2, "r": 0, "terrain": "Forest", "side": "defender", "hp": 8, "stunned": false},
			{"q": 0, "r": 1, "terrain": "Plains", "side": "attacker", "hp": 10, "stunned": false},
		]
	}
	if not targets.is_empty():
		model.battle["attack_targets"] = targets.duplicate(true)
	return model


func _no_battle_model() -> SnapshotModel:
	var model := SnapshotModel.new()
	model.year = 1
	model.month = 1
	model.player_result = "ongoing"
	model.regions = []
	model.battle = null
	return model


func _click_hex(battle_view: Control, q: int, r: int) -> void:
	var tile := battle_view.find_child("HexTile_%d_%d" % [q, r], true, false) as Control
	if tile == null:
		return
	var center := tile.get_global_rect().get_center()
	var press := InputEventMouseButton.new()
	press.button_index = MOUSE_BUTTON_LEFT
	press.pressed = true
	press.position = center
	press.global_position = center
	var release := InputEventMouseButton.new()
	release.button_index = MOUSE_BUTTON_LEFT
	release.pressed = false
	release.position = center
	release.global_position = center
	var viewport := tile.get_viewport()
	if viewport == null:
		return
	viewport.push_input(press)
	viewport.push_input(release)


func _hexes(model: SnapshotModel) -> Array:
	return [] if model == null or not model.battle is Dictionary else model.battle.get("hexes", [])


func _attack_targets(model: SnapshotModel) -> Array:
	if model == null or not model.battle is Dictionary:
		return []
	return model.battle.get("attack_targets", [])


func _label_text(scene_root: Control, name: String) -> String:
	var label := scene_root.find_child(name, true, false) as Label
	return "" if label == null else label.text


func _fail(message: String) -> void:
	printerr("battle_target_selection_probe: ", message)
	quit(1)
