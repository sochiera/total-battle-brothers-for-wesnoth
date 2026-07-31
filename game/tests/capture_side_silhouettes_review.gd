extends SceneTree


## One-shot review capture for G104.1c (task-585). Prefer a real display
## (not --headless) so the viewport can sample pixels. Writes 1152×648 PNGs
## under res://screenshots/: map with both army silhouettes, and battle with
## both side silhouettes + PŻ.

const MAIN_SCENE_PATH := "res://scenes/main.tscn"
const SnapshotModel = preload("res://scripts/snapshot_model.gd")
const VIEWPORT_W := 1152.0
const VIEWPORT_H := 648.0
const MAP_PATH := "res://screenshots/task-585-map-armies-1152x648.png"
const BATTLE_PATH := "res://screenshots/task-585-battle-sides-1152x648.png"

const REGION_PLAYER := "Gród Własny"
const REGION_NEUTRAL := "Puste Pole"
const REGION_AI := "Twierdza AI"


func _init() -> void:
	call_deferred("_run")


func _run() -> void:
	root.size = Vector2i(int(VIEWPORT_W), int(VIEWPORT_H))

	var scene: PackedScene = ResourceLoader.load(MAIN_SCENE_PATH) as PackedScene
	if scene == null:
		printerr("capture_side_silhouettes_review: cannot load main scene")
		quit(2)
		return

	var scene_root: Control = scene.instantiate() as Control
	if scene_root == null:
		printerr("capture_side_silhouettes_review: cannot instantiate main scene")
		quit(2)
		return

	root.add_child(scene_root)
	scene_root.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	scene_root.size = Vector2(VIEWPORT_W, VIEWPORT_H)

	for _i in 4:
		await process_frame

	if not scene_root.has_method("apply_model"):
		printerr("capture_side_silhouettes_review: Main.apply_model missing")
		quit(3)
		return

	# Map: both player and AI armies visible together.
	scene_root.call("apply_model", _model_map_both_armies())
	for _i in 6:
		await process_frame
	if not _save_viewport(MAP_PATH):
		quit(4)
		return
	print("CAPTURED ", MAP_PATH)

	# Battle: both sides with distinct hp for PŻ context.
	scene_root.call("apply_model", _model_with_battle_sides())
	for _i in 6:
		await process_frame
	var battle_view: CanvasItem = scene_root.find_child("BattleView", true, false) as CanvasItem
	if battle_view == null or not battle_view.is_visible_in_tree():
		printerr("capture_side_silhouettes_review: BattleView missing or hidden")
		quit(5)
		return
	if not _save_viewport(BATTLE_PATH):
		quit(6)
		return
	print("CAPTURED ", BATTLE_PATH)
	quit(0)


func _save_viewport(res_path: String) -> bool:
	var tex = root.get_texture()
	if tex == null:
		printerr("capture_side_silhouettes_review: viewport texture null (use non-headless)")
		return false
	var img: Image = tex.get_image()
	if img == null:
		printerr("capture_side_silhouettes_review: get_image null")
		return false
	if img.get_width() != int(VIEWPORT_W) or img.get_height() != int(VIEWPORT_H):
		printerr(
			"capture_side_silhouettes_review: unexpected size %sx%s"
			% [img.get_width(), img.get_height()]
		)
		return false
	var abs_path := ProjectSettings.globalize_path(res_path)
	var err := img.save_png(abs_path)
	if err != OK:
		printerr("capture_side_silhouettes_review: save_png failed ", err, " ", abs_path)
		return false
	return true


func _model_map_both_armies() -> SnapshotModel:
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


func _model_with_battle_sides() -> SnapshotModel:
	var model := _model_map_both_armies()
	model.battle = {
		"result": "attacker_win",
		"hexes": [
			{"q": 0, "r": 0, "terrain": "Plains", "side": "attacker", "hp": 10},
			{"q": 2, "r": 0, "terrain": "Plains", "side": "defender", "hp": 8},
			{"q": 0, "r": 1, "terrain": "Forest", "side": "attacker", "hp": 5},
			{"q": 0, "r": 2, "terrain": "Hills", "side": "attacker", "hp": 7},
			{"q": 2, "r": 2, "terrain": "Forest", "side": "defender", "hp": 6},
			{"q": 1, "r": 0, "terrain": "Plains", "side": "unknown", "hp": 1},
			{"q": 1, "r": 1, "terrain": "Hills", "side": "", "hp": 1},
		],
	}
	return model
