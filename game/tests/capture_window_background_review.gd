extends SceneTree


## One-shot review capture for G100.1d (task-569). Run with a real display
## (not --headless): headless uses the dummy renderer and cannot sample pixels.
## Writes 1152×648 PNGs under res://screenshots/: fresh party, selected region,
## and visible battle after full-window parchment.

const MAIN_SCENE_PATH := "res://scenes/main.tscn"
const SnapshotModel = preload("res://scripts/snapshot_model.gd")
const PartyMapMark = preload("res://tests/party_map_mark_helpers.gd")
const VIEWPORT_W := 1152.0
const VIEWPORT_H := 648.0
const FRESH_PATH := "res://screenshots/task-569-fresh-1152x648.png"
const SELECTED_PATH := "res://screenshots/task-569-selected-region-1152x648.png"
const BATTLE_PATH := "res://screenshots/task-569-visible-battle-1152x648.png"

const REGION_PLAYER := "Gród Własny"
const REGION_NEUTRAL := "Puste Pole"
const REGION_AI := "Twierdza AI"


func _init() -> void:
	call_deferred("_run")


func _run() -> void:
	root.size = Vector2i(int(VIEWPORT_W), int(VIEWPORT_H))

	var scene: PackedScene = ResourceLoader.load(MAIN_SCENE_PATH) as PackedScene
	if scene == null:
		printerr("capture_window_background_review: cannot load main scene")
		quit(2)
		return

	var scene_root: Control = scene.instantiate() as Control
	if scene_root == null:
		printerr("capture_window_background_review: cannot instantiate main scene")
		quit(2)
		return

	root.add_child(scene_root)
	scene_root.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	scene_root.size = Vector2(VIEWPORT_W, VIEWPORT_H)

	for _i in 4:
		await process_frame

	if not scene_root.has_method("apply_model"):
		printerr("capture_window_background_review: Main.apply_model missing")
		quit(3)
		return

	var map_view: Node = scene_root.find_child("MapView", true, false)

	# 1) Fresh party — empty selection, no battle, full-window parchment.
	scene_root.call("apply_model", _model_full())
	for _i in 5:
		await process_frame
	if not _save_viewport(FRESH_PATH):
		quit(4)
		return
	print("CAPTURED ", FRESH_PATH)

	# 2) Selected player region — panel hierarchy + map target frame.
	await _click_region(map_view, REGION_PLAYER)
	for _i in 4:
		await process_frame
	if not _save_viewport(SELECTED_PATH):
		quit(5)
		return
	print("CAPTURED ", SELECTED_PATH)

	# 3) Visible battle — BattleView open; controls still on-screen.
	scene_root.call("apply_model", _model_with_battle())
	for _i in 5:
		await process_frame
	if not _save_viewport(BATTLE_PATH):
		quit(6)
		return
	print("CAPTURED ", BATTLE_PATH)
	quit(0)


func _save_viewport(res_path: String) -> bool:
	var tex = root.get_texture()
	if tex == null:
		printerr("capture_window_background_review: viewport texture null (use non-headless)")
		return false
	var img: Image = tex.get_image()
	if img == null:
		printerr("capture_window_background_review: get_image null")
		return false
	if img.get_width() != int(VIEWPORT_W) or img.get_height() != int(VIEWPORT_H):
		printerr(
			"capture_window_background_review: unexpected size %sx%s"
			% [img.get_width(), img.get_height()]
		)
		return false
	var abs_path := ProjectSettings.globalize_path(res_path)
	var err := img.save_png(abs_path)
	if err != OK:
		printerr("capture_window_background_review: save_png failed ", err, " ", abs_path)
		return false
	return true


func _model_full() -> SnapshotModel:
	var model := SnapshotModel.new()
	model.year = 1
	model.month = 1
	model.player_result = "ongoing"
	model.regions = [
		{
			"name": REGION_PLAYER,
			"col": 0,
			"row": 0,
			"owner": "player",
			"settlement": {"name": "Player Keep"},
			"party": {"owner": "player"},
		},
		{
			"name": REGION_NEUTRAL,
			"col": 1,
			"row": 0,
			"owner": null,
			"settlement": null,
			"party": null,
		},
		{
			"name": REGION_AI,
			"col": 2,
			"row": 0,
			"owner": "ai",
			"settlement": {"name": "AI Outpost"},
			"party": {"owner": "ai"},
		},
	]
	model.player_duchy_status = {"morale": 1, "settlements": 1, "parties": 1}
	model.player_party_region = REGION_PLAYER
	model.battle = null
	return model


func _model_with_battle() -> SnapshotModel:
	var model := _model_full()
	model.battle = {
		"result": "attacker_win",
		"hexes": [
			{"q": 0, "r": 0, "terrain": "Plains", "side": "attacker", "hp": 10},
			{"q": 1, "r": 0, "terrain": "Plains", "side": "defender", "hp": 8},
		],
	}
	return model


func _click_region(map_view: Node, region_name: String) -> void:
	if map_view == null:
		return
	var tile: Control = _find_region_tile(map_view, region_name)
	if tile == null:
		printerr("capture_window_background_review: tile missing for ", region_name)
		return
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
		return
	vp.push_input(press)
	vp.push_input(release)


func _find_region_tile(map_view: Node, region_name: String) -> Control:
	var label: Label = PartyMapMark.find_label_with_text(map_view, region_name)
	if label == null:
		return null
	return PartyMapMark.tile_control(label, map_view)
