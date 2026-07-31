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
	var button := scene_root.find_child("RecruitButton", true, false) as Button
	if button != null:
		button.emit_signal("pressed")
	print(PREFIX, JSON.stringify({
		"button": _button_payload(button),
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
		"pressed_connections": button.get_signal_connection_list("pressed").size(),
	}


func _controls(scene_root: Control) -> Dictionary:
	# Public control texts only — not scene tree shape (MainLayout nests children).
	return {
		"date": (scene_root.find_child("DateLabel", true, false) as Label).text,
		"result": (scene_root.find_child("ResultContractLabel", true, false) as Label).text,
		"duchy_status": (scene_root.find_child("PlayerDuchyStatusLabel", true, false) as Label).text,
		"order_status": (scene_root.find_child("LastOrderStatusLabel", true, false) as Label).text,
	}
