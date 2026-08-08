extends SceneTree


const MAIN_SCENE_PATH := "res://scenes/main.tscn"
const MainScene = preload("res://scripts/main.gd")
const PREFIX := "ORDER_BAR_DYNAMIC_BUTTON "


class TrackingScene extends MainScene:
	var calls: Array[String] = []

	func send_order_from_bridge(_client, order_name: String, _target: String = "") -> bool:
		calls.append(order_name)
		return true


func _init() -> void:
	call_deferred("_run")


func _run() -> void:
	var packed_scene := ResourceLoader.load(MAIN_SCENE_PATH) as PackedScene
	if packed_scene == null:
		_fail("cannot load main scene")
		return
	var scene_root := packed_scene.instantiate() as Control
	if scene_root == null:
		_fail("cannot instantiate main scene")
		return
	scene_root.set_script(TrackingScene)
	var order_buttons := scene_root.find_child("OrderButtons", true, false) as Container
	if order_buttons == null:
		_fail("missing OrderButtons")
		return
	var save_load_buttons := scene_root.find_child("SaveLoadButtons", true, false) as Container
	if save_load_buttons == null:
		_fail("missing SaveLoadButtons")
		return

	# These are the next designer-added commands: each declares its order
	# locally, but is intentionally absent from every code list.  One exercises
	# the command grid and one the other OrderBarContent row.
	var grid_button := _make_probe_recruit_button("ProbeGridRecruitButton")
	var other_row_button := _make_probe_recruit_button("ProbeOtherRowRecruitButton")
	order_buttons.add_child(grid_button)
	save_load_buttons.add_child(other_row_button)
	root.add_child(scene_root)
	await process_frame

	scene_root.bind_client(RefCounted.new())
	grid_button.emit_signal("pressed")
	other_row_button.emit_signal("pressed")
	var reinforce_button := scene_root.find_child("ReinforceButton", true, false) as Button
	if reinforce_button != null:
		reinforce_button.emit_signal("pressed")

	var buttons := {}
	for button: Button in [grid_button, other_row_button]:
		buttons[button.name] = _button_states(button)
	print(PREFIX, JSON.stringify({
		"calls": scene_root.calls,
		"buttons": buttons,
		"reinforce": _order_button_observation(reinforce_button),
	}))
	quit(0)


func _make_probe_recruit_button(button_name: String) -> Button:
	var button := Button.new()
	button.name = button_name
	button.text = "Próbna rekrutacja"
	button.set_meta("order_name", "recruit")
	return button


func _button_states(button: Button) -> Dictionary:
	var states := {}
	for state_name: String in ["normal", "hover", "pressed"]:
		var style := button.get_theme_stylebox(state_name)
		states[state_name] = {
			"carrier": "StyleBoxTexture" if style is StyleBoxTexture else str(style),
			"explicit": button.has_theme_stylebox_override(state_name),
		}
	return states


func _order_button_observation(button: Button) -> Dictionary:
	if button == null:
		return {"found": false}
	var icon_path := ""
	if button.icon != null:
		icon_path = button.icon.resource_path
	return {
		"found": true,
		"text": button.text,
		"order_name": str(button.get_meta("order_name", "")),
		"icon": icon_path,
		"styles": _button_states(button),
	}


func _fail(message: String) -> void:
	printerr("order_bar_dynamic_button_probe: ", message)
	quit(1)
