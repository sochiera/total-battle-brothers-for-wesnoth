extends SceneTree


const MAIN_SCENE_PATH := "res://scenes/main.tscn"
const PREFIX := "SAVE_LOAD_BUTTONS "


func _init() -> void:
	var scene := ResourceLoader.load(MAIN_SCENE_PATH) as PackedScene
	if scene == null:
		printerr("save_load_buttons_probe: cannot load main scene")
		call_deferred("quit", 2)
		return
	var scene_root := scene.instantiate() as Control
	if scene_root == null:
		printerr("save_load_buttons_probe: cannot instantiate main scene")
		call_deferred("quit", 2)
		return
	root.add_child(scene_root)

	var before_controls := _controls(scene_root)
	var save_button := scene_root.get_node_or_null("%SaveGameButton") as Button
	var load_button := scene_root.get_node_or_null("%LoadGameButton") as Button
	if save_button != null:
		save_button.emit_signal("pressed")
	if load_button != null:
		load_button.emit_signal("pressed")
	print(PREFIX, JSON.stringify({
		"save": _button_payload(save_button),
		"load": _button_payload(load_button),
		"controls_unchanged": _controls(scene_root) == before_controls,
	}))
	call_deferred("quit", 0)


func _button_payload(button: Button) -> Variant:
	if button == null:
		return null
	return {
		"name": button.name,
		"text": button.text,
		"disabled": button.disabled,
		"visible": button.visible,
		"pressed_connections": button.get_signal_connection_list("pressed").size(),
	}


func _controls(scene_root: Control) -> Dictionary:
	# Public control texts only — not scene tree shape (MainLayout nests children).
	return {
		"date": (scene_root.find_child("DateLabel", true, false) as Label).text,
		"result": (scene_root.find_child("ResultLabel", true, false) as Label).text,
		"duchy_status": (scene_root.find_child("PlayerDuchyStatusLabel", true, false) as Label).text,
		"order_status": (scene_root.find_child("LastOrderStatusLabel", true, false) as Label).text,
	}
