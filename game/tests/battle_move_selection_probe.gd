extends SceneTree


const MAIN_SCENE_PATH := "res://scenes/main.tscn"
const SnapshotModel = preload("res://scripts/snapshot_model.gd")
const PREFIX := "BATTLE_MOVE_SELECTION "
const VIEWPORT_W := 1152.0
const VIEWPORT_H := 648.0
const MOVER := {"q": 0, "r": 0}
const ENEMY := {"q": 2, "r": 0}
const VALID_DESTINATION := {"q": 0, "r": 1}
const REFUSED_DESTINATION := {"q": 1, "r": 0}
# Occupied-free axial neighbour that is not a revealed move tile after select.
const EMPTY_MISS := {"q": 3, "r": 0}


class RecordingClient extends RefCounted:
	var current_model: SnapshotModel
	var move_calls: Array = []
	var target_calls: Array = []
	var last_move_result: Variant = null
	var last_target_result: Variant = null
	var _last_battle_result: Variant = null

	func _init(model: SnapshotModel) -> void:
		current_model = model

	func snapshot_model() -> SnapshotModel:
		return current_model

	func battle_move(mover: Dictionary, destination: Dictionary) -> SnapshotModel:
		move_calls.append({"mover": mover, "destination": destination})
		if mover == MOVER and destination == VALID_DESTINATION:
			last_move_result = {"kind": "battle_move", "changed": true}
			current_model = make_model(null, [], [{
				"mover": mover,
				"destination": destination,
			}])
		else:
			last_move_result = {
				"kind": "battle_move",
				"changed": false,
				"reason": "pole docelowe jest niedostępne",
			}
		return current_model

	func battle_target(attacker: Dictionary, target: Dictionary) -> SnapshotModel:
		target_calls.append({"attacker": attacker, "target": target})
		if attacker == MOVER and target == ENEMY:
			last_target_result = {"kind": "battle_target", "changed": true}
			current_model = make_model(null, [{
				"attacker": attacker,
				"target": target,
			}], [])
		else:
			last_target_result = {
				"kind": "battle_target",
				"changed": false,
				"reason": "cel nie jest aktywnym wrogiem",
			}
		return current_model

	func battle_advance() -> SnapshotModel:
		return current_model

	func battle_auto() -> SnapshotModel:
		return current_model

	func last_battle_move_result() -> Variant:
		return last_move_result

	func last_battle_target_result() -> Variant:
		return last_target_result

	func last_battle_result() -> Variant:
		return _last_battle_result

	func reset_pending() -> void:
		current_model = make_model(null, [], [])
		last_move_result = null
		last_target_result = null
		_last_battle_result = null

	static func make_model(result: Variant, targets: Array, moves: Array) -> SnapshotModel:
		var model := SnapshotModel.new()
		model.year = 1
		model.month = 1
		model.player_result = "ongoing"
		model.regions = []
		model.battle = {
			"result": result,
			"hexes": [
				{
					"q": 0,
					"r": 0,
					"terrain": "Plains",
					"side": "attacker",
					"hp": 10,
					"stunned": false,
				},
				{
					"q": 2,
					"r": 0,
					"terrain": "Forest",
					"side": "defender",
					"hp": 8,
					"stunned": false,
				},
			],
		}
		if not targets.is_empty():
			model.battle["attack_targets"] = targets.duplicate(true)
		if not moves.is_empty():
			model.battle["move_targets"] = moves.duplicate(true)
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

	var client := RecordingClient.new(RecordingClient.make_model(null, [], []))
	scene_root.bind_client(client)
	scene_root.apply_model(client.current_model)
	await process_frame
	await process_frame

	var battle_view := scene_root.find_child("BattleView", true, false) as Control
	if battle_view == null or not battle_view.visible:
		_fail("pending battle view is not visible")
		return

	var status_label: Label = scene_root.find_child("LastOrderStatusLabel", true, false) as Label
	var destinations_before_select: Array = _destination_tile_names(battle_view)
	await _click_hex(battle_view, 0, 0)
	await process_frame
	await process_frame
	var destinations_after_select: Array = _destination_tile_names(battle_view)

	await _click_hex(battle_view, int(VALID_DESTINATION["q"]), int(VALID_DESTINATION["r"]))
	await process_frame
	await process_frame
	var valid_move_calls: Array = client.move_calls.duplicate(true)
	var confirmed_moves: Array = _move_targets(client.current_model)
	var pending_after_valid: Variant = _battle_result(client.current_model)
	var hexes_after_valid: Array = _hexes(client.current_model)
	var battle_visible_after_valid: bool = battle_view.visible

	_reset_scenario(client, scene_root, status_label)
	await process_frame
	await process_frame
	var hexes_before_refuse: Array = _hexes(client.current_model)
	await _click_hex(battle_view, 0, 0)
	await process_frame
	await process_frame
	await _click_hex(
		battle_view, int(REFUSED_DESTINATION["q"]), int(REFUSED_DESTINATION["r"])
	)
	await process_frame
	await process_frame
	var refused_move_calls: Array = client.move_calls.duplicate(true)
	var refused_hexes: Array = _hexes(client.current_model)
	var refused_status: String = _label_text(status_label)
	var refused_moves: Array = _move_targets(client.current_model)
	var battle_visible_after_refuse: bool = battle_view.visible

	_reset_scenario(client, scene_root, status_label)
	await process_frame
	await process_frame
	await _click_hex(battle_view, 0, 0)
	await process_frame
	await process_frame
	await _click_hex(battle_view, int(ENEMY["q"]), int(ENEMY["r"]))
	await process_frame
	await process_frame
	var attack_move_calls: Array = client.move_calls.duplicate(true)
	var attack_target_calls: Array = client.target_calls.duplicate(true)

	_reset_scenario(client, scene_root, status_label)
	await process_frame
	await process_frame
	await _click_hex(battle_view, 0, 0)
	await process_frame
	await process_frame
	# Non-destination empty hex after own-unit select must not emit move/target.
	await _click_synthetic(battle_view, int(EMPTY_MISS["q"]), int(EMPTY_MISS["r"]))
	await process_frame
	await process_frame
	var empty_miss_move_calls: Array = client.move_calls.duplicate(true)
	var empty_miss_target_calls: Array = client.target_calls.duplicate(true)
	var empty_miss_status: String = _label_text(status_label)

	_reset_scenario(client, scene_root, status_label)
	await process_frame
	await process_frame
	await _click_hex(battle_view, int(ENEMY["q"]), int(ENEMY["r"]))
	await process_frame
	await process_frame
	var enemy_first_move_calls: Array = client.move_calls.duplicate(true)
	var enemy_first_target_calls: Array = client.target_calls.duplicate(true)
	var enemy_first_status: String = _label_text(status_label)

	print(PREFIX, JSON.stringify({
		"destinations_before_select": destinations_before_select,
		"destinations_after_select": destinations_after_select,
		"valid_move_calls": valid_move_calls,
		"confirmed_moves": confirmed_moves,
		"pending_after_valid": pending_after_valid,
		"hexes_after_valid": hexes_after_valid,
		"battle_visible_after_valid": battle_visible_after_valid,
		"refused_move_calls": refused_move_calls,
		"refused_hexes": refused_hexes,
		"hexes_before_refuse": hexes_before_refuse,
		"refused_status": refused_status,
		"refused_moves": refused_moves,
		"battle_visible_after_refuse": battle_visible_after_refuse,
		"attack_move_calls": attack_move_calls,
		"attack_target_calls": attack_target_calls,
		"empty_miss_move_calls": empty_miss_move_calls,
		"empty_miss_target_calls": empty_miss_target_calls,
		"empty_miss_status": empty_miss_status,
		"enemy_first_move_calls": enemy_first_move_calls,
		"enemy_first_target_calls": enemy_first_target_calls,
		"enemy_first_status": enemy_first_status,
	}))
	quit(0)


func _reset_scenario(
	client: RecordingClient, scene_root: Control, status_label: Label
) -> void:
	client.reset_pending()
	scene_root.apply_model(client.current_model)
	client.move_calls.clear()
	client.target_calls.clear()
	if status_label != null:
		status_label.text = ""


func _destination_tile_names(battle_view: Control) -> Array:
	var names: Array = []
	for child: Node in battle_view.get_children():
		if not child.get_meta("move_destination", false):
			continue
		names.append(str(child.name))
	names.sort()
	return names


func _click_hex(battle_view: Control, q: int, r: int) -> void:
	var tile := battle_view.find_child("HexTile_%d_%d" % [q, r], true, false) as Control
	if tile == null:
		return
	_push_click_at(tile.get_viewport(), tile.get_global_rect().get_center())


func _click_synthetic(battle_view: Control, q: int, r: int) -> void:
	## Off-board empty hex: drive the same handler path without a real tile.
	var press := InputEventMouseButton.new()
	press.button_index = MOUSE_BUTTON_LEFT
	press.pressed = true
	battle_view._on_tile_gui_input(press, {"q": q, "r": r, "terrain": "Plains"})


func _push_click_at(viewport: Viewport, center: Vector2) -> void:
	if viewport == null:
		return
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
	viewport.push_input(press)
	viewport.push_input(release)


func _hexes(model: SnapshotModel) -> Array:
	return [] if model == null or not model.battle is Dictionary else model.battle.get("hexes", [])


func _move_targets(model: SnapshotModel) -> Array:
	if model == null or not model.battle is Dictionary:
		return []
	return model.battle.get("move_targets", [])


func _battle_result(model: SnapshotModel) -> Variant:
	if model == null or not model.battle is Dictionary:
		return "missing"
	return model.battle.get("result")


func _label_text(status_label: Label) -> String:
	return "" if status_label == null else status_label.text


func _fail(message: String) -> void:
	printerr("battle_move_selection_probe: ", message)
	quit(1)
