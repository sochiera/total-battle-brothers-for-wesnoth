extends SceneTree


const MAIN_SCENE_PATH := "res://scenes/main.tscn"
const BridgeClient = preload("res://scripts/bridge_client.gd")
const PREFIX := "PERSISTENT_MARCH_PROCESS "


func _init() -> void:
	var args := OS.get_cmdline_user_args()
	if args.size() != 5:
		_fail("expected command prefix, state path, request path, seed and phase")
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
	var march_button := scene_root.get_node_or_null("MarchButton") as Button
	if march_button == null:
		_fail("missing MarchButton")
		return
	if args[4] == "first":
		var muster_button := scene_root.get_node_or_null("MusterButton") as Button
		if muster_button == null:
			_fail("missing MusterButton")
			return
		muster_button.emit_signal("pressed")
	else:
		if args[4] != "resume":
			_fail("unknown phase")
			return
	march_button.emit_signal("pressed")
	print(PREFIX, JSON.stringify({
		"controls": _controls(scene_root),
		"state_exists": FileAccess.file_exists(args[1]),
		"session_command": client.session_command(),
	}))
	call_deferred("quit", 0)


func _controls(scene_root: Control) -> Dictionary:
	return {
		"date": (scene_root.get_node("DateLabel") as Label).text,
		"result": (scene_root.get_node("ResultLabel") as Label).text,
		"order_status": (scene_root.get_node("LastOrderStatusLabel") as Label).text,
	}


func _fail(message: String) -> void:
	printerr("persistent_march_process_probe: ", message)
	call_deferred("quit", 2)
