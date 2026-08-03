extends SceneTree


## One-shot review capture for G106.1b (task-592). Run with a real display
## (not --headless): headless uses the dummy renderer and cannot sample pixels.
## Writes 1152×648 PNG pair under res://screenshots/ for empty → selected
## region after K105: ornament + PL empty state, then map_target_frame + PL
## detail rows. Topology matches capture_fresh_post_k105_review (five-region
## strip with army marks on keeps). Empty frame is intentionally the same
## presentation state as task-591 (pair readability only). Fail closed if
## the player-region click does not stick — never write SELECTED_PATH empty.
## Selection semantics unchanged.

const MAIN_SCENE_PATH := "res://scenes/main.tscn"
const SnapshotModel = preload("res://scripts/snapshot_model.gd")
const PartyMapMark = preload("res://tests/party_map_mark_helpers.gd")
const VIEWPORT_W := 1152.0
const VIEWPORT_H := 648.0
const EMPTY_PATH := "res://screenshots/task-592-selected-region-empty-1152x648.png"
const SELECTED_PATH := "res://screenshots/task-592-selected-region-selected-1152x648.png"

## Canonical region name on the public five-region strip (player keep).
const REGION_PLAYER := "player lands"


func _init() -> void:
	call_deferred("_run")


func _run() -> void:
	root.size = Vector2i(int(VIEWPORT_W), int(VIEWPORT_H))

	var scene: PackedScene = ResourceLoader.load(MAIN_SCENE_PATH) as PackedScene
	if scene == null:
		printerr("capture_selected_region_post_k105_review: cannot load main scene")
		quit(2)
		return

	var scene_root: Control = scene.instantiate() as Control
	if scene_root == null:
		printerr("capture_selected_region_post_k105_review: cannot instantiate main scene")
		quit(2)
		return

	root.add_child(scene_root)
	scene_root.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	scene_root.size = Vector2(VIEWPORT_W, VIEWPORT_H)

	for _i in 4:
		await process_frame

	if not scene_root.has_method("apply_model"):
		printerr("capture_selected_region_post_k105_review: Main.apply_model missing")
		quit(3)
		return

	var map_view: Node = scene_root.find_child("MapView", true, false)
	scene_root.call("apply_model", _model_fresh_five_regions())
	for _i in 8:
		await process_frame

	# Empty selection: ornament + „Nie wybrano regionu” (post-K105 chrome).
	if not _save_viewport(EMPTY_PATH):
		quit(4)
		return
	print("CAPTURED ", EMPTY_PATH)

	# Selected player region: map_target_frame + PL detail rows; order bar stays.
	# Fail closed: never write SELECTED_PATH from an empty-selection frame.
	if not _click_region(map_view, REGION_PLAYER):
		quit(6)
		return
	for _i in 6:
		await process_frame
	if map_view == null or str(map_view.get("selected_region_name")) != REGION_PLAYER:
		printerr(
			"capture_selected_region_post_k105_review: selection not applied for ",
			REGION_PLAYER,
			" got ",
			null if map_view == null else map_view.get("selected_region_name")
		)
		quit(6)
		return
	if not _save_viewport(SELECTED_PATH):
		quit(5)
		return
	print("CAPTURED ", SELECTED_PATH)
	quit(0)


func _save_viewport(res_path: String) -> bool:
	var tex = root.get_texture()
	if tex == null:
		printerr("capture_selected_region_post_k105_review: viewport texture null (use non-headless)")
		return false
	var img: Image = tex.get_image()
	if img == null:
		printerr("capture_selected_region_post_k105_review: get_image null")
		return false
	if img.get_width() != int(VIEWPORT_W) or img.get_height() != int(VIEWPORT_H):
		printerr(
			"capture_selected_region_post_k105_review: unexpected size %sx%s"
			% [img.get_width(), img.get_height()]
		)
		return false
	var abs_path := ProjectSettings.globalize_path(res_path)
	var err := img.save_png(abs_path)
	if err != OK:
		printerr("capture_selected_region_post_k105_review: save_png failed ", err, " ", abs_path)
		return false
	return true


func _model_fresh_five_regions() -> SnapshotModel:
	## Same presentation model as capture_fresh_post_k105_review.gd (G106.1a):
	## five-region strip, parties on keeps for iso/¾ army marks, no battle.
	var model := SnapshotModel.new()
	model.year = 1
	model.month = 1
	model.player_result = "ongoing"
	model.regions = [
		{
			"name": "player lands",
			"col": 0,
			"row": 0,
			"owner": "player",
			"settlement": {"name": "Player Keep"},
			"party": {"owner": "player"},
		},
		{
			"name": "player outpost",
			"col": 1,
			"row": 0,
			"owner": "player",
			"settlement": {"name": "Player Outpost"},
			"party": null,
		},
		{
			"name": "border",
			"col": 2,
			"row": 0,
			"owner": null,
			"settlement": null,
			"party": null,
		},
		{
			"name": "ai outpost",
			"col": 3,
			"row": 0,
			"owner": "ai",
			"settlement": {"name": "AI Outpost"},
			"party": null,
		},
		{
			"name": "ai lands",
			"col": 4,
			"row": 0,
			"owner": "ai",
			"settlement": {"name": "AI Keep"},
			"party": {"owner": "ai"},
		},
	]
	model.player_duchy_status = {"morale": 1, "settlements": 2, "parties": 1}
	model.player_party_region = "player lands"
	model.battle = null
	return model


func _click_region(map_view: Node, region_name: String) -> bool:
	if map_view == null:
		printerr("capture_selected_region_post_k105_review: MapView missing")
		return false
	var tile: Control = _find_region_tile(map_view, region_name)
	if tile == null:
		printerr("capture_selected_region_post_k105_review: tile missing for ", region_name)
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
	var vp: Viewport = tile.get_viewport()
	if vp == null:
		printerr("capture_selected_region_post_k105_review: viewport missing for tile ", region_name)
		return false
	vp.push_input(press)
	vp.push_input(release)
	return true


func _find_region_tile(map_view: Node, region_name: String) -> Control:
	var label: Label = PartyMapMark.find_label_with_text(map_view, region_name)
	if label == null:
		return null
	return PartyMapMark.tile_control(label, map_view)
