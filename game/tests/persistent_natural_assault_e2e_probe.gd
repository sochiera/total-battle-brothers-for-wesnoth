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
	var battle_pending: Dictionary = {}
	var battle_after_auto: Dictionary = {}
	var controls_pending: Dictionary = {}
	match phase:
		"play":
			after_start = _observation(scene_root)
			var staging := AssaultPrecondition.stage_live_frontier(scene_root)
			if not staging.get("ok", false):
				_fail("live frontier staging failed: %s" % staging)
				return
			order_results.append_array(staging.get("order_results", []))
			assault_precondition = AssaultPrecondition.inspect(client)
			if not assault_precondition.get("ready", false):
				_fail("assault precondition failed: %s" % assault_precondition)
				return
			if not _press(scene_root, "AssaultButton"):
				return
			order_results.append(client.last_order_result())
		"resume":
			battle_pending = _battle_observation(scene_root)
			controls_pending = _controls(scene_root)
			if not scene_root.call("battle_auto_from_bridge", client):
				_fail("battle_auto failed after AssaultButton")
				return
			battle_after_auto = _battle_observation(scene_root)
			order_results.append(client.last_battle_result())
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
		"battle_pending": battle_pending if not battle_pending.is_empty() else _battle_observation(scene_root),
		"battle_after_auto": battle_after_auto,
		"controls_pending": controls_pending,
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
	if button == null or button.disabled:
		_fail("missing or disabled %s" % button_name)
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


func _battle_observation(scene_root: Control) -> Dictionary:
	var battle_view: Node = scene_root.find_child("BattleView", true, false)
	var tiles: Array = []
	var paint_groups: Dictionary = {}
	if battle_view != null:
		for child: Node in battle_view.get_children():
			if not child is Control or not str(child.name).begins_with("HexTile_"):
				continue
			var tile := child as Control
			var visual := _visual_key(tile)
			tiles.append({
				"name": str(child.name),
				"visual": visual,
				"visible": tile.is_visible_in_tree(),
			})
			paint_groups[visual] = true
	var result_label: Node = null
	if battle_view != null:
		result_label = battle_view.find_child("BattleResultLabel", true, false)
	return {
		"tile_count": tiles.size(),
		"tiles": tiles,
		"paint_groups": paint_groups.size(),
		"result_text": result_label.text.strip_edges() if result_label is Label else "",
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
			var child_mod: Color = (child as CanvasItem).modulate
			if child_mod != Color(1, 1, 1, 1):
				return _color_key(child_mod)
	var side_paths: PackedStringArray = _side_texture_paths_under(tile)
	if not side_paths.is_empty():
		side_paths.sort()
		return "|".join(side_paths)
	return _color_key(tile.modulate)


func _side_texture_paths_under(node: Node) -> PackedStringArray:
	var paths: PackedStringArray = PackedStringArray()
	var path: String = _direct_texture_path(node)
	if not path.is_empty() and _is_side_texture_layer(node, path):
		paths.append(path)
	for child: Node in node.get_children():
		paths.append_array(_side_texture_paths_under(child))
	return paths


func _is_side_texture_layer(node: Node, path: String) -> bool:
	return str(node.name) == "SideSilhouette" or path.contains("side_attacker") or path.contains("side_defender")


func _direct_texture_path(node: Node) -> String:
	if node is TextureRect:
		var texture_rect := node as TextureRect
		if texture_rect.texture != null:
			var texture_path: String = texture_rect.texture.resource_path
			return texture_path if not texture_path.is_empty() else "<embedded>"
	if node is Sprite2D:
		var sprite := node as Sprite2D
		if sprite.texture != null:
			var sprite_path: String = sprite.texture.resource_path
			return sprite_path if not sprite_path.is_empty() else "<embedded>"
	return ""


func _color_key(color: Color) -> String:
	return "%.4f,%.4f,%.4f,%.4f" % [color.r, color.g, color.b, color.a]


func _fail(message: String) -> void:
	printerr("persistent_natural_assault_e2e_probe: ", message)
	quit(2)
