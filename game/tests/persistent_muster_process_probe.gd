extends SceneTree


const MAIN_SCENE_PATH := "res://scenes/main.tscn"
const BridgeClient = preload("res://scripts/bridge_client.gd")
const PREFIX := "PERSISTENT_MUSTER_PROCESS "


func _init() -> void:
	var args := OS.get_cmdline_user_args()
	if args.size() != 4:
		_fail("expected command prefix, state path, request path and seed")
		return
	var scene := ResourceLoader.load(MAIN_SCENE_PATH) as PackedScene
	if scene == null:
		_fail("cannot load main scene")
		return
	var scene_root := scene.instantiate() as Control
	if scene_root == null:
		_fail("cannot instantiate main scene")
		return
	root.add_child(scene_root)
	var client := BridgeClient.create_persistent(args[0], args[1], args[3].to_int(), args[2])
	scene_root.bind_client(client)
	var button := scene_root.find_child("MusterButton", true, false) as Button
	if button == null:
		_fail("missing MusterButton")
		return
	button.emit_signal("pressed")
	print(PREFIX, JSON.stringify({
		"controls": _controls(scene_root),
		"state_exists": FileAccess.file_exists(args[1]),
		"session_command": client.session_command(),
	}))
	call_deferred("quit", 0)


func _controls(scene_root: Control) -> Dictionary:
	return {
		"date": (scene_root.find_child("DateLabel", true, false) as Label).text,
		"result": (scene_root.find_child("ResultContractLabel", true, false) as Label).text,
		"order_status": (scene_root.find_child("LastOrderStatusLabel", true, false) as Label).text,
	}


func _fail(message: String) -> void:
	printerr("persistent_muster_process_probe: ", message)
	call_deferred("quit", 2)
