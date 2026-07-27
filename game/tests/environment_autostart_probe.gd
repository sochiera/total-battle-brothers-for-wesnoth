extends SceneTree


const MAIN_SCENE_PATH := "res://scenes/main.tscn"
const PREFIX := "ENVIRONMENT_AUTOSTART "
const BridgeConfig = preload("res://scripts/bridge_config.gd")


func _init() -> void:
	var press_next_turn := "--press" in OS.get_cmdline_user_args()
	var develop_presses := OS.get_cmdline_user_args().count("--develop")
	if press_next_turn and develop_presses > 0:
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
	call_deferred("_observe_autostart", scene_root, press_next_turn, develop_presses)


func _observe_autostart(scene_root: Control, press_next_turn: bool, develop_presses: int) -> void:
	var config: Dictionary = BridgeConfig.from_environment()
	var after_start := _controls(scene_root)
	if press_next_turn:
		var button := scene_root.find_child("NextTurnButton", true, false) as Button
		if button == null:
			_fail("missing NextTurnButton")
			return
		button.emit_signal("pressed")
	if develop_presses > 0:
		var button := scene_root.find_child("DevelopButton", true, false) as Button
		if button == null:
			_fail("missing DevelopButton")
			return
		for _press: int in develop_presses:
			button.emit_signal("pressed")
	print(PREFIX, JSON.stringify({
		"after_start": after_start,
		"after_press": _controls(scene_root),
		"state_exists": FileAccess.file_exists(config["state_path"]),
	}))
	call_deferred("quit", 0)


func _controls(scene_root: Control) -> Dictionary:
	var region_list := scene_root.find_child("RegionList", true, false) as ItemList
	var names: Array[String] = []
	for index: int in region_list.item_count:
		names.append(region_list.get_item_text(index))
	return {
		"date": (scene_root.find_child("DateLabel", true, false) as Label).text,
		"result": (scene_root.find_child("ResultLabel", true, false) as Label).text,
		"duchy_status": (scene_root.find_child("PlayerDuchyStatusLabel", true, false) as Label).text,
		"regions": names,
		"order_status": (scene_root.find_child("LastOrderStatusLabel", true, false) as Label).text,
	}


func _fail(message: String) -> void:
	printerr("environment_autostart_probe: ", message)
	call_deferred("quit", 2)
