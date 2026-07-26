extends SceneTree


const MAIN_SCENE_PATH := "res://scenes/main.tscn"
const BridgeClient = preload("res://scripts/bridge_client.gd")
const PREFIX := "PERSISTENT_ASSAULT_PROCESS "


func _init() -> void:
	var args := OS.get_cmdline_user_args()
	if args.size() != 5:
		_fail("expected command prefix, state path, request path, seed and phase")
		return
	var scene_root := _instantiate_scene()
	if scene_root == null:
		return
	var client := BridgeClient.create_persistent(args[0], args[1], args[3].to_int(), args[2])
	scene_root.bind_client(client)
	var controls_before_order := _controls(scene_root)
	var controls_after_muster: Variant = _run_phase(scene_root, args[4])
	if controls_after_muster == null:
		return

	print(PREFIX, JSON.stringify({
		"controls_before_order": controls_before_order,
		"controls_after_muster": controls_after_muster,
		"controls": _controls(scene_root),
		"state_exists": FileAccess.file_exists(args[1]),
		"session_command": client.session_command(),
	}))
	call_deferred("quit", 0)


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


func _run_phase(scene_root: Control, phase: String) -> Variant:
	match phase:
		"prepare":
			if not _press(scene_root, "MusterButton"):
				return null
			var after_muster := _controls(scene_root)
			if not _press(scene_root, "MarchButton"):
				return null
			return after_muster
		"battle", "unchanged":
			if _press(scene_root, "AssaultButton"):
				return {}
			return null
		_:
			_fail("unknown phase")
			return null


func _press(scene_root: Control, button_name: String) -> bool:
	var button := scene_root.get_node_or_null(button_name) as Button
	if button == null:
		_fail("missing %s" % button_name)
		return false
	button.emit_signal("pressed")
	return true


func _controls(scene_root: Control) -> Dictionary:
	var region_list := scene_root.get_node("RegionList") as ItemList
	var regions: Array[String] = []
	for index: int in region_list.item_count:
		regions.append(region_list.get_item_text(index))
	return {
		"date": (scene_root.get_node("DateLabel") as Label).text,
		"result": (scene_root.get_node("ResultLabel") as Label).text,
		"party_position": (scene_root.get_node("PlayerPartyPositionLabel") as Label).text,
		"regions": regions,
		"duchy_status": (scene_root.get_node("PlayerDuchyStatusLabel") as Label).text,
		"order_status": (scene_root.get_node("LastOrderStatusLabel") as Label).text,
	}


func _fail(message: String) -> void:
	printerr("persistent_assault_process_probe: ", message)
	call_deferred("quit", 2)
