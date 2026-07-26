extends SceneTree


const MAIN_SCENE_PATH := "res://scenes/main.tscn"
const BridgeConfig = preload("res://scripts/bridge_config.gd")
const PREFIX := "START_SESSION "


func _init() -> void:
	var args: PackedStringArray = OS.get_cmdline_user_args()
	if args.size() != 3:
		_fail("expected command prefix, state path and seed")
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

	if not scene_root.has_method("start_session"):
		print(PREFIX, JSON.stringify({"available": false}))
		call_deferred("quit", 0)
		return

	var config: Variant = BridgeConfig.from_values(
		" %s " % args[0],
		" %s " % args[1],
		args[2],
	)
	var started: bool = scene_root.start_session(config)
	var after_start := _controls(scene_root)
	var state_exists_after_start := FileAccess.file_exists(args[1])
	var button := scene_root.get_node_or_null("NextTurnButton") as Button
	if button == null:
		_fail("missing NextTurnButton")
		return
	button.emit_signal("pressed")

	print(PREFIX, JSON.stringify({
		"available": true,
		"started": started,
		"state_exists_after_start": state_exists_after_start,
		"after_start": after_start,
		"after_first_press": _controls(scene_root),
	}))
	call_deferred("quit", 0)


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
	printerr("start_session_probe: ", message)
	call_deferred("quit", 2)
