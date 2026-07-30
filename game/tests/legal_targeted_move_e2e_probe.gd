extends SceneTree


## G97.1f e2e: legal targeted move via MapView selection + MarchButton on a
## live bridge. Public Main controls only — party mark, selection frame, panel
## and LastOrderStatusLabel after the JSONL→core→render path. Seed 73:
## muster lands the party on "player lands"; "player outpost" is the legal
## adjacent own settlement used by the bridge-level move gate (G97.1b).

const MAIN_SCENE_PATH := "res://scenes/main.tscn"
const BridgeClient = preload("res://scripts/bridge_client.gd")
const PartyMapMark = preload("res://tests/party_map_mark_helpers.gd")
const MapTargetFrame = preload("res://tests/map_target_frame_helpers.gd")
const PREFIX := "LEGAL_TARGETED_MOVE_E2E "
const VIEWPORT_W := 1152.0
const VIEWPORT_H := 648.0

const SOURCE_REGION := "player lands"
const TARGET_REGION := "player outpost"


func _init() -> void:
	call_deferred("_run")


func _run() -> void:
	var args := OS.get_cmdline_user_args()
	if args.size() != 4:
		_fail("expected command prefix, state path, request path and seed")
		return

	root.size = Vector2i(int(VIEWPORT_W), int(VIEWPORT_H))

	var scene_root := _instantiate_scene()
	if scene_root == null:
		return
	await process_frame
	await process_frame

	var client := BridgeClient.create_persistent(args[0], args[1], args[3].to_int(), args[2])
	scene_root.bind_client(client)
	await process_frame
	await process_frame

	var map_view: Node = scene_root.find_child("MapView", true, false)
	if map_view == null:
		_fail("missing MapView")
		return

	if not _press(scene_root, "MusterButton"):
		return
	await process_frame
	await process_frame
	var after_muster: Dictionary = _observe(scene_root, map_view)

	await _click_region(map_view, TARGET_REGION)
	await process_frame
	await process_frame
	var after_select: Dictionary = _observe(scene_root, map_view)

	if not _press(scene_root, "MarchButton"):
		return
	await process_frame
	await process_frame
	var after_move: Dictionary = _observe(scene_root, map_view)

	print(PREFIX, JSON.stringify({
		"source_region": SOURCE_REGION,
		"target_region": TARGET_REGION,
		"after_muster": after_muster,
		"after_select": after_select,
		"after_move": after_move,
		"state_exists": FileAccess.file_exists(args[1]),
		"session_command": client.session_command(),
	}))
	quit(0)


func _instantiate_scene() -> Control:
	var scene := ResourceLoader.load(MAIN_SCENE_PATH) as PackedScene
	if scene == null:
		_fail("cannot load main scene")
		return null
	var scene_root := scene.instantiate() as Control
	if scene_root == null:
		_fail("cannot instantiate main scene")
		return null
	root.add_child(scene_root)
	scene_root.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	scene_root.size = Vector2(VIEWPORT_W, VIEWPORT_H)
	return scene_root


func _press(scene_root: Control, button_name: String) -> bool:
	var button := scene_root.find_child(button_name, true, false) as Button
	if button == null:
		_fail("missing %s" % button_name)
		return false
	button.emit_signal("pressed")
	return true


func _observe(scene_root: Control, map_view: Node) -> Dictionary:
	var position_label := scene_root.find_child("PlayerPartyPositionLabel", true, false) as Label
	var status_label := scene_root.find_child("LastOrderStatusLabel", true, false) as Label
	var panel_label := scene_root.find_child("SelectedRegionDetailsLabel", true, false) as Label
	var march_button := scene_root.find_child("MarchButton", true, false) as Button
	var region_names: Array[String] = PartyMapMark.region_names_from_map(map_view)
	var selected := ""
	if map_view.get("selected_region_name") != null:
		selected = str(map_view.get("selected_region_name"))
	return {
		"position_label": "" if position_label == null else position_label.text,
		"order_status": "" if status_label == null else status_label.text,
		"panel_text": "" if panel_label == null else panel_label.text,
		"march_label": "" if march_button == null else march_button.text,
		"selected_region_name": selected,
		"marked_regions": PartyMapMark.marked_party_regions(map_view, region_names),
		"marker_count": PartyMapMark.count_party_markers(map_view),
		"frame_count": MapTargetFrame.count_target_frames(map_view),
		"framed_regions": MapTargetFrame.framed_regions(map_view, region_names),
		"region_names": region_names,
	}


func _click_region(map_view: Node, region_name: String) -> void:
	var tile: Control = _find_region_tile(map_view, region_name)
	if tile == null:
		_fail("missing tile for %s" % region_name)
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
		_fail("missing viewport for tile %s" % region_name)
		return
	vp.push_input(press)
	vp.push_input(release)


func _find_region_tile(map_view: Node, region_name: String) -> Control:
	var label: Label = PartyMapMark.find_label_with_text(map_view, region_name)
	if label == null:
		return null
	return PartyMapMark.tile_control(label, map_view)


func _fail(message: String) -> void:
	printerr("legal_targeted_move_e2e_probe: ", message)
	quit(2)
