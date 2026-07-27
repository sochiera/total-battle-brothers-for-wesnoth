extends SceneTree


## G84.1c e2e: party tile mark via bridge muster→march across two processes.
## Fresh session has no player party; after muster+march the mark follows the
## party region from the model (and stays after --resume). No manual model setup.

const MAIN_SCENE_PATH := "res://scenes/main.tscn"
const BridgeClient = preload("res://scripts/bridge_client.gd")
const PartyMapMark = preload("res://tests/party_map_mark_helpers.gd")
const PREFIX := "PERSISTENT_PARTY_MAP_MARK "


func _init() -> void:
	call_deferred("_run")


func _run() -> void:
	var args := OS.get_cmdline_user_args()
	if args.size() != 5:
		_fail("expected command prefix, state path, request path, seed and phase")
		return
	var scene_root := _instantiate_scene()
	if scene_root == null:
		return
	await process_frame
	await process_frame

	var client := BridgeClient.create_persistent(args[0], args[1], args[3].to_int(), args[2])
	scene_root.bind_client(client)
	await process_frame
	await process_frame

	var map_view: Node = scene_root.find_child("MapView", true, false)
	if map_view == null:
		_fail("missing MapView")
		return

	var phase: String = args[4]
	var after_start: Dictionary = {}
	var after_orders: Dictionary = {}

	match phase:
		"orders":
			after_start = _party_mark_observation(scene_root, map_view)
			if not _press(scene_root, "MusterButton"):
				return
			if not _press(scene_root, "MarchButton"):
				return
			await process_frame
			await process_frame
			after_orders = _party_mark_observation(scene_root, map_view)
		"resume":
			after_orders = _party_mark_observation(scene_root, map_view)
		_:
			_fail("unknown phase: %s" % phase)
			return

	print(PREFIX, JSON.stringify({
		"phase": phase,
		"after_start": after_start,
		"after_orders": after_orders,
		"state_exists": FileAccess.file_exists(args[1]),
		"session_command": client.session_command(),
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
	if button == null:
		_fail("missing %s" % button_name)
		return false
	button.emit_signal("pressed")
	return true


func _party_mark_observation(scene_root: Control, map_view: Node) -> Dictionary:
	var position_label := scene_root.find_child("PlayerPartyPositionLabel", true, false) as Label
	var region_names: Array[String] = _region_names_from_map(map_view)
	return {
		"position_label": "" if position_label == null else position_label.text,
		"marked_regions": PartyMapMark.marked_party_regions(map_view, region_names),
		"marker_count": PartyMapMark.count_party_markers(map_view),
		"region_names": region_names,
	}


func _region_names_from_map(map_view: Node) -> Array[String]:
	var names: Array[String] = []
	for child: Node in map_view.get_children():
		if not str(child.name).begins_with("RegionTile_"):
			continue
		for nested: Node in child.get_children():
			if nested is Label:
				var text: String = (nested as Label).text
				if not text.is_empty() and not names.has(text):
					names.append(text)
	return names


func _fail(message: String) -> void:
	printerr("persistent_party_map_mark_probe: ", message)
	quit(2)
