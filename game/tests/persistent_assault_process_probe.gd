extends SceneTree


## G85.1c e2e: assault button feeds BattleView from live bridge snapshots across
## two processes on a shared state file. Pre-assault battle view is empty; after
## assault tiles of both sides and Polish result appear; resume reloads them.

const MAIN_SCENE_PATH := "res://scenes/main.tscn"
const BridgeClient = preload("res://scripts/bridge_client.gd")
const PREFIX := "PERSISTENT_ASSAULT_PROCESS "


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

	var battle_view: Node = scene_root.find_child("BattleView", true, false)
	if battle_view == null:
		_fail("missing BattleView")
		return

	var controls_before_order := _controls(scene_root)
	var battle_before_order := _battle_observation(battle_view)
	var controls_after_muster: Variant = null
	var phase: String = args[4]

	match phase:
		"prepare":
			if not _press(scene_root, "MusterButton"):
				return
			controls_after_muster = _controls(scene_root)
			# G92.2a chain: player lands → player outpost → border (two marches).
			if not _press(scene_root, "MarchButton"):
				return
			if not _press(scene_root, "MarchButton"):
				return
		"battle", "second_assault":
			if not _press(scene_root, "AssaultButton"):
				return
		_:
			_fail("unknown phase")
			return

	await process_frame
	await process_frame

	print(PREFIX, JSON.stringify({
		"phase": phase,
		"controls_before_order": controls_before_order,
		"controls_after_muster": controls_after_muster if controls_after_muster != null else {},
		"controls": _controls(scene_root),
		"battle_before_order": battle_before_order,
		"battle": _battle_observation(battle_view),
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


func _battle_observation(battle_view: Node) -> Dictionary:
	var tiles: Array = []
	var sides: Dictionary = {}
	for child: Node in battle_view.get_children():
		if not child is Control:
			continue
		var name_str: String = str(child.name)
		if not name_str.begins_with("HexTile_"):
			continue
		var tile := child as Control
		var parts: PackedStringArray = name_str.split("_")
		# Public contract: HexTile_<q>_<r>
		if parts.size() != 3:
			continue
		var q: int = int(parts[1])
		var r: int = int(parts[2])
		var visual: String = _visual_key(tile)
		tiles.append({
			"q": q,
			"r": r,
			"name": name_str,
			"visual": visual,
			"visible": tile.is_visible_in_tree(),
		})
		# side inferred only for reporting paint groups (not private structure)
		if not sides.has(visual):
			sides[visual] = []
		(sides[visual] as Array).append({"q": q, "r": r})

	var result_label: Node = battle_view.find_child("BattleResultLabel", true, false)
	var result_text := ""
	if result_label is Label:
		result_text = (result_label as Label).text.strip_edges()

	return {
		"tile_count": tiles.size(),
		"tiles": tiles,
		"paint_groups": sides.size(),
		"result_text": result_text,
	}


func _visual_key(tile: Control) -> String:
	# paint_groups must mean "distinct side paint", not "distinct terrain".
	# 1) legacy ColorRect / non-identity modulate (pre-G98.1b ground tint);
	# 2) side silhouette Texture2D paths only (G98.1b). Fingerprinting all
	# textures under the hex would let attacker/defender terrain differences
	# alone green paint_groups >= 2 without visible side figures.
	if tile is ColorRect:
		return _color_key((tile as ColorRect).color)
	if tile is TextureRect:
		var root_mod: Color = (tile as CanvasItem).modulate
		if root_mod != Color(1, 1, 1, 1):
			return _color_key(root_mod)
	for child: Node in tile.get_children():
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
	# Production names SideSilhouette; public assets side_attacker / side_defender.
	if str(node.name) == "SideSilhouette":
		return true
	return path.contains("side_attacker") or path.contains("side_defender")


func _direct_texture_path(node: Node) -> String:
	if node is TextureRect:
		var tr: TextureRect = node as TextureRect
		if tr.texture != null:
			var p: String = tr.texture.resource_path
			return p if not p.is_empty() else "<embedded>"
	if node is Sprite2D:
		var sp: Sprite2D = node as Sprite2D
		if sp.texture != null:
			var p2: String = sp.texture.resource_path
			return p2 if not p2.is_empty() else "<embedded>"
	return ""


func _color_key(color: Color) -> String:
	return "%.4f,%.4f,%.4f,%.4f" % [color.r, color.g, color.b, color.a]


func _fail(message: String) -> void:
	printerr("persistent_assault_process_probe: ", message)
	quit(2)
