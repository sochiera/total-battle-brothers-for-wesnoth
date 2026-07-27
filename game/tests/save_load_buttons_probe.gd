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

	var save_button := scene_root.get_node_or_null("%SaveGameButton") as Button
	var load_button := scene_root.get_node_or_null("%LoadGameButton") as Button
	# Presence/labels only; binding/status is save_load_binding_probe.
	print(PREFIX, JSON.stringify({
		"save": _button_payload(save_button),
		"load": _button_payload(load_button),
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
	}
