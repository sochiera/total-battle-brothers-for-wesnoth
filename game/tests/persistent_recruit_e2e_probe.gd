extends SceneTree


const MAIN_SCENE_PATH := "res://scenes/main.tscn"
const BridgeClient = preload("res://scripts/bridge_client.gd")
const PREFIX := "PERSISTENT_RECRUIT "
# G92.2a: two keeps fill after eight recruits; ninth is the first no-op.
const RECRUIT_COUNT := 9


func _init() -> void:
	var args: PackedStringArray = OS.get_cmdline_user_args()
	if args.size() != 4:
		_fail("expected command prefix, state path, request path and seed")
		return

	var seed := args[3].to_int()
	var first_scene := _instantiate_scene()
	if first_scene == null:
		return
	var first_client := BridgeClient.create_persistent(args[0], args[1], seed, args[2])
	first_scene.bind_client(first_client)
	var first_button := first_scene.find_child("RecruitButton", true, false) as Button
	if first_button == null:
		_fail("missing RecruitButton")
		return
	var first := _press_and_capture(first_scene, first_button, RECRUIT_COUNT)
	var state_exists_after_first_process := FileAccess.file_exists(args[1])
	first_scene.queue_free()

	var resumed_scene := _instantiate_scene()
	if resumed_scene == null:
		return
	var resumed_client := BridgeClient.create_persistent(args[0], args[1], seed, args[2])
	resumed_scene.bind_client(resumed_client)
	var resumed_button := resumed_scene.find_child("RecruitButton", true, false) as Button
	if resumed_button == null:
		_fail("missing RecruitButton after resume")
		return
	resumed_button.emit_signal("pressed")

	print(PREFIX, JSON.stringify({
		"state_exists_after_first_process": state_exists_after_first_process,
		"first": first,
		"resumed_command": resumed_client.session_command(),
		"resumed": _controls(resumed_scene),
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


func _controls(scene_root: Control) -> Dictionary:
	return {
		"date": (scene_root.find_child("DateLabel", true, false) as Label).text,
		"result": (scene_root.find_child("ResultLabel", true, false) as Label).text,
		"order_status": (scene_root.find_child("LastOrderStatusLabel", true, false) as Label).text,
	}


func _press_and_capture(scene_root: Control, button: Button, count: int) -> Array[Dictionary]:
	var controls: Array[Dictionary] = []
	for _press in count:
		button.emit_signal("pressed")
		controls.append(_controls(scene_root))
	return controls


func _fail(message: String) -> void:
	printerr("persistent_recruit_e2e_probe: ", message)
	call_deferred("quit", 2)
