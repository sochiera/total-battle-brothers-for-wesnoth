extends SceneTree


## G112.1d: live reinforce UI path across two Godot processes.
## The probe deliberately uses BridgeClient + Main controls only: button presses
## become JSON Lines, the bridge runs the core, and the next process renders the
## saved snapshot without issuing another order.

const BridgeClient = preload("res://scripts/bridge_client.gd")
const MapOrderE2E = preload("res://tests/map_order_e2e_helpers.gd")
const PREFIX := "PERSISTENT_REINFORCE_PROCESS "
const VIEWPORT_W := 1152.0
const VIEWPORT_H := 648.0
const TARGET_REGION := "player outpost"


func _init() -> void:
	call_deferred("_run")


func _run() -> void:
	var args := OS.get_cmdline_user_args()
	if args.size() != 5:
		_fail("expected command prefix, state path, request path, seed and phase")
		return

	root.size = Vector2i(int(VIEWPORT_W), int(VIEWPORT_H))
	var scene_root := MapOrderE2E.instantiate_scene(self, VIEWPORT_W, VIEWPORT_H)
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

	match args[4]:
		"first":
			await _stage_party(scene_root)
			if not await _select_region(map_view):
				return
			var before := _observation(scene_root, map_view)
			if not await _press(scene_root, "ReinforceButton"):
				return
			var after := _observation(scene_root, map_view)
			print(PREFIX, JSON.stringify({
				"phase": "first",
				"before": before,
				"after": after,
				"requests": _request_lines(args[2]),
				"state_exists": FileAccess.file_exists(args[1]),
				"session_command": client.session_command(),
			}))
		"resume":
			if not await _select_region(map_view):
				return
			var resumed := _observation(scene_root, map_view)
			print(PREFIX, JSON.stringify({
				"phase": "resume",
				"resumed": resumed,
				"requests": _request_lines(args[2]),
				"state_exists": FileAccess.file_exists(args[1]),
				"session_command": client.session_command(),
			}))
		_:
			_fail("unknown phase: %s" % args[4])
			return
	quit(0)


func _stage_party(scene_root: Control) -> void:
	for _i in 10:
		if not await _press(scene_root, "RecruitButton"):
			return
	if not await _press(scene_root, "MusterButton"):
		return
	if not await _select_region(scene_root.find_child("MapView", true, false)):
		return
	if not await _press(scene_root, "MarchButton"):
		return
	await process_frame
	await process_frame
	if not await _press(scene_root, "NextTurnButton"):
		return


func _select_region(map_view: Node) -> bool:
	if not MapOrderE2E.click_region(self, map_view, TARGET_REGION):
		return false
	await process_frame
	await process_frame
	return true


func _press(scene_root: Control, button_name: String) -> bool:
	if not MapOrderE2E.press(self, scene_root, button_name):
		return false
	await process_frame
	await process_frame
	return true


func _observation(scene_root: Control, map_view: Node) -> Dictionary:
	var public_observation := MapOrderE2E.observe(scene_root, map_view)
	public_observation["selected_panel_text"] = _selected_panel_text(scene_root)
	return public_observation


func _selected_panel_text(scene_root: Control) -> String:
	var panel := scene_root.find_child("SelectedRegionPanel", true, false)
	if panel == null:
		return ""
	return "\n".join(_visible_label_texts(panel))


func _visible_label_texts(node: Node) -> Array[String]:
	var texts: Array[String] = []
	_collect_visible_label_texts(node, texts)
	return texts


func _collect_visible_label_texts(node: Node, texts: Array[String]) -> void:
	if node is Label:
		var label := node as Label
		if label.is_visible_in_tree() and not label.text.is_empty():
			texts.append(label.text)
	for child: Node in node.get_children():
		_collect_visible_label_texts(child, texts)


func _request_lines(path: String) -> Array:
	if not FileAccess.file_exists(path):
		return []
	var file := FileAccess.open(path, FileAccess.READ)
	if file == null:
		return []
	var lines: Array = []
	for line in file.get_as_text().split("\n"):
		if line.strip_edges().is_empty():
			continue
		var parsed: Variant = JSON.parse_string(line)
		lines.append(parsed if parsed is Dictionary else {})
	return lines


func _fail(message: String) -> void:
	printerr("persistent_reinforce_process_probe: ", message)
	quit(2)
