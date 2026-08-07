extends SceneTree


## One-shot live review capture for task-613.
## Starts the real persistent bridge, resolves one Engage action, clicks Engage
## again in the same month, and saves the resulting exhausted-action status.

const MAIN_SCENE_PATH := "res://scenes/main.tscn"
const VIEWPORT_W := 1152.0
const VIEWPORT_H := 648.0
const PASSIVE_TURNS := 5
const PLAYER_OUTPOST_ID := "player outpost"
const OUT_PATH := "res://screenshots/task-613-blocked-military-order-1152x648.png"
const EXHAUSTED_STATUS := "Oddział już działał w tym miesiącu — zakończ turę."


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

	for _turn in PASSIVE_TURNS:
		if not await _press_button(scene_root, "NextTurnButton", 4):
			return
	if not await _press_button(scene_root, "RecruitButton", 5):
		return
	if not await _press_button(scene_root, "MusterButton", 6):
		return

	var map_view := scene_root.find_child("MapView", true, false) as Control
	if not _click_region(map_view, PLAYER_OUTPOST_ID):
		_fail("cannot select %s on the live map" % PLAYER_OUTPOST_ID, 7)
		return
	await process_frame
	await process_frame
	if not await _press_button(scene_root, "MarchButton", 8):
		return
	# March and battle are separate monthly actions.  Reset the marker before
	# the first Engage, while the live AI party remains on the border.
	if not await _press_button(scene_root, "NextTurnButton", 9):
		return
	if not await _press_button(scene_root, "EngageButton", 10):
		return

	var battle_view := scene_root.find_child("BattleView", true, false) as Control
	if not _has_resolved_battle(battle_view):
		_fail("first Engage did not render a resolved battle", 11)
		return

	# The second click is the task's visible monthly-action block.
	if not await _press_button(scene_root, "EngageButton", 12):
		return
	var status := scene_root.find_child("LastOrderStatusLabel", true, false) as Label
	if status == null or status.text != EXHAUSTED_STATUS:
		_fail("unexpected blocked-order status: %s" % ("missing" if status == null else status.text), 13)
		return
	if battle_view != null and battle_view.visible:
		_fail("blocked order must clear the stale battle view", 14)
		return
	if not _has_readable_strategic_chrome(scene_root):
		_fail("blocked-order capture pushed strategic chrome outside the viewport", 15)
		return

	if not _save_viewport(OUT_PATH):
		quit(16)
		return
	print("CAPTURED ", OUT_PATH)
	quit(0)


func _press_button(scene_root: Control, button_name: String, error_code: int) -> bool:
	var button := scene_root.find_child(button_name, true, false) as Button
	if button == null:
		_fail("missing %s" % button_name, error_code)
		return false
	if button.disabled:
		_fail("%s is disabled" % button_name, error_code)
		return false
	button.emit_signal("pressed")
	await process_frame
	await process_frame
	return true


func _click_region(map_view: Control, region_name: String) -> bool:
	if map_view == null:
		return false
	var tile := map_view.find_child("RegionTile_%s" % region_name, false, false) as Control
	if tile == null:
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
		return false
	viewport.push_input(press)
	viewport.push_input(release)
	return true


func _has_resolved_battle(battle_view: Control) -> bool:
	if battle_view == null or not battle_view.is_visible_in_tree():
		return false
	var result_label := battle_view.find_child("BattleResultLabel", true, false) as Label
	if result_label == null or result_label.text.strip_edges().is_empty():
		return false
	var tile_count := 0
	var side_paths := {}
	for child: Node in battle_view.get_children():
		if not child is Control or not str(child.name).begins_with("HexTile_"):
			continue
		tile_count += 1
		var silhouette := child.find_child("SideSilhouette", true, false) as TextureRect
		if silhouette != null and silhouette.texture != null:
			side_paths[silhouette.texture.resource_path] = true
	return tile_count >= 2 and side_paths.size() >= 2


func _has_readable_strategic_chrome(scene_root: Control) -> bool:
	var map_view := scene_root.find_child("MapView", true, false) as Control
	var status_controls := scene_root.find_child("StatusControls", true, false) as Control
	var order_controls := scene_root.find_child("OrderControls", true, false) as Control
	if map_view == null or status_controls == null or order_controls == null:
		return false
	var viewport_rect := Rect2(Vector2.ZERO, Vector2(VIEWPORT_W, VIEWPORT_H))
	if (
		not viewport_rect.encloses(map_view.get_global_rect())
		or not viewport_rect.encloses(status_controls.get_global_rect())
		or not viewport_rect.encloses(order_controls.get_global_rect())
	):
		return false
	var legend := map_view.find_child("OwnerLegend", true, false) as Control
	if legend == null or not map_view.get_global_rect().encloses(legend.get_global_rect()):
		return false
	return true


func _save_viewport(res_path: String) -> bool:
	var tex = root.get_texture()
	if tex == null:
		printerr("capture_task613_live_blocked_order: viewport texture null (use non-headless)")
		return false
	var img: Image = tex.get_image()
	if img == null:
		printerr("capture_task613_live_blocked_order: get_image null")
		return false
	if img.get_width() != int(VIEWPORT_W) or img.get_height() != int(VIEWPORT_H):
		printerr(
			"capture_task613_live_blocked_order: unexpected size %sx%s"
			% [img.get_width(), img.get_height()]
		)
		return false
	var abs_path := ProjectSettings.globalize_path(res_path)
	var err := img.save_png(abs_path)
	if err != OK:
		printerr("capture_task613_live_blocked_order: save_png failed ", err, " ", abs_path)
		return false
	return true


func _fail(message: String, exit_code: int) -> void:
	printerr("capture_task613_live_blocked_order: ", message)
	quit(exit_code)
