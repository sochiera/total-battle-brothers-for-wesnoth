extends SceneTree


## Headless probe for BattleView: after render_model / apply_model, report one
## tile per battle hex (stable axial name under BattleView), global rects, side
## paint key, Polish result text, and re-render / empty-model cleanup.

const MAIN_SCENE_PATH := "res://scenes/main.tscn"
const SnapshotModel = preload("res://scripts/snapshot_model.gd")
const PREFIX := "BATTLE_VIEW "


func _init() -> void:
	call_deferred("_run")


func _run() -> void:
	var scene: PackedScene = ResourceLoader.load(MAIN_SCENE_PATH) as PackedScene
	if scene == null:
		_fail("cannot load main scene")
		return
	var scene_root: Control = scene.instantiate() as Control
	if scene_root == null:
		_fail("cannot instantiate main scene")
		return

	root.add_child(scene_root)
	await process_frame
	await process_frame

	var battle_view: Node = scene_root.find_child("BattleView", true, false)
	if battle_view == null:
		print(PREFIX, JSON.stringify({
			"battle_view_found": false,
			"has_render_model": false,
			"hexes": [],
			"tiles_after_first": [],
			"tiles_after_second": [],
			"tiles_after_empty": [],
			"tiles_after_direct_render": [],
			"tiles_after_null_render": [],
			"tile_count_after_first": 0,
			"tile_count_after_second": 0,
			"tile_count_after_empty": 0,
			"tile_count_after_direct_render": 0,
			"tile_count_after_null_render": 0,
			"result_text_attacker_win": "",
			"result_text_defender_win": "",
			"result_text_draw": "",
			"result_text_no_battle": "",
			"view_rect": null,
			"result_label_rect": null,
		}))
		quit(0)
		return

	# Settlement-like field: domain r∈{0,1,2}. r=0/1 alone missed label-on-tile overlap.
	# Include Plains/Forest/Hills so terrain texture mapping is observable (G87.1c-1).
	# Include unknown / empty side so G87.1c-2 can assert terrain-only (no silhouette).
	var hexes_full: Array = [
		{"q": 0, "r": 0, "terrain": "Plains", "side": "attacker", "hp": 10},
		{"q": 2, "r": 0, "terrain": "Plains", "side": "defender", "hp": 8},
		{"q": 0, "r": 1, "terrain": "Forest", "side": "attacker", "hp": 5},
		{"q": 0, "r": 2, "terrain": "Hills", "side": "attacker", "hp": 7},
		{"q": 2, "r": 2, "terrain": "Forest", "side": "defender", "hp": 6},
		{"q": 1, "r": 0, "terrain": "Plains", "side": "unknown", "hp": 1},
		{"q": 1, "r": 1, "terrain": "Hills", "side": "", "hp": 1},
	]
	# Unknown / empty / missing terrain must still paint a default asset tile (no drop).
	var hexes_fallback: Array = [
		{"q": 0, "r": 0, "terrain": "Swamp", "side": "attacker", "hp": 1},
		{"q": 1, "r": 0, "terrain": "", "side": "defender", "hp": 1},
		{"q": 2, "r": 0, "side": "attacker", "hp": 1},
	]

	scene_root.apply_model(_model_with_battle(hexes_full, "attacker_win"))
	await process_frame
	await process_frame
	var tiles_first: Array = _collect_tiles(battle_view, hexes_full)
	var count_first: int = _count_hex_tiles(battle_view)
	var result_attacker: String = _result_text(battle_view)
	var view_rect: Variant = _control_rect(battle_view as Control)
	var result_label_rect: Variant = _result_label_rect(battle_view)

	scene_root.apply_model(_model_with_battle(hexes_full, "attacker_win"))
	await process_frame
	await process_frame
	var tiles_second: Array = _collect_tiles(battle_view, hexes_full)
	var count_second: int = _count_hex_tiles(battle_view)

	scene_root.apply_model(_model_without_battle())
	await process_frame
	await process_frame
	var tiles_empty: Array = _collect_tiles(battle_view, hexes_full)
	var count_empty: int = _count_hex_tiles(battle_view)
	var result_no_battle: String = _result_text(battle_view)

	var tiles_direct: Array = []
	var count_direct: int = 0
	var tiles_null: Array = []
	var count_null: int = 0
	var tiles_fallback: Array = []
	var result_defender: String = ""
	var result_draw: String = ""
	var has_render := battle_view.has_method("render_model")
	if has_render:
		battle_view.call("render_model", _model_with_battle(hexes_full, "defender_win"))
		await process_frame
		await process_frame
		tiles_direct = _collect_tiles(battle_view, hexes_full)
		count_direct = _count_hex_tiles(battle_view)
		result_defender = _result_text(battle_view)

		battle_view.call("render_model", _model_with_battle(hexes_full, "draw"))
		await process_frame
		await process_frame
		result_draw = _result_text(battle_view)

		battle_view.call("render_model", _model_with_battle(hexes_fallback, "draw"))
		await process_frame
		await process_frame
		tiles_fallback = _collect_tiles(battle_view, hexes_fallback)

		battle_view.call("render_model", null)
		await process_frame
		await process_frame
		tiles_null = _collect_tiles(battle_view, hexes_full)
		count_null = _count_hex_tiles(battle_view)

	print(PREFIX, JSON.stringify({
		"battle_view_found": true,
		"has_render_model": has_render,
		"hexes": hexes_full,
		"hexes_fallback": hexes_fallback,
		"tiles_after_first": tiles_first,
		"tiles_after_second": tiles_second,
		"tiles_after_empty": tiles_empty,
		"tiles_after_direct_render": tiles_direct,
		"tiles_after_null_render": tiles_null,
		"tiles_after_fallback": tiles_fallback,
		"tile_count_after_first": count_first,
		"tile_count_after_second": count_second,
		"tile_count_after_empty": count_empty,
		"tile_count_after_direct_render": count_direct,
		"tile_count_after_null_render": count_null,
		"result_text_attacker_win": result_attacker,
		"result_text_defender_win": result_defender,
		"result_text_draw": result_draw,
		"result_text_no_battle": result_no_battle,
		"view_rect": view_rect,
		"result_label_rect": result_label_rect,
	}))
	quit(0)


func _model_with_battle(hexes: Array, result: String) -> SnapshotModel:
	var model := SnapshotModel.new()
	model.year = 1
	model.month = 1
	model.player_result = "ongoing"
	model.regions = []
	model.battle = {"result": result, "hexes": hexes}
	return model


func _model_without_battle() -> SnapshotModel:
	var model := SnapshotModel.new()
	model.year = 1
	model.month = 1
	model.player_result = "ongoing"
	model.regions = []
	model.battle = null
	return model


func _hex_tile_name(q: int, r: int) -> String:
	# Public contract: tile names are stable and derived from axial (q, r).
	return "HexTile_%d_%d" % [q, r]


func _count_hex_tiles(battle_view: Node) -> int:
	var count := 0
	for child: Node in battle_view.get_children():
		if child is Control and str(child.name).begins_with("HexTile_"):
			count += 1
	return count


func _find_hex_tile(battle_view: Node, q: int, r: int) -> Control:
	var wanted: String = _hex_tile_name(q, r)
	for child: Node in battle_view.get_children():
		if child is Control and str(child.name) == wanted:
			return child as Control
	var nested: Node = battle_view.find_child(wanted, true, false)
	if nested is Control:
		return nested as Control
	return null


func _collect_tiles(battle_view: Node, hexes: Array) -> Array:
	var tiles: Array = []
	for hex: Variant in hexes:
		if not hex is Dictionary:
			continue
		var q: int = int(hex["q"])
		var r: int = int(hex["r"])
		var tile: Control = _find_hex_tile(battle_view, q, r)
		if tile == null:
			continue
		var rect: Rect2 = tile.get_global_rect()
		# Public observation: each TextureRect/Sprite2D under the hex with path+size.
		# G87.1c-2 needs layer size so a full-tile stretched side sprite fails.
		var texture_layers: Array = _collect_texture_layers(tile)
		var texture_paths: Array = []
		for layer: Variant in texture_layers:
			if layer is Dictionary and layer.has("path"):
				texture_paths.append(layer["path"])
		tiles.append({
			"q": q,
			"r": r,
			"side": hex.get("side", ""),
			"terrain": str(hex.get("terrain", "")),
			"name": str(tile.name),
			"x": rect.position.x,
			"y": rect.position.y,
			"w": rect.size.x,
			"h": rect.size.y,
			"visible": tile.is_visible_in_tree(),
			"visual": _visual_key(tile),
			"has_texture": not texture_paths.is_empty(),
			"texture_paths": texture_paths,
			"texture_layers": texture_layers,
		})
	return tiles


func _collect_texture_layers(node: Node) -> Array:
	var layers: Array = []
	var path: String = _direct_texture_path(node)
	if not path.is_empty() and node is CanvasItem:
		var size: Vector2 = Vector2.ZERO
		if node is Control:
			size = (node as Control).get_global_rect().size
		elif node is Sprite2D:
			var sp: Sprite2D = node as Sprite2D
			if sp.texture != null:
				var tex_size: Vector2 = sp.texture.get_size()
				size = Vector2(tex_size.x * absf(sp.scale.x), tex_size.y * absf(sp.scale.y))
		layers.append({"path": path, "w": size.x, "h": size.y})
	for child: Node in node.get_children():
		layers.append_array(_collect_texture_layers(child))
	return layers


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


func _control_rect(control: Control) -> Dictionary:
	var rect: Rect2 = control.get_global_rect()
	return {
		"x": rect.position.x,
		"y": rect.position.y,
		"w": rect.size.x,
		"h": rect.size.y,
	}


func _result_label_rect(battle_view: Node) -> Variant:
	# Named outcome label is public scene contract; geometry must not cover hex tiles.
	var label: Node = battle_view.find_child("BattleResultLabel", true, false)
	if label is Control:
		return _control_rect(label as Control)
	return null


func _result_text(battle_view: Node) -> String:
	# Contractual outcome only: do not mix terrain Labels under HexTile_*.
	var label: Node = battle_view.find_child("BattleResultLabel", true, false)
	if label is Label:
		return (label as Label).text.strip_edges()
	return ""


func _visual_key(tile: Control) -> String:
	# Side paint: ColorRect fill, root/child modulate on textured tiles (MapView-style).
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
	return _color_key(tile.modulate)


func _color_key(color: Color) -> String:
	return "%.4f,%.4f,%.4f,%.4f" % [color.r, color.g, color.b, color.a]


func _fail(message: String) -> void:
	printerr("battle_view_probe: ", message)
	quit(1)
