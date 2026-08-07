extends SceneTree


## One-shot live review capture for G111.1d (task-624).
## Reads the measured seed-73 fixture through the real persistent bridge,
## captures the blocked March explanation, then captures the Engage escape hatch
## and battle.

const MAIN_SCENE_PATH := "res://scenes/main.tscn"
const VIEWPORT_W := 1152.0
const VIEWPORT_H := 648.0
const PLAYER_OUTPOST_ID := "player outpost"
const BLOCKED_STATUS := (
	"Droga zablokowana w regionie Pogranicze: stoi tam wojsko wroga. "
	+ "Uderz na wojsko wroga."
)
const BLOCKED_PATH := "res://screenshots/task-624-live-blocked-march-1152x648.png"
const ENGAGE_PATH := "res://screenshots/task-624-live-engage-battle-1152x648.png"


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
	if not _marker_visible_at(scene_root, PLAYER_OUTPOST_ID, "PlayerPartyMarker"):
		_fail("fixture did not start with the player at the outpost", 4)
		return
	if not await _press_button(scene_root, "MarchButton", 5):
		return
	var status := scene_root.find_child("LastOrderStatusLabel", true, false) as Label
	if status == null or status.text != BLOCKED_STATUS:
		_fail("unexpected blocked-march status: %s" % ("missing" if status == null else status.text), 6)
		return
	if not _marker_visible_at(scene_root, PLAYER_OUTPOST_ID, "PlayerPartyMarker"):
		_fail("blocked march moved the player party", 7)
		return
	if not _has_readable_strategic_chrome(scene_root):
		_fail("blocked-march frame has overlapping legend or clipped chrome", 8)
		return
	if not _save_viewport(BLOCKED_PATH):
		quit(9)
		return

	if not await _press_button(scene_root, "EngageButton", 10):
		return
	var battle_view := scene_root.find_child("BattleView", true, false) as Control
	if (
		battle_view == null
		or not battle_view.is_visible_in_tree()
		or not status.text.begins_with("Starcie: ")
	):
		_fail("Engage did not render a resolved battle", 11)
		return
	var result := battle_view.find_child("BattleResultLabel", true, false) as Label
	if result == null or result.text.strip_edges().is_empty():
		_fail("Engage battle has no result", 12)
		return
	if not _has_readable_strategic_chrome(scene_root):
		_fail("engage frame has overlapping legend or clipped chrome", 13)
		return
	if not _save_viewport(ENGAGE_PATH):
		quit(14)
		return

	print("CAPTURED ", BLOCKED_PATH)
	print("CAPTURED ", ENGAGE_PATH)
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


func _marker_visible_at(scene_root: Control, region_id: String, marker_name: String) -> bool:
	var map_view := scene_root.find_child("MapView", true, false) as Control
	if map_view == null:
		return false
	var tile := map_view.find_child("RegionTile_%s" % region_id, false, false)
	var marker := null if tile == null else tile.find_child(marker_name, false, false)
	return marker is CanvasItem and (marker as CanvasItem).is_visible_in_tree()


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
	for child in map_view.get_children():
		if child is Control and str(child.name).begins_with("RegionTile_"):
			if legend.get_global_rect().intersects((child as Control).get_global_rect()):
				return false
	return true


func _save_viewport(res_path: String) -> bool:
	var texture := root.get_texture()
	if texture == null:
		printerr("capture_task624_live_blocked_march: viewport texture null (use non-headless)")
		return false
	var image: Image = texture.get_image()
	if image == null:
		return false
	if image.get_width() != int(VIEWPORT_W) or image.get_height() != int(VIEWPORT_H):
		printerr("capture_task624_live_blocked_march: unexpected viewport size")
		return false
	return image.save_png(ProjectSettings.globalize_path(res_path)) == OK


func _fail(message: String, exit_code: int) -> void:
	printerr("capture_task624_live_blocked_march: ", message)
	quit(exit_code)
