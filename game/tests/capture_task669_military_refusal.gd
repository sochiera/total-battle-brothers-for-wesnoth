extends SceneTree


## One-shot live review capture for task-669.
## Starts the real seed-73 bridge, musters the player at Player Lands, refuses
## an Assault with no enemy in reach, and saves the full-screen refusal frame.

const MAIN_SCENE_PATH := "res://scenes/main.tscn"
const VIEWPORT_W := 1152.0
const VIEWPORT_H := 648.0
const OUT_PATH := "res://screenshots/task-669-military-refusal-1152x648.png"
const EXPECTED_STATUS := "W zasięgu nie ma wrogiej osady — uderz na wojsko wroga."


func _init() -> void:
	call_deferred("_run")


func _run() -> void:
	root.size = Vector2i(int(VIEWPORT_W), int(VIEWPORT_H))

	var scene: PackedScene = ResourceLoader.load(MAIN_SCENE_PATH) as PackedScene
	if scene == null:
		_fail("cannot load main scene", 2)
		return
	var scene_root := scene.instantiate() as Control
	if scene_root == null:
		_fail("cannot instantiate main scene", 2)
		return
	root.add_child(scene_root)
	scene_root.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	scene_root.size = Vector2(VIEWPORT_W, VIEWPORT_H)

	for _i in 8:
		await process_frame

	var start_status := scene_root.find_child("StartStatusLabel", true, false) as Label
	if start_status == null or not start_status.text.is_empty():
		_fail("live bridge did not start", 3)
		return
	if not await _press_button(scene_root, "MusterButton", 4):
		return
	if not await _press_button(scene_root, "AssaultButton", 5):
		return

	var status := scene_root.find_child("LastOrderStatusLabel", true, false) as Label
	if status == null or status.text != EXPECTED_STATUS:
		_fail("unexpected refusal status: %s" % ("missing" if status == null else status.text), 6)
		return
	if not status.is_visible_in_tree() or not _has_readable_strategic_chrome(scene_root):
		_fail("refusal frame does not show the complete strategic scene", 7)
		return

	if not _save_viewport(OUT_PATH):
		quit(8)
		return
	print("CAPTURED ", OUT_PATH)
	print("ORDER_STATUS ", status.text)
	quit(0)


func _press_button(scene_root: Control, button_name: String, error_code: int) -> bool:
	var button := scene_root.find_child(button_name, true, false) as Button
	if button == null or button.disabled:
		_fail("missing or disabled %s" % button_name, error_code)
		return false
	button.emit_signal("pressed")
	await process_frame
	await process_frame
	return true


func _has_readable_strategic_chrome(scene_root: Control) -> bool:
	var viewport_rect := Rect2(Vector2.ZERO, Vector2(VIEWPORT_W, VIEWPORT_H))
	for node_name in ["MapView", "StatusControls", "OrderControls"]:
		var node := scene_root.find_child(node_name, true, false) as Control
		if node == null or not node.is_visible_in_tree() or not viewport_rect.encloses(node.get_global_rect()):
			return false
	var map_view := scene_root.find_child("MapView", true, false) as Control
	var legend := map_view.find_child("OwnerLegend", true, false) as Control
	return legend != null and map_view.get_global_rect().encloses(legend.get_global_rect())


func _save_viewport(res_path: String) -> bool:
	var texture := root.get_texture()
	if texture == null:
		printerr("capture_task669_military_refusal: viewport texture null (use non-headless)")
		return false
	var image: Image = texture.get_image()
	if image == null:
		printerr("capture_task669_military_refusal: get_image null")
		return false
	if image.get_width() != int(VIEWPORT_W) or image.get_height() != int(VIEWPORT_H):
		printerr("capture_task669_military_refusal: unexpected size %sx%s" % [image.get_width(), image.get_height()])
		return false
	return image.save_png(ProjectSettings.globalize_path(res_path)) == OK


func _fail(message: String, exit_code: int) -> void:
	printerr("capture_task669_military_refusal: ", message)
	quit(exit_code)
