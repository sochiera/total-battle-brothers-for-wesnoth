extends SceneTree


## G89.1b-4 / G91.1b / G92.2a e2e: natural recruit → muster → march →
## next_turn → engage →
## assault on a live bridge process must end with a readable battle outcome,
## map ownership of the captured frontier keep (ai outpost), and resume of
## that state. Multi-keep world keeps the campaign ongoing after one capture.

const MAIN_SCENE_PATH := "res://scenes/main.tscn"
const BridgeClient = preload("res://scripts/bridge_client.gd")
const PartyMapMark = preload("res://tests/party_map_mark_helpers.gd")
const AssaultPrecondition = preload("res://tests/persistent_assault_precondition.gd")
const PREFIX := "PERSISTENT_NATURAL_ASSAULT "
const PLAYER_LANDS := "player lands"
const AI_OUTPOST := "ai outpost"


func _init() -> void:
	call_deferred("_run")


func _run() -> void:
	var args := OS.get_cmdline_user_args()
	if args.size() != 5:
		_fail("expected command prefix, state path, request path, seed and phase")
		return
	var scene_root := _instantiate_scene()
	if scene_root == null:
		return
	await process_frame
	await process_frame

	var client := BridgeClient.create_persistent(args[0], args[1], args[3].to_int(), args[2])
	scene_root.bind_client(client)
	await process_frame
	await process_frame

	var phase: String = args[4]
	var order_results: Array = []
	var after_start: Dictionary = {}
	var assault_precondition: Dictionary = {}
	match phase:
		"play":
			after_start = _observation(scene_root)
			# One military move per month; next_turn resets the marker before the
			# player engages the AI party on the border and assaults the keep.
			for button_name in ["RecruitButton", "MusterButton", "MarchButton"]:
				if not _press(scene_root, button_name):
					return
				order_results.append(client.last_order_result())
			# Three passive AI turns are the smallest seed-73 staging window that
			# leaves the frontier garrison alive after Engage clears its field party.
			for _turn in range(AssaultPrecondition.NEXT_TURNS_TO_STAGE_LIVE_FRONTIER):
				if not _press(scene_root, "NextTurnButton"):
					return
				order_results.append(client.last_order_result())
			for button_name in ["EngageButton"]:
				if not _press(scene_root, button_name):
					return
				order_results.append(client.last_order_result())
			assault_precondition = AssaultPrecondition.inspect(client)
			if not assault_precondition.get("ready", false):
				_fail("assault precondition failed: %s" % assault_precondition)
				return
			if not _press(scene_root, "AssaultButton"):
				return
			order_results.append(client.last_order_result())
		"resume":
			pass
		_:
			_fail("unknown phase")
			return

	await process_frame
	await process_frame

	var payload: Dictionary = {
		"phase": phase,
		"controls": _controls(scene_root),
		"order_results": order_results,
		"state_exists": FileAccess.file_exists(args[1]),
		"session_command": client.session_command(),
		"map_view": _map_view_observation(scene_root),
		"assault_precondition": assault_precondition,
	}
	if phase == "play":
		payload["after_start"] = after_start
	print(PREFIX, JSON.stringify(payload))
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
	return scene_root


func _press(scene_root: Control, button_name: String) -> bool:
	var button := scene_root.find_child(button_name, true, false) as Button
	if button == null:
		_fail("missing %s" % button_name)
		return false
	button.emit_signal("pressed")
	return true


func _controls(scene_root: Control) -> Dictionary:
	var region_list := scene_root.find_child("RegionList", true, false) as ItemList
	var regions: Array[String] = []
	for index: int in region_list.item_count:
		regions.append(region_list.get_item_text(index))
	return {
		"date": (scene_root.find_child("DateLabel", true, false) as Label).text,
		"result": (scene_root.find_child("ResultContractLabel", true, false) as Label).text,
		"party_position": (scene_root.find_child("PartyPositionContractLabel", true, false) as Label).text,
		"regions": regions,
		"duchy_status": (scene_root.find_child("PlayerDuchyStatusLabel", true, false) as Label).text,
		"order_status": (scene_root.find_child("LastOrderStatusLabel", true, false) as Label).text,
	}


func _observation(scene_root: Control) -> Dictionary:
	## Same top-level shape as the final payload slice: controls + map_view.
	return {
		"controls": _controls(scene_root),
		"map_view": _map_view_observation(scene_root),
	}


func _map_view_observation(scene_root: Control) -> Dictionary:
	var map_view: Node = scene_root.find_child("MapView", true, false)
	var tile_visuals: Dictionary = {}
	if map_view != null:
		for region_name: String in [PLAYER_LANDS, AI_OUTPOST]:
			var visual: String = _tile_visual(map_view, region_name)
			if not visual.is_empty():
				tile_visuals[region_name] = visual
	return {
		"map_view_found": map_view != null,
		"tile_visuals": tile_visuals,
	}


func _tile_visual(map_view: Node, region_name: String) -> String:
	var label: Label = PartyMapMark.find_label_with_text(map_view, region_name)
	if label == null:
		return ""
	var tile: Control = PartyMapMark.tile_control(label, map_view)
	return _visual_key(tile)


func _visual_key(tile: Control) -> String:
	## Same ownership observation as persistent_next_turn_e2e_probe / map_view_probe.
	if tile is ColorRect:
		return _color_key((tile as ColorRect).color)
	if tile is TextureRect:
		var root_mod: Color = (tile as CanvasItem).modulate
		if root_mod != Color(1, 1, 1, 1):
			return _color_key(root_mod)
	for child: Node in tile.get_children():
		var child_name: String = str(child.name)
		if child_name == "PlayerPartyMarker" or child_name == "Settlement":
			continue
		if child is ColorRect:
			return _color_key((child as ColorRect).color)
		if child is TextureRect:
			return _color_key((child as CanvasItem).modulate)
	return _color_key(tile.modulate)


func _color_key(color: Color) -> String:
	return "%.4f,%.4f,%.4f,%.4f" % [color.r, color.g, color.b, color.a]


func _fail(message: String) -> void:
	printerr("persistent_natural_assault_e2e_probe: ", message)
	quit(2)
