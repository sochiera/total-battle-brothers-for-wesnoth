extends SceneTree


const MAIN_SCENE_PATH := "res://scenes/main.tscn"
const PREFIX := "ENVIRONMENT_AUTOSTART "


func _init() -> void:
	var press_next_turn := "--press" in OS.get_cmdline_user_args()
	var press_develop := "--develop" in OS.get_cmdline_user_args()
	if press_next_turn and press_develop:
		_fail("expected at most one button press")
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
	call_deferred("_observe_autostart", scene_root, press_next_turn, press_develop)


func _observe_autostart(scene_root: Control, press_next_turn: bool, press_develop: bool) -> void:
	var after_start := _controls(scene_root)
	if press_next_turn:
		var button := scene_root.get_node_or_null("NextTurnButton") as Button
		if button == null:
			_fail("missing NextTurnButton")
			return
		button.emit_signal("pressed")
	if press_develop:
		var button := scene_root.get_node_or_null("DevelopButton") as Button
		if button == null:
			_fail("missing DevelopButton")
			return
		button.emit_signal("pressed")
	print(PREFIX, JSON.stringify({
		"after_start": after_start,
		"after_press": _controls(scene_root),
		"state_exists": FileAccess.file_exists(OS.get_environment("TBB_STATE_PATH")),
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
		"duchy_status": (scene_root.get_node("PlayerDuchyStatusLabel") as Label).text,
		"regions": names,
	}


func _fail(message: String) -> void:
	printerr("environment_autostart_probe: ", message)
	call_deferred("quit", 2)
