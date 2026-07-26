extends SceneTree


const MAIN_SCENE_PATH := "res://scenes/main.tscn"
const PREFIX := "RECRUIT_BUTTON "


func _init() -> void:
	var scene := ResourceLoader.load(MAIN_SCENE_PATH) as PackedScene
	if scene == null:
		printerr("recruit_button_probe: cannot load main scene")
		call_deferred("quit", 2)
		return
	var scene_root := scene.instantiate() as Control
	if scene_root == null:
		printerr("recruit_button_probe: cannot instantiate main scene")
		call_deferred("quit", 2)
		return
	root.add_child(scene_root)

	var before_controls := _controls(scene_root)
	var button := scene_root.get_node_or_null("RecruitButton") as Button
	if button != null:
		button.emit_signal("pressed")
	print(PREFIX, JSON.stringify({
		"button": _button_payload(button, scene_root),
		"controls_unchanged": _controls(scene_root) == before_controls,
	}))
	call_deferred("quit", 0)


func _button_payload(button: Button, scene_root: Control) -> Variant:
	if button == null:
		return null
	return {
		"name": button.name,
		"text": button.text,
		"disabled": button.disabled,
		"direct_child": button.get_parent() == scene_root,
		"pressed_connections": button.get_signal_connection_list("pressed").size(),
	}


func _controls(scene_root: Control) -> Dictionary:
	return {
		"date": (scene_root.get_node("DateLabel") as Label).text,
		"result": (scene_root.get_node("ResultLabel") as Label).text,
		"duchy_status": (scene_root.get_node("PlayerDuchyStatusLabel") as Label).text,
		"order_status": (scene_root.get_node("LastOrderStatusLabel") as Label).text,
		"children": scene_root.get_child_count(),
	}
