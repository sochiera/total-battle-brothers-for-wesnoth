extends SceneTree


## One-shot review capture for G103.1c (task-581). Prefer a real display
## (not --headless) so the viewport can sample pixels. Writes 1152×648 PNG
## under res://screenshots/ showing five regions with three ground variants,
## settlements, armies and PL labels on the muted parchment hexes.

const MAIN_SCENE_PATH := "res://scenes/main.tscn"
const SnapshotModel = preload("res://scripts/snapshot_model.gd")
const VIEWPORT_W := 1152.0
const VIEWPORT_H := 648.0
const OUT_PATH := "res://screenshots/task-581-map-grounds-1152x648.png"


func _init() -> void:
	call_deferred("_run")


func _run() -> void:
	root.size = Vector2i(int(VIEWPORT_W), int(VIEWPORT_H))

	var scene: PackedScene = ResourceLoader.load(MAIN_SCENE_PATH) as PackedScene
	if scene == null:
		printerr("capture_map_grounds_review: cannot load main scene")
		quit(2)
		return

	var scene_root: Control = scene.instantiate() as Control
	if scene_root == null:
		printerr("capture_map_grounds_review: cannot instantiate main scene")
		quit(2)
		return

	root.add_child(scene_root)
	scene_root.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	scene_root.size = Vector2(VIEWPORT_W, VIEWPORT_H)

	for _i in 4:
		await process_frame

	if not scene_root.has_method("apply_model"):
		printerr("capture_map_grounds_review: Main.apply_model missing")
		quit(3)
		return

	scene_root.call("apply_model", _model_five_regions())
	for _i in 6:
		await process_frame

	if not _save_viewport(OUT_PATH):
		quit(4)
		return
	print("CAPTURED ", OUT_PATH)
	quit(0)


func _save_viewport(res_path: String) -> bool:
	var tex = root.get_texture()
	if tex == null:
		printerr("capture_map_grounds_review: viewport texture null (use non-headless)")
		return false
	var img: Image = tex.get_image()
	if img == null:
		printerr("capture_map_grounds_review: get_image null")
		return false
	if img.get_width() != int(VIEWPORT_W) or img.get_height() != int(VIEWPORT_H):
		printerr(
			"capture_map_grounds_review: unexpected size %sx%s"
			% [img.get_width(), img.get_height()]
		)
		return false
	var abs_path := ProjectSettings.globalize_path(res_path)
	var err := img.save_png(abs_path)
	if err != OK:
		printerr("capture_map_grounds_review: save_png failed ", err, " ", abs_path)
		return false
	return true


func _model_five_regions() -> SnapshotModel:
	# Five regions; col+2*row mod 3 hits grass/earth/stone for visual variety.
	var model := SnapshotModel.new()
	model.year = 1
	model.month = 1
	model.player_result = "ongoing"
	model.regions = [
		{
			"name": "Łąka Zachodnia",
			"col": 0,
			"row": 0,
			"owner": "player",
			"settlement": {"name": "Player Keep"},
			"party": {"owner": "player"},
		},
		{
			"name": "Ugór Środkowy",
			"col": 1,
			"row": 0,
			"owner": null,
			"settlement": null,
			"party": null,
		},
		{
			"name": "Kamienny Brzeg",
			"col": 2,
			"row": 0,
			"owner": "ai",
			"settlement": {"name": "AI outpost"},
			"party": {"owner": "ai"},
		},
		{
			"name": "Pastwisko Dolne",
			"col": 0,
			"row": 1,
			"owner": "player",
			"settlement": {"name": "village"},
			"party": null,
		},
		{
			"name": "Grzbiet Wschodni",
			"col": 1,
			"row": 1,
			"owner": "ai",
			"settlement": {"name": "AI Keep"},
			"party": {"owner": "ai"},
		},
	]
	model.player_duchy_status = {"morale": 1, "settlements": 2, "parties": 1}
	model.player_party_region = "Łąka Zachodnia"
	model.battle = null
	return model
