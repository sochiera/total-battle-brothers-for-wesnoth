extends SceneTree


## One-shot live review capture for G108.1d (task-606).
## The scene starts the real persistent bridge from TBB_* environment variables;
## five NextTurnButton presses are deliberately passive player turns. This
## script never constructs a SnapshotModel or mounts a presentation fixture.

const MAIN_SCENE_PATH := "res://scenes/main.tscn"
const VIEWPORT_W := 1152.0
const VIEWPORT_H := 648.0
const PASSIVE_TURNS := 5
const TARGET_REGION_ID := "border"
const AI_OWNER_ID := "ai"
const OUT_PATH := "res://screenshots/task-606-live-enemy-army-1152x648.png"


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
		_fail("live bridge did not start: %s" % ("missing status" if start_status == null else start_status.text), 3)
		return

	var next_turn := scene_root.find_child("NextTurnButton", true, false) as Button
	if next_turn == null:
		_fail("missing NextTurnButton", 3)
		return
	if next_turn.disabled:
		_fail("NextTurnButton is disabled before passive turns", 3)
		return

	for _turn in PASSIVE_TURNS:
		next_turn.emit_signal("pressed")
		await process_frame
		await process_frame

	if not _has_live_enemy_army(scene_root):
		_fail(
			"seed-73 live session has no rendered AI party in %s after %d passive turns; regions: %s"
			% [TARGET_REGION_ID, PASSIVE_TURNS, _region_summary(scene_root)],
			4
		)
		return

	if not _save_viewport(OUT_PATH):
		quit(5)
		return
	print("CAPTURED ", OUT_PATH)
	quit(0)


func _has_live_enemy_army(scene_root: Control) -> bool:
	var regions: Variant = scene_root.get("_current_regions")
	if not regions is Array:
		return false
	var has_model_party := false
	for region_variant in regions:
		if not region_variant is Dictionary:
			continue
		var region: Dictionary = region_variant
		var party: Variant = region.get("party")
		if region.get("name") == TARGET_REGION_ID and region.get("owner") == AI_OWNER_ID:
			has_model_party = (
				party is Dictionary
				and party.get("owner") == AI_OWNER_ID
				and int(party.get("size", 0)) > 0
			)
			break
	if not has_model_party:
		return false

	var map_view := scene_root.find_child("MapView", true, false) as Control
	if map_view == null:
		return false
	var region_tile := map_view.find_child("RegionTile_%s" % TARGET_REGION_ID, false, false)
	return region_tile != null and region_tile.find_child("AIPartyMarker", false, false) != null


func _region_summary(scene_root: Control) -> String:
	var regions: Variant = scene_root.get("_current_regions")
	if not regions is Array:
		return "unavailable"
	var summary: Array[String] = []
	for region_variant in regions:
		if not region_variant is Dictionary:
			continue
		var region: Dictionary = region_variant
		var party: Variant = region.get("party")
		var party_owner := "none"
		var party_size := 0
		if party is Dictionary:
			party_owner = str(party.get("owner", "missing"))
			party_size = int(party.get("size", 0))
		summary.append(
			"%s(owner=%s, party=%s:%d)"
			% [str(region.get("name", "missing")), str(region.get("owner", "missing")), party_owner, party_size]
		)
	return ", ".join(summary)


func _save_viewport(res_path: String) -> bool:
	var tex = root.get_texture()
	if tex == null:
		printerr("capture_task606_live_enemy_army: viewport texture null (use non-headless)")
		return false
	var img: Image = tex.get_image()
	if img == null:
		printerr("capture_task606_live_enemy_army: get_image null")
		return false
	if img.get_width() != int(VIEWPORT_W) or img.get_height() != int(VIEWPORT_H):
		printerr(
			"capture_task606_live_enemy_army: unexpected size %sx%s"
			% [img.get_width(), img.get_height()]
		)
		return false
	var abs_path := ProjectSettings.globalize_path(res_path)
	var err := img.save_png(abs_path)
	if err != OK:
		printerr("capture_task606_live_enemy_army: save_png failed ", err, " ", abs_path)
		return false
	return true


func _fail(message: String, exit_code: int) -> void:
	printerr("capture_task606_live_enemy_army: ", message)
	quit(exit_code)
