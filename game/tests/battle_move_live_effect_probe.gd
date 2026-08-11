extends SceneTree


const MAIN_SCENE_PATH := "res://scenes/main.tscn"
const BridgeClient = preload("res://scripts/bridge_client.gd")
const PREFIX := "BATTLE_MOVE_LIVE_EFFECT "
const MOVER := {"q": 0, "r": 2}
const DESTINATION := {"q": 0, "r": 3}


func _init() -> void:
	call_deferred("_run")


func _run() -> void:
	var args := OS.get_cmdline_user_args()
	if args.size() != 5:
		_fail("expected command prefix, state path, request path, phase and seed")
		return

	root.size = Vector2i(1152, 648)
	var scene_root := _instantiate_scene()
	if scene_root == null:
		return
	scene_root.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	scene_root.size = Vector2(1152, 648)
	for _i in 6:
		await process_frame

	var client := BridgeClient.create_persistent(
		args[0], args[1], args[4].to_int(), args[2]
	)
	scene_root.bind_client(client)
	for _i in 4:
		await process_frame

	var phase: String = args[3]
	if phase == "select":
		await _run_select(scene_root, client, args[1], args[2])
		return
	if phase == "resume_advance":
		await _run_resume_advance(scene_root, client, args[2])
		return
	_fail("unknown phase: %s" % phase)


func _run_select(
	scene_root: Control, client: BridgeClient, state_path: String, request_path: String
) -> void:
	if not _press(scene_root, "EngageButton"):
		return
	for _i in 4:
		await process_frame

	var pending_model: Variant = client.snapshot_model()
	if pending_model == null or not pending_model.battle is Dictionary:
		_fail("engage did not produce a pending battle")
		return
	var pending_battle: Dictionary = pending_model.battle.duplicate(true)

	if not await _click_hex(scene_root, int(MOVER["q"]), int(MOVER["r"])):
		return
	for _i in 3:
		await process_frame
	var destinations_after_select: Array = _destination_tile_names(scene_root)

	if not await _click_hex(
		scene_root, int(DESTINATION["q"]), int(DESTINATION["r"])
	):
		return
	for _i in 4:
		await process_frame

	# Capture JSON Lines before any later snapshot_model overwrites the file.
	var move_request_types := _request_types(request_path)
	var move_result: Variant = client.last_battle_move_result()
	var after_move := _battle_observation(scene_root, client)
	if after_move["model_hexes"].is_empty():
		_fail("battle_move did not keep a pending battle")
		return

	print(PREFIX, JSON.stringify({
		"phase": "select",
		"state_exists": FileAccess.file_exists(state_path),
		"session_command": client.session_command(),
		"pending": pending_battle,
		"destinations_after_select": destinations_after_select,
		"move_result": move_result,
		"after_move": after_move,
		"request_types": move_request_types,
	}))
	quit(0)


func _run_resume_advance(
	scene_root: Control, client: BridgeClient, request_path: String
) -> void:
	var resumed_model: Variant = client.snapshot_model()
	if resumed_model == null or not resumed_model.battle is Dictionary:
		_fail("resume did not restore a pending battle")
		return
	var before_advance := _battle_observation(scene_root, client)

	if not _press(scene_root, "BattleAdvanceButton"):
		return
	for _i in 4:
		await process_frame

	# Capture JSON Lines before any later snapshot_model overwrites the file.
	var advance_request_types := _request_types(request_path)
	var after_advance := _battle_observation(scene_root, client)
	if after_advance["model_hexes"].is_empty():
		_fail("battle_advance did not return a battle board")
		return

	print(PREFIX, JSON.stringify({
		"phase": "resume_advance",
		"session_command": client.session_command(),
		"before_advance": before_advance,
		"after_advance": after_advance,
		"request_types": advance_request_types,
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


func _press(scene_root: Control, button_name: String) -> bool:
	var button := scene_root.find_child(button_name, true, false) as Button
	if button == null or button.disabled:
		_fail("missing or disabled %s" % button_name)
		return false
	button.emit_signal("pressed")
	return true


func _click_hex(scene_root: Control, q: int, r: int) -> bool:
	var battle_view := scene_root.find_child("BattleView", true, false) as Control
	if battle_view == null or not battle_view.visible:
		_fail("missing visible BattleView")
		return false
	var tile := battle_view.find_child("HexTile_%d_%d" % [q, r], true, false) as Control
	if tile == null:
		_fail("missing battle hex %d,%d" % [q, r])
		return false
	var hit_target := tile.find_child("BattleHitTarget", true, false) as Control
	var clickable: Control = hit_target if hit_target != null else tile
	var center := clickable.get_global_rect().get_center()
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
	var viewport := clickable.get_viewport()
	if viewport == null:
		_fail("battle hex has no viewport")
		return false
	viewport.push_input(press)
	viewport.push_input(release)
	return true


func _destination_tile_names(scene_root: Control) -> Array:
	var battle_view := scene_root.find_child("BattleView", true, false) as Control
	if battle_view == null:
		return []
	var names: Array = []
	for child: Node in battle_view.get_children():
		if not child.get_meta("move_destination", false):
			continue
		names.append(str(child.name))
	names.sort()
	return names


func _battle_observation(scene_root: Control, client: BridgeClient) -> Dictionary:
	var battle_view := scene_root.find_child("BattleView", true, false) as Control
	var tiles: Array = []
	var mover_marked := false
	var destination_marked := false
	if battle_view != null:
		for child: Node in battle_view.get_children():
			if not child is Control or not str(child.name).begins_with("HexTile_"):
				continue
			var coordinates := str(child.name).trim_prefix("HexTile_").split("_")
			if coordinates.size() < 2:
				continue
			var q := int(coordinates[0])
			var r := int(coordinates[1])
			var hp_marker := child.find_child("HpMarker", true, false) as Label
			var marker_names: Array = []
			for nested: Node in child.get_children():
				var nested_name := str(nested.name)
				if nested_name.begins_with("MoveTargetMarker_"):
					marker_names.append(nested_name)
			tiles.append({
				"q": q,
				"r": r,
				"hp_text": "" if hp_marker == null else hp_marker.text,
				"visible": child.is_visible_in_tree(),
				"move_destination": bool(child.get_meta("move_destination", false)),
				"move_markers": marker_names,
			})
			if q == int(MOVER["q"]) and r == int(MOVER["r"]):
				for marker_name: String in marker_names:
					if marker_name.contains("mover") or marker_name.contains("both"):
						mover_marked = true
			if q == int(DESTINATION["q"]) and r == int(DESTINATION["r"]):
				if bool(child.get_meta("move_destination", false)):
					destination_marked = true
				for marker_name: String in marker_names:
					if (
						marker_name.contains("destination")
						or marker_name.contains("both")
					):
						destination_marked = true

	var model_battle: Dictionary = {}
	var model: Variant = client.snapshot_model()
	if model != null and model.battle is Dictionary:
		model_battle = model.battle.duplicate(true)

	return {
		"battle_visible": battle_view != null and battle_view.is_visible_in_tree(),
		"tiles": tiles,
		"model_battle": model_battle,
		"move_targets": model_battle.get("move_targets", []),
		"model_hexes": model_battle.get("hexes", []),
		"model_result": model_battle.get("result"),
		"mover_marked": mover_marked,
		"destination_marked": destination_marked,
		"order_status": _label_text(scene_root, "LastOrderStatusLabel"),
	}


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


func _label_text(scene_root: Control, label_name: String) -> String:
	var label := scene_root.find_child(label_name, true, false) as Label
	return "" if label == null else label.text


func _fail(message: String) -> void:
	printerr("battle_move_live_effect_probe: ", message)
	quit(1)
