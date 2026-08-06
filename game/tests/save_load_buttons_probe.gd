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
	var new_game_button := scene_root.get_node_or_null("%NewGameButton") as Button
	# Presence/labels + icon presentation (G95.1d/G107.1b); binding/status is save_load_binding_probe.
	print(PREFIX, JSON.stringify({
		"save": _button_payload(save_button),
		"load": _button_payload(load_button),
		"new_game": _button_payload(new_game_button),
	}))
	call_deferred("quit", 0)


func _button_payload(button: Button) -> Variant:
	if button == null:
		return null
	var icon_path := ""
	var icon_w := 0
	var icon_h := 0
	if button.icon != null:
		var tex := button.icon as Texture2D
		icon_path = tex.resource_path
		icon_w = int(tex.get_width())
		icon_h = int(tex.get_height())
	return {
		"name": button.name,
		"text": button.text,
		"disabled": button.disabled,
		"visible": button.visible,
		"unique_name_in_owner": button.unique_name_in_owner,
		"icon_path": icon_path,
		"icon_w": icon_w,
		"icon_h": icon_h,
	}
