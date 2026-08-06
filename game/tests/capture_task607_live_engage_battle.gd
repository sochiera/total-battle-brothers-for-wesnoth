extends SceneTree


## One-shot live review capture for G108.1d (task-607).
## The scene starts the real persistent bridge from TBB_* environment variables,
## then drives one coherent seed-73 session to a resolved Engage battle. This
## script never constructs a SnapshotModel or mounts a presentation fixture.

const MAIN_SCENE_PATH := "res://scenes/main.tscn"
const VIEWPORT_W := 1152.0
const VIEWPORT_H := 648.0
const PASSIVE_TURNS := 5
const ENEMY_REGION_ID := "border"
const PLAYER_OUTPOST_ID := "player outpost"
const AI_OWNER_ID := "ai"
const PLAYER_OWNER_ID := "player"
const OUT_PATH := "res://screenshots/task-607-live-engage-battle-1152x648.png"


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
		if not await _press_button(scene_root, "NextTurnButton", 3):
			return

	if not _marker_visible_at(scene_root, ENEMY_REGION_ID, "AIPartyMarker"):
		_fail(
			"seed-73 live session has no rendered AI party in %s after %d passive turns; regions: %s"
			% [ENEMY_REGION_ID, PASSIVE_TURNS, _region_summary(scene_root)],
			4
		)
		return

	if not await _press_button(scene_root, "MusterButton", 5):
		return
	var map_view := scene_root.find_child("MapView", true, false) as Control
	if not _click_region(map_view, PLAYER_OUTPOST_ID):
		_fail("cannot select %s on the live map" % PLAYER_OUTPOST_ID, 6)
		return
	await process_frame
	await process_frame

	if not await _press_button(scene_root, "MarchButton", 7):
		return
	if not _marker_visible_at(scene_root, PLAYER_OUTPOST_ID, "PlayerPartyMarker"):
		_fail(
			"live move did not reach %s; regions: %s"
			% [PLAYER_OUTPOST_ID, _region_summary(scene_root)],
			8
		)
		return

	if not await _press_button(scene_root, "EngageButton", 9):
		return
	if not _has_resolved_battle(scene_root):
		_fail("Engage did not render a resolved battle", 10)
		return
	if not _has_readable_strategic_chrome(scene_root):
		_fail("Engage pushed strategic chrome outside the viewport or over map tiles", 11)
		return

	if not _save_viewport(OUT_PATH):
		quit(12)
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


func _marker_visible_at(scene_root: Control, region_id: String, marker_name: String) -> bool:
	var map_view := scene_root.find_child("MapView", true, false) as Control
	if map_view == null:
		return false
	var tile := map_view.find_child("RegionTile_%s" % region_id, false, false)
	var marker := null if tile == null else tile.find_child(marker_name, false, false)
	return marker is CanvasItem and (marker as CanvasItem).is_visible_in_tree()


func _has_resolved_battle(scene_root: Control) -> bool:
	var battle_view := scene_root.find_child("BattleView", true, false) as Control
	if battle_view == null or not battle_view.is_visible_in_tree():
		return false
	var result_label := battle_view.find_child("BattleResultLabel", true, false) as Label
	if result_label == null or result_label.text.strip_edges().is_empty():
		return false
	var lowered := result_label.text.strip_edges().to_lower()
	if not (lowered.contains("zwycięstwo") or lowered.contains("porażka") or lowered.contains("remis")):
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
	## The live Engage capture must retain its complete strategic chrome: map,
	## status card and order bar fit the viewport; the legend stays inside MapView
	## and clear of all region tiles.
	var map_view := scene_root.find_child("MapView", true, false) as Control
	var status_controls := scene_root.find_child("StatusControls", true, false) as Control
	var order_controls := scene_root.find_child("OrderControls", true, false) as Control
	if map_view == null or status_controls == null or order_controls == null:
		return false
	var viewport_rect := Rect2(Vector2.ZERO, Vector2(VIEWPORT_W, VIEWPORT_H))
	var map_rect := map_view.get_global_rect()
	if (
		not viewport_rect.encloses(map_rect)
		or map_rect.position.y <= 0.0
		or not viewport_rect.encloses(status_controls.get_global_rect())
		or not viewport_rect.encloses(order_controls.get_global_rect())
	):
		return false
	var legend := map_view.find_child("OwnerLegend", true, false) as Control
	if legend == null or not map_rect.encloses(legend.get_global_rect()):
		return false
	for child in map_view.get_children():
		if child is Control and str(child.name).begins_with("RegionTile_"):
			if legend.get_global_rect().intersects((child as Control).get_global_rect()):
				return false
	return true


func _region_summary(scene_root: Control) -> String:
	var map_view := scene_root.find_child("MapView", true, false) as Control
	if map_view == null:
		return "unavailable"
	var summary: Array[String] = []
	for region_name in [ENEMY_REGION_ID, PLAYER_OUTPOST_ID]:
		var tile := map_view.find_child("RegionTile_%s" % region_name, false, false)
		if tile == null:
			summary.append("%s(missing)" % region_name)
			continue
		var markers: Array[String] = []
		for marker_name in ["PlayerPartyMarker", "AIPartyMarker"]:
			var marker := tile.find_child(marker_name, false, false)
			if marker is CanvasItem and (marker as CanvasItem).is_visible_in_tree():
				markers.append(marker_name)
		summary.append("%s(markers=%s)" % [region_name, "+".join(markers)])
	return ", ".join(summary)


func _save_viewport(res_path: String) -> bool:
	var tex = root.get_texture()
	if tex == null:
		printerr("capture_task607_live_engage_battle: viewport texture null (use non-headless)")
		return false
	var img: Image = tex.get_image()
	if img == null:
		printerr("capture_task607_live_engage_battle: get_image null")
		return false
	if img.get_width() != int(VIEWPORT_W) or img.get_height() != int(VIEWPORT_H):
		printerr(
			"capture_task607_live_engage_battle: unexpected size %sx%s"
			% [img.get_width(), img.get_height()]
		)
		return false
	var abs_path := ProjectSettings.globalize_path(res_path)
	var err := img.save_png(abs_path)
	if err != OK:
		printerr("capture_task607_live_engage_battle: save_png failed ", err, " ", abs_path)
		return false
	return true


func _fail(message: String, exit_code: int) -> void:
	printerr("capture_task607_live_engage_battle: ", message)
	quit(exit_code)
