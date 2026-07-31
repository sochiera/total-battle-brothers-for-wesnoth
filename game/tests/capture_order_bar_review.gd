extends SceneTree


## One-shot review capture for G103.1a (task-579). Run with a real display
## (not --headless): headless uses the dummy renderer and cannot sample pixels.
## Writes 1152×648 PNGs under res://screenshots/.

const MAIN_SCENE_PATH := "res://scenes/main.tscn"
const SnapshotModel = preload("res://scripts/snapshot_model.gd")
const VIEWPORT_W := 1152.0
const VIEWPORT_H := 648.0
const FRESH_PATH := "res://screenshots/task-579-fresh-order-states-1152x648.png"
const BATTLE_PATH := "res://screenshots/task-579-visible-battle-1152x648.png"

const HOVER_DEMO := ["RecruitButton", "MusterButton", "LoadGameButton"]
const PRESSED_DEMO := ["MarchButton", "AssaultButton", "SaveGameButton"]


func _init() -> void:
	call_deferred("_run")


func _run() -> void:
	root.size = Vector2i(int(VIEWPORT_W), int(VIEWPORT_H))

	var scene: PackedScene = ResourceLoader.load(MAIN_SCENE_PATH) as PackedScene
	if scene == null:
		printerr("capture_order_bar_review: cannot load main scene")
		quit(2)
		return

	var scene_root: Node = scene.instantiate()
	if scene_root == null:
		printerr("capture_order_bar_review: cannot instantiate main scene")
		quit(2)
		return

	root.add_child(scene_root)
	if scene_root is Control:
		var main_ctrl: Control = scene_root as Control
		main_ctrl.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
		main_ctrl.size = Vector2(VIEWPORT_W, VIEWPORT_H)

	for _i in 4:
		await process_frame

	if not scene_root.has_method("apply_model"):
		printerr("capture_order_bar_review: Main.apply_model missing")
		quit(3)
		return

	# Fresh party: show normal / hover / pressed surfaces on distinct buttons.
	scene_root.call("apply_model", _model_without_battle())
	for _i in 4:
		await process_frame
	_apply_demo_button_states(scene_root)
	for _i in 3:
		await process_frame
	if not _save_viewport(FRESH_PATH):
		quit(4)
		return
	print("CAPTURED ", FRESH_PATH)

	# Restore real styles, then show complete bar with battle view open.
	_restore_button_states(scene_root)
	scene_root.call("apply_model", _model_with_battle())
	for _i in 5:
		await process_frame
	if not _save_viewport(BATTLE_PATH):
		quit(5)
		return
	print("CAPTURED ", BATTLE_PATH)
	quit(0)


func _save_viewport(res_path: String) -> bool:
	var tex = root.get_texture()
	if tex == null:
		printerr("capture_order_bar_review: viewport texture null (use non-headless)")
		return false
	var img: Image = tex.get_image()
	if img == null:
		printerr("capture_order_bar_review: get_image null")
		return false
	if img.get_width() != int(VIEWPORT_W) or img.get_height() != int(VIEWPORT_H):
		printerr(
			"capture_order_bar_review: unexpected size %sx%s"
			% [img.get_width(), img.get_height()]
		)
		return false
	var abs_path := ProjectSettings.globalize_path(res_path)
	var err := img.save_png(abs_path)
	if err != OK:
		printerr("capture_order_bar_review: save_png failed ", err, " ", abs_path)
		return false
	return true


func _apply_demo_button_states(scene_root: Node) -> void:
	## Paint selected buttons with hover/pressed StyleBox as their normal surface
	## so one still frame documents all three public interaction looks.
	for button_name: String in HOVER_DEMO:
		var button: Button = scene_root.find_child(button_name, true, false) as Button
		if button == null:
			continue
		var hover: StyleBox = button.get_theme_stylebox("hover")
		if hover != null:
			button.add_theme_stylebox_override("normal", hover.duplicate())
		button.add_theme_color_override(
			"font_color", button.get_theme_color("font_hover_color")
		)
	for button_name: String in PRESSED_DEMO:
		var button2: Button = scene_root.find_child(button_name, true, false) as Button
		if button2 == null:
			continue
		var pressed: StyleBox = button2.get_theme_stylebox("pressed")
		if pressed != null:
			button2.add_theme_stylebox_override("normal", pressed.duplicate())
		button2.add_theme_color_override(
			"font_color", button2.get_theme_color("font_pressed_color")
		)
		button2.button_pressed = true


func _restore_button_states(scene_root: Node) -> void:
	if scene_root.has_method("_apply_order_button_state_styles"):
		scene_root.call("_apply_order_button_state_styles")
	for button_name: String in PRESSED_DEMO:
		var button: Button = scene_root.find_child(button_name, true, false) as Button
		if button != null:
			button.button_pressed = false


func _model_without_battle() -> SnapshotModel:
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
		},
		{
			"name": "player outpost",
			"col": 1,
			"row": 0,
			"owner": "player",
			"settlement": {"name": "Player Outpost"},
		},
		{"name": "border", "col": 2, "row": 0, "owner": null, "settlement": null},
		{
			"name": "ai outpost",
			"col": 3,
			"row": 0,
			"owner": "ai",
			"settlement": {"name": "AI Outpost"},
		},
		{
			"name": "ai lands",
			"col": 4,
			"row": 0,
			"owner": "ai",
			"settlement": {"name": "AI Keep"},
		},
	]
	model.player_duchy_status = {"morale": 1, "settlements": 2, "parties": 1}
	model.player_party_region = "player lands"
	model.battle = null
	return model


func _model_with_battle() -> SnapshotModel:
	var model := _model_without_battle()
	model.battle = {
		"result": "attacker_win",
		"hexes": [
			{"q": 0, "r": 0, "terrain": "Plains", "side": "attacker", "hp": 10},
			{"q": 1, "r": 0, "terrain": "Plains", "side": "defender", "hp": 8},
		],
	}
	return model
