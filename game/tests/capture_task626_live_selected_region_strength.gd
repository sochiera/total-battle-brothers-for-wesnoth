extends SceneTree


## One-shot live review capture for G113.1b (task-626).
## Uses the persistent bridge and the measured seed-73 sequence, then saves
## the selected own-party and enemy-settlement panel states at review size.

const MAIN_SCENE_PATH := "res://scenes/main.tscn"
const VIEWPORT_W := 1152.0
const VIEWPORT_H := 648.0
const PARTY_REGION_ID := "player lands"
const ENEMY_SETTLEMENT_REGION_ID := "ai outpost"
const PARTY_PANEL_TEXT := "Armia: własny (gracz), 5 jednostek, 73 PŻ"
const SETTLEMENT_PANEL_TEXT := "Osada: Posterunek wroga, garnizon: 1"
const PARTY_PATH := "res://screenshots/task-626-live-selected-party-1152x648.png"
const SETTLEMENT_PATH := "res://screenshots/task-626-live-selected-enemy-settlement-1152x648.png"


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
		_fail(
			"live bridge did not start: %s"
			% ("missing status" if start_status == null else start_status.text),
			3
		)
		return

	if not await _press_repeated(scene_root, "RecruitButton", 10):
		return
	if not await _press_button(scene_root, "MusterButton", 4):
		return

	var map_view := scene_root.find_child("MapView", true, false) as Control
	if not await _select_region(scene_root, map_view, PARTY_REGION_ID):
		return
	var party_panel := _panel_text(scene_root)
	if PARTY_PANEL_TEXT not in party_panel:
		_fail("own-party panel text missing: %s" % party_panel, 5)
		return
	if not _has_readable_review_chrome(scene_root):
		_fail("own-party frame clips strategic chrome", 6)
		return
	if not _save_viewport(PARTY_PATH):
		quit(7)
		return

	if not await _select_region(scene_root, map_view, ENEMY_SETTLEMENT_REGION_ID):
		return
	var settlement_panel := _panel_text(scene_root)
	if SETTLEMENT_PANEL_TEXT not in settlement_panel:
		_fail("enemy-settlement panel text missing: %s" % settlement_panel, 8)
		return
	if not _has_readable_review_chrome(scene_root):
		_fail("enemy-settlement frame clips strategic chrome", 9)
		return
	if not _save_viewport(SETTLEMENT_PATH):
		quit(10)
		return

	print("CAPTURED ", PARTY_PATH)
	print("CAPTURED ", SETTLEMENT_PATH)
	quit(0)


func _press_repeated(scene_root: Control, button_name: String, repeats: int) -> bool:
	for _i in repeats:
		if not await _press_button(scene_root, button_name, 4):
			return false
	return true


func _press_button(scene_root: Control, button_name: String, error_code: int) -> bool:
	var button := scene_root.find_child(button_name, true, false) as Button
	if button == null or button.disabled:
		_fail("missing or disabled %s" % button_name, error_code)
		return false
	button.emit_signal("pressed")
	await process_frame
	await process_frame
	return true


func _select_region(scene_root: Control, map_view: Control, region_id: String) -> bool:
	if map_view == null:
		_fail("missing MapView", 4)
		return false
	var tile := map_view.find_child("RegionTile_%s" % region_id, false, false) as Control
	if tile == null:
		_fail("missing tile for %s" % region_id, 4)
		return false
	var center: Vector2 = tile.get_global_rect().get_center()
	var press := InputEventMouseButton.new()
	press.button_index = MOUSE_BUTTON_LEFT
	press.pressed = true
	press.position = center
	press.global_position = center
	var release := InputEventMouseButton.new()
	release.button_index = MOUSE_BUTTON_LEFT
	release.pressed = false
	release.position = center
	release.global_position = center
	var viewport := tile.get_viewport()
	if viewport == null:
		_fail("missing viewport for %s" % region_id, 4)
		return false
	viewport.push_input(press)
	viewport.push_input(release)
	await process_frame
	await process_frame
	var selected := str(map_view.get("selected_region_name"))
	if selected != region_id:
		_fail("selection did not reach %s (got %s)" % [region_id, selected], 4)
		return false
	return true


func _panel_text(scene_root: Control) -> String:
	var panel := scene_root.find_child("SelectedRegionPanel", true, false)
	if panel == null:
		return ""
	return "\n".join(_visible_label_texts(panel))


func _visible_label_texts(node: Node) -> Array[String]:
	var texts: Array[String] = []
	_collect_visible_label_texts(node, texts)
	return texts


func _collect_visible_label_texts(node: Node, texts: Array[String]) -> void:
	if node is Label and (node as Label).is_visible_in_tree():
		var label_text := (node as Label).text
		if not label_text.is_empty():
			texts.append(label_text)
	for child: Node in node.get_children():
		_collect_visible_label_texts(child, texts)


func _has_readable_review_chrome(scene_root: Control) -> bool:
	var map_view := scene_root.find_child("MapView", true, false) as Control
	var status_controls := scene_root.find_child("StatusControls", true, false) as Control
	var order_controls := scene_root.find_child("OrderControls", true, false) as Control
	var selected_panel := scene_root.find_child("SelectedRegionPanel", true, false) as Control
	if map_view == null or status_controls == null or order_controls == null or selected_panel == null:
		return false
	var viewport_rect := Rect2(Vector2.ZERO, Vector2(VIEWPORT_W, VIEWPORT_H))
	for control: Control in [map_view, status_controls, order_controls, selected_panel]:
		if not control.is_visible_in_tree() or not viewport_rect.encloses(control.get_global_rect()):
			return false
	var legend := map_view.find_child("OwnerLegend", true, false) as Control
	if legend == null or not map_view.get_global_rect().encloses(legend.get_global_rect()):
		return false
	for child in map_view.get_children():
		if child is Control and str(child.name).begins_with("RegionTile_"):
			if legend.get_global_rect().intersects((child as Control).get_global_rect()):
				return false
	return true


func _save_viewport(res_path: String) -> bool:
	var texture := root.get_texture()
	if texture == null:
		printerr("capture_task626_live_selected_region_strength: viewport texture null")
		return false
	var image: Image = texture.get_image()
	if image == null:
		printerr("capture_task626_live_selected_region_strength: get_image null")
		return false
	if image.get_width() != int(VIEWPORT_W) or image.get_height() != int(VIEWPORT_H):
		printerr(
			"capture_task626_live_selected_region_strength: unexpected size %sx%s"
			% [image.get_width(), image.get_height()]
		)
		return false
	return image.save_png(ProjectSettings.globalize_path(res_path)) == OK


func _fail(message: String, exit_code: int) -> void:
	printerr("capture_task626_live_selected_region_strength: ", message)
	quit(exit_code)
