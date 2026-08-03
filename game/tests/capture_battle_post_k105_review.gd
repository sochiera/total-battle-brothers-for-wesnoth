extends SceneTree


## One-shot review capture for G106.1c (task-593). Run with a real display
## (not --headless): headless uses the dummy renderer and cannot sample pixels.
## Writes 1152×648 PNG under res://screenshots/ for the visible battle after
## K105: five-region strategic chrome + BattleView with iso/¾ sides, PŻ
## badges, terrain decor, PL result banner, and K105.1c centered occupied
## cluster. Map and order bar remain on the same full-screen frame.

const MAIN_SCENE_PATH := "res://scenes/main.tscn"
const SnapshotModel = preload("res://scripts/snapshot_model.gd")
const VIEWPORT_W := 1152.0
const VIEWPORT_H := 648.0
const OUT_PATH := "res://screenshots/task-593-visible-battle-post-k105-1152x648.png"


func _init() -> void:
	call_deferred("_run")


func _run() -> void:
	root.size = Vector2i(int(VIEWPORT_W), int(VIEWPORT_H))

	var scene: PackedScene = ResourceLoader.load(MAIN_SCENE_PATH) as PackedScene
	if scene == null:
		printerr("capture_battle_post_k105_review: cannot load main scene")
		quit(2)
		return

	var scene_root: Control = scene.instantiate() as Control
	if scene_root == null:
		printerr("capture_battle_post_k105_review: cannot instantiate main scene")
		quit(2)
		return

	root.add_child(scene_root)
	scene_root.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	scene_root.size = Vector2(VIEWPORT_W, VIEWPORT_H)

	for _i in 4:
		await process_frame

	if not scene_root.has_method("apply_model"):
		printerr("capture_battle_post_k105_review: Main.apply_model missing")
		quit(3)
		return

	# Five-region post-K105 chrome + multi-hex battle (both sides, distinct hp,
	# terrain decor, PL result banner) — same battle field as G104/G105 captures.
	scene_root.call("apply_model", _model_five_regions_with_battle())
	for _i in 8:
		await process_frame

	var battle_view: CanvasItem = scene_root.find_child("BattleView", true, false) as CanvasItem
	if battle_view == null or not battle_view.is_visible_in_tree():
		printerr("capture_battle_post_k105_review: BattleView missing or hidden")
		quit(5)
		return

	# G106.1c: full chrome must fit the review frame — do not save a clipped proof.
	# OrderControls is the control container for both order rows (incl. save/load).
	if not _chrome_fully_inside_viewport(scene_root):
		quit(6)
		return

	if not _save_viewport(OUT_PATH):
		quit(4)
		return
	print("CAPTURED ", OUT_PATH)
	quit(0)


func _chrome_fully_inside_viewport(scene_root: Control) -> bool:
	var viewport := Rect2(0.0, 0.0, VIEWPORT_W, VIEWPORT_H)
	var tol := 1.0
	for control_name: String in ["OrderControls", "DateLabel", "SaveGameButton", "LoadGameButton"]:
		var node: Control = scene_root.find_child(control_name, true, false) as Control
		if node == null or not node.is_visible_in_tree():
			printerr(
				"capture_battle_post_k105_review: chrome control missing/hidden: ",
				control_name
			)
			return false
		var rect: Rect2 = node.get_global_rect()
		var inside := (
			rect.position.x >= viewport.position.x - tol
			and rect.position.y >= viewport.position.y - tol
			and rect.position.x + rect.size.x <= viewport.position.x + viewport.size.x + tol
			and rect.position.y + rect.size.y <= viewport.position.y + viewport.size.y + tol
		)
		if not inside:
			printerr(
				"capture_battle_post_k105_review: %s not fully inside %sx%s viewport, rect=%s"
				% [control_name, int(VIEWPORT_W), int(VIEWPORT_H), rect]
			)
			return false
	return true


func _save_viewport(res_path: String) -> bool:
	var tex = root.get_texture()
	if tex == null:
		printerr("capture_battle_post_k105_review: viewport texture null (use non-headless)")
		return false
	var img: Image = tex.get_image()
	if img == null:
		printerr("capture_battle_post_k105_review: get_image null")
		return false
	if img.get_width() != int(VIEWPORT_W) or img.get_height() != int(VIEWPORT_H):
		printerr(
			"capture_battle_post_k105_review: unexpected size %sx%s"
			% [img.get_width(), img.get_height()]
		)
		return false
	var abs_path := ProjectSettings.globalize_path(res_path)
	var err := img.save_png(abs_path)
	if err != OK:
		printerr("capture_battle_post_k105_review: save_png failed ", err, " ", abs_path)
		return false
	return true


func _model_five_regions_with_battle() -> SnapshotModel:
	## Same presentation strip as capture_fresh_post_k105_review (G106.1a), plus
	## battle payload matching capture_side_silhouettes_review / HP badge review:
	## attacker+defender sides, distinct hp for PŻ, Plains/Forest/Hills decor,
	## result attacker_win → PL banner. Empty/unknown hexes without side marks.
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
