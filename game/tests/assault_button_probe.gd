extends SceneTree


const MAIN_SCENE_PATH := "res://scenes/main.tscn"
const PREFIX := "ASSAULT_BUTTON "


func _init() -> void:
	var scene := ResourceLoader.load(MAIN_SCENE_PATH) as PackedScene
	if scene == null:
		_fail("cannot load main scene")
		return
	var scene_root := scene.instantiate() as Control
	if scene_root == null:
		_fail("cannot instantiate main scene")
		return
	root.add_child(scene_root)

	var before_controls := _controls(scene_root)
	var button := scene_root.find_child("AssaultButton", true, false) as Button
	if button == null:
		print(PREFIX, JSON.stringify(null))
		call_deferred("quit", 0)
		return
	button.emit_signal("pressed")

	print(PREFIX, JSON.stringify({
		"name": button.name,
		"text": button.text,
		"pressed_connections": button.get_signal_connection_list("pressed").size(),
		"controls_unchanged": _controls(scene_root) == before_controls,
	}))
	call_deferred("quit", 0)


func _controls(scene_root: Control) -> Dictionary:
	var region_list := scene_root.find_child("RegionList", true, false) as ItemList
	var regions: Array[String] = []
	for index: int in region_list.item_count:
		regions.append(region_list.get_item_text(index))
	return {
		"date": (scene_root.find_child("DateLabel", true, false) as Label).text,
		"result": (scene_root.find_child("ResultLabel", true, false) as Label).text,
		"duchy_status": (scene_root.find_child("PlayerDuchyStatusLabel", true, false) as Label).text,
		"order_status": (scene_root.find_child("LastOrderStatusLabel", true, false) as Label).text,
		"regions": regions,
	}


func _fail(message: String) -> void:
	printerr("assault_button_probe: ", message)
	call_deferred("quit", 1)
