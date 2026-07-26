extends SceneTree


const MAIN_SCENE_PATH := "res://scenes/main.tscn"
const BridgeClientScript = preload("res://scripts/bridge_client.gd")
const PREFIX := "PERSISTENT_NEXT_TURN "


func _init() -> void:
	var args: PackedStringArray = OS.get_cmdline_user_args()
	if args.size() != 4:
		_fail("expected command prefix, state path, request path and seed")
		return

	var seed := args[3].to_int()
	var first_scene := _instantiate_scene()
	if first_scene == null:
		return
	var first_client = BridgeClientScript.create_persistent(args[0], args[1], seed, args[2])
	first_scene.bind_client(first_client)
	var first_button := first_scene.get_node_or_null("NextTurnButton") as Button
	if first_button == null:
		_fail("missing NextTurnButton")
		return
	first_button.emit_signal("pressed")
	var first := _controls(first_scene)
	var state_exists_after_first_press := FileAccess.file_exists(args[1])
	first_scene.queue_free()

	var second_scene := _instantiate_scene()
	if second_scene == null:
		return
	var second_client = BridgeClientScript.create_persistent(args[0], args[1], seed, args[2])
	second_scene.bind_client(second_client)
	var second_button := second_scene.get_node_or_null("NextTurnButton") as Button
	if second_button == null:
		_fail("missing NextTurnButton after resume")
		return
	second_button.emit_signal("pressed")

	print(PREFIX, JSON.stringify({
		"state_exists_after_first_press": state_exists_after_first_press,
		"first": first,
		"second": _controls(second_scene),
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
	var region_list := scene_root.get_node("RegionList") as ItemList
	var names: Array[String] = []
	for index: int in region_list.item_count:
		names.append(region_list.get_item_text(index))
	return {
		"date": (scene_root.get_node("DateLabel") as Label).text,
		"result": (scene_root.get_node("ResultLabel") as Label).text,
		"regions": names,
	}


func _fail(message: String) -> void:
	printerr("persistent_next_turn_e2e_probe: ", message)
	call_deferred("quit", 2)
