extends SceneTree


const BridgeClient = preload("res://scripts/bridge_client.gd")
const MapOrderE2E = preload("res://tests/map_order_e2e_helpers.gd")
const PREFIX := "PERSISTENT_MUSTER_PROCESS "
const TARGET_REGION := "player lands"
const VIEWPORT_W := 1152.0
const VIEWPORT_H := 648.0


func _init() -> void:
	call_deferred("_run")


func _run() -> void:
	var args := OS.get_cmdline_user_args()
	if args.size() != 4:
		_fail("expected command prefix, state path, request path and seed")
		return

	root.size = Vector2i(int(VIEWPORT_W), int(VIEWPORT_H))
	var scene_root := MapOrderE2E.instantiate_scene(self, VIEWPORT_W, VIEWPORT_H)
	if scene_root == null:
		return
	await process_frame
	await process_frame

	var map_view: Node = scene_root.find_child("MapView", true, false)
	if map_view == null:
		_fail("missing MapView")
		return
	var is_resume := FileAccess.file_exists(args[1])
	var client := BridgeClient.create_persistent(args[0], args[1], args[3].to_int(), args[2])
	scene_root.bind_client(client)
	await process_frame
	await process_frame

	if not await _select_region(map_view):
		return
	if not is_resume:
		# Start above the K117 boundary: the fresh game has one defender, so two
		# real recruit-button clicks make the source settlement's garrison 3.
		for _i in 2:
			if not await _press(scene_root, "RecruitButton"):
				return
		if not await _select_region(map_view):
			return
	var before := _observation(scene_root, map_view)
	if not await _press(scene_root, "MusterButton"):
		return
	var after := _observation(scene_root, map_view)
	print(PREFIX, JSON.stringify({
		"before": before,
		"after": after,
		"controls": _controls(scene_root),
		"state_exists": FileAccess.file_exists(args[1]),
		"session_command": client.session_command(),
	}))
	quit(0)


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
	return MapOrderE2E.observe(scene_root, map_view)


func _controls(scene_root: Control) -> Dictionary:
	return {
		"date": (scene_root.find_child("DateLabel", true, false) as Label).text,
		"result": (scene_root.find_child("ResultContractLabel", true, false) as Label).text,
		"order_status": (scene_root.find_child("LastOrderStatusLabel", true, false) as Label).text,
	}


func _fail(message: String) -> void:
	printerr("persistent_muster_process_probe: ", message)
	call_deferred("quit", 2)
