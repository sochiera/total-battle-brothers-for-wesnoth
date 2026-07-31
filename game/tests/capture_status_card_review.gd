extends SceneTree


## One-shot review capture for G101.1c (task-572). Run with a real display
## (not --headless): headless uses the dummy renderer and cannot sample pixels.
## Writes 1152×648 PNGs under res://screenshots/: fresh ongoing status hierarchy
## and finished-party (victory) result styling. Also prints layout fit JSON for
## map / battle / order controls so coders can confirm nothing is pushed off-screen.

const MAIN_SCENE_PATH := "res://scenes/main.tscn"
const SnapshotModel = preload("res://scripts/snapshot_model.gd")
const VIEWPORT_W := 1152.0
const VIEWPORT_H := 648.0
const FRESH_PATH := "res://screenshots/task-572-status-fresh-1152x648.png"
const FINISHED_PATH := "res://screenshots/task-572-status-finished-1152x648.png"

const REGION_PLAYER := "Gród Własny"
const REGION_NEUTRAL := "Puste Pole"
const REGION_AI := "Twierdza AI"

const FIT_CONTROL_NAMES: Array[String] = [
	"StatusControls",
	"MapView",
	"BattleView",
	"OrderControls",
	"NextTurnButton",
	"DevelopButton",
	"RecruitButton",
	"MusterButton",
	"MarchButton",
	"AssaultButton",
	"SaveGameButton",
	"LoadGameButton",
	"DateLabel",
	"ResultLabel",
	"MoraleValueLabel",
	"SettlementsValueLabel",
	"PartiesValueLabel",
	"PlayerPartyPositionLabel",
	"SelectedRegionPanel",
]


func _init() -> void:
	call_deferred("_run")


func _run() -> void:
	root.size = Vector2i(int(VIEWPORT_W), int(VIEWPORT_H))

	var scene: PackedScene = ResourceLoader.load(MAIN_SCENE_PATH) as PackedScene
	if scene == null:
		printerr("capture_status_card_review: cannot load main scene")
		quit(2)
		return

	var scene_root: Control = scene.instantiate() as Control
	if scene_root == null:
		printerr("capture_status_card_review: cannot instantiate main scene")
		quit(2)
		return

	root.add_child(scene_root)
	scene_root.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	scene_root.size = Vector2(VIEWPORT_W, VIEWPORT_H)

	for _i in 4:
		await process_frame

	if not scene_root.has_method("apply_model"):
		printerr("capture_status_card_review: Main.apply_model missing")
		quit(3)
		return

	# 1) Fresh party — ongoing result, hierarchy rows visible, no battle.
	scene_root.call("apply_model", _model_fresh())
	for _i in 5:
		await process_frame
	var fresh_fit: Dictionary = _layout_fit_report(scene_root)
	print("STATUS_CARD_LAYOUT fresh ", JSON.stringify(fresh_fit))
	if not bool(fresh_fit.get("all_inside", false)):
		printerr("capture_status_card_review: fresh layout overflows viewport")
		quit(6)
		return
	if not _save_viewport(FRESH_PATH):
		quit(4)
		return
	print("CAPTURED ", FRESH_PATH)

	# 2) Finished party — victory styling of Wynik row (human review of hierarchy).
	scene_root.call("apply_model", _model_finished_victory())
	for _i in 5:
		await process_frame
	var finished_fit: Dictionary = _layout_fit_report(scene_root)
	print("STATUS_CARD_LAYOUT finished ", JSON.stringify(finished_fit))
	if not bool(finished_fit.get("all_inside", false)):
		printerr("capture_status_card_review: finished layout overflows viewport")
		quit(7)
		return
	if not _save_viewport(FINISHED_PATH):
		quit(5)
		return
	print("CAPTURED ", FINISHED_PATH)
	quit(0)


func _save_viewport(res_path: String) -> bool:
	var tex = root.get_texture()
	if tex == null:
		printerr("capture_status_card_review: viewport texture null (use non-headless)")
		return false
	var img: Image = tex.get_image()
	if img == null:
		printerr("capture_status_card_review: get_image null")
		return false
	if img.get_width() != int(VIEWPORT_W) or img.get_height() != int(VIEWPORT_H):
		printerr(
			"capture_status_card_review: unexpected size %sx%s"
			% [img.get_width(), img.get_height()]
		)
		return false
	var abs_path := ProjectSettings.globalize_path(res_path)
	var err := img.save_png(abs_path)
	if err != OK:
		printerr("capture_status_card_review: save_png failed ", err, " ", abs_path)
		return false
	return true


func _layout_fit_report(scene_root: Node) -> Dictionary:
	var controls: Dictionary = {}
	var all_inside := true
	for control_name: String in FIT_CONTROL_NAMES:
		var node: Control = scene_root.find_child(control_name, true, false) as Control
		if node == null:
			controls[control_name] = null
			continue
		var rect: Rect2 = node.get_global_rect()
		var entry := {
			"x": rect.position.x,
			"y": rect.position.y,
			"w": rect.size.x,
			"h": rect.size.y,
			"visible": node.visible,
		}
		var takes_space: bool = (
			node.visible
			and rect.size.x > 0.5
			and rect.size.y > 0.5
		)
		var inside: bool = (
			not takes_space
			or (
				rect.position.x >= -0.5
				and rect.position.y >= -0.5
				and rect.position.x + rect.size.x <= VIEWPORT_W + 0.5
				and rect.position.y + rect.size.y <= VIEWPORT_H + 0.5
			)
		)
		entry["inside_viewport"] = inside
		if not inside:
			all_inside = false
		controls[control_name] = entry
	return {
		"viewport": {"w": VIEWPORT_W, "h": VIEWPORT_H},
		"all_inside": all_inside,
		"controls": controls,
	}


func _model_fresh() -> SnapshotModel:
	var model := SnapshotModel.new()
	model.year = 1
	model.month = 1
	model.player_result = "ongoing"
	model.regions = _regions()
	model.player_duchy_status = {"morale": 1, "settlements": 1, "parties": 1}
	model.player_party_region = REGION_PLAYER
	model.battle = null
	return model


func _model_finished_victory() -> SnapshotModel:
	var model := _model_fresh()
	model.year = 3
	model.month = 8
	model.player_result = "victory"
	model.player_duchy_status = {"morale": 4, "settlements": 3, "parties": 2}
	return model


func _regions() -> Array:
	return [
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
