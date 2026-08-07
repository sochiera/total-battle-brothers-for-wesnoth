extends SceneTree


## One-shot live review capture for G110.1c (task-619).
## Runs the same seed-73 bridge sequence as the natural assault e2e and saves
## the enemy-settlement frame immediately before assault and the captured,
## resolved-battle frame immediately after it.

const MAIN_SCENE_PATH := "res://scenes/main.tscn"
const AssaultPrecondition = preload("res://tests/persistent_assault_precondition.gd")
const VIEWPORT_W := 1152.0
const VIEWPORT_H := 648.0
const PLAYER_PARTY_REGION_ID := "border"
const TARGET_REGION_ID := "ai outpost"
const BEFORE_PATH := "res://screenshots/task-619-live-assault-before-1152x648.png"
const AFTER_PATH := "res://screenshots/task-619-live-assault-after-1152x648.png"
const EXPECTED_STATUS_PREFIX := "Szturm: zwycięstwo"
const REVIEW_BUTTONS := [
	"NextTurnButton",
	"DevelopButton",
	"RecruitButton",
	"MusterButton",
	"MarchButton",
	"AssaultButton",
	"EngageButton",
	"SaveGameButton",
	"LoadGameButton",
	"NewGameButton",
]


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

	var staging := AssaultPrecondition.stage_live_frontier(scene_root)
	if not staging.get("ok", false):
		_fail("live frontier staging failed: %s" % staging, 4)
		return
	for _i in 2:
		await process_frame

	var client: Variant = scene_root.get("_client")
	var precondition := AssaultPrecondition.inspect(client)
	if not precondition.get("ready", false):
		_fail("assault precondition failed: %s" % precondition, 8)
		return

	var map_view := scene_root.find_child("MapView", true, false) as Control
	if not _click_region(map_view, TARGET_REGION_ID):
		_fail("cannot select %s" % TARGET_REGION_ID, 9)
		return
	await process_frame
	await process_frame
	if not _has_enemy_settlement_frame(scene_root) or not _has_review_chrome(scene_root):
		_fail("before frame does not show the enemy settlement position", 10)
		return
	if not _save_viewport(BEFORE_PATH):
		quit(11)
		return

	if not await _press_button(scene_root, "AssaultButton", 12):
		return
	# Let the container settle the direct render-path fit before checking or
	# capturing the frame.
	for _i in 3:
		await process_frame
	if not _has_captured_battle_frame(scene_root):
		_fail("after frame does not show captured region and resolved assault", 13)
		return
	if not _save_viewport(AFTER_PATH):
		quit(14)
		return

	print("CAPTURED ", BEFORE_PATH)
	print("CAPTURED ", AFTER_PATH)
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


func _has_enemy_settlement_frame(scene_root: Control) -> bool:
	var map_view := scene_root.find_child("MapView", true, false) as Control
	var tile := null if map_view == null else map_view.find_child(
		"RegionTile_%s" % TARGET_REGION_ID, false, false
	)
	if tile == null:
		return false
	var settlement := tile.find_child("Settlement", false, false)
	var ownership_mark := tile.find_child("OwnershipMark", false, false)
	var party_tile := map_view.find_child(
		"RegionTile_%s" % PLAYER_PARTY_REGION_ID, false, false
	) if map_view != null else null
	var party := null if party_tile == null else party_tile.find_child(
		"PlayerPartyMarker", false, false
	)
	return settlement is CanvasItem and ownership_mark is CanvasItem \
		and ownership_mark.get_meta("owner_kind", "") == "ai" \
		and party is CanvasItem \
		and (settlement as CanvasItem).is_visible_in_tree() \
		and (ownership_mark as CanvasItem).is_visible_in_tree() \
		and (party as CanvasItem).is_visible_in_tree()


func _has_captured_battle_frame(scene_root: Control) -> bool:
	if not _has_review_chrome(scene_root):
		return false
	var status := scene_root.find_child("LastOrderStatusLabel", true, false) as Label
	if status == null or not status.text.begins_with(EXPECTED_STATUS_PREFIX):
		return false
	var battle_view := scene_root.find_child("BattleView", true, false) as Control
	if battle_view == null or not battle_view.is_visible_in_tree():
		return false
	var result := battle_view.find_child("BattleResultLabel", true, false) as Label
	if result == null or result.text.strip_edges().is_empty():
		return false
	var map_view := scene_root.find_child("MapView", true, false) as Control
	if map_view == null:
		return false
	var tile := null if map_view == null else map_view.find_child(
		"RegionTile_%s" % TARGET_REGION_ID, false, false
	)
	var owner_mark := null if tile == null else tile.find_child("Settlement", false, false)
	var ownership_mark := null if tile == null else tile.find_child("OwnershipMark", false, false)
	return owner_mark is CanvasItem and (owner_mark as CanvasItem).is_visible_in_tree() \
		and ownership_mark is CanvasItem \
		and (ownership_mark as CanvasItem).is_visible_in_tree() \
		and ownership_mark.get_meta("owner_kind", "") == "player"


func _has_review_chrome(scene_root: Control) -> bool:
	for node_name in ["MapView", "OwnerLegend", "StatusControls", "OrderControls"]:
		var node := scene_root.find_child(node_name, true, false) as Control
		if node == null or not node.is_visible_in_tree() or not _fits_viewport(node):
			return false
	for button_name in REVIEW_BUTTONS:
		var button := scene_root.find_child(button_name, true, false) as Button
		if button == null or not button.is_visible_in_tree() or not _fits_viewport(button):
			return false
	return true


func _fits_viewport(control: Control) -> bool:
	var rect := control.get_global_rect()
	return (
		rect.position.x >= -1.0
		and rect.position.y >= -1.0
		and rect.end.x <= VIEWPORT_W + 1.0
		and rect.end.y <= VIEWPORT_H + 1.0
	)


func _save_viewport(res_path: String) -> bool:
	var texture := root.get_texture()
	if texture == null:
		printerr("capture_task619_live_assault: viewport texture null (use non-headless)")
		return false
	var image: Image = texture.get_image()
	if image == null:
		printerr("capture_task619_live_assault: get_image null")
		return false
	if image.get_width() != int(VIEWPORT_W) or image.get_height() != int(VIEWPORT_H):
		printerr("capture_task619_live_assault: unexpected size %sx%s" % [image.get_width(), image.get_height()])
		return false
	var abs_path := ProjectSettings.globalize_path(res_path)
	return image.save_png(abs_path) == OK


func _fail(message: String, exit_code: int) -> void:
	printerr("capture_task619_live_assault: ", message)
	quit(exit_code)
