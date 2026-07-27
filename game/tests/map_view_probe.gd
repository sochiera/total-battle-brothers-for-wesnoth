extends SceneTree


## Headless probe for MapView: after apply_model / render_model, report one tile
## per region (name label under MapView), global rects, and an observable visual
## key used to distinguish ownership without reading names.

const MAIN_SCENE_PATH := "res://scenes/main.tscn"
const SnapshotModel = preload("res://scripts/snapshot_model.gd")
const PREFIX := "MAP_VIEW "


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

	var map_view: Node = scene_root.find_child("MapView", true, false)
	if map_view == null:
		print(PREFIX, JSON.stringify({
			"map_view_found": false,
			"has_render_model": false,
			"regions": [],
			"tiles_after_first": [],
			"tiles_after_second": [],
			"tiles_after_empty": [],
			"tiles_after_direct_render": [],
			"tile_count_after_first": 0,
			"tile_count_after_second": 0,
			"tile_count_after_empty": 0,
			"tile_count_after_direct_render": 0,
		}))
		quit(0)
		return

	# Single source of truth for synthetic regions; emitted in payload for Python.
	var regions_full: Array = [
		{"name": "Alpha", "col": 0, "row": 0, "owner": "player"},
		{"name": "Beta", "col": 2, "row": 0, "owner": null},
		{"name": "Gamma", "col": 0, "row": 1, "owner": "ai"},
	]
	var names_full: Array[String] = []
	for region: Variant in regions_full:
		names_full.append(region["name"])

	scene_root.apply_model(_model(regions_full))
	await process_frame
	await process_frame
	var tiles_first: Array = _collect_tiles(map_view, names_full)
	var count_first: int = _count_tiles(map_view)

	scene_root.apply_model(_model(regions_full))
	await process_frame
	await process_frame
	var tiles_second: Array = _collect_tiles(map_view, names_full)
	var count_second: int = _count_tiles(map_view)

	scene_root.apply_model(_model([]))
	await process_frame
	await process_frame
	var tiles_empty: Array = _collect_tiles(map_view, names_full)
	var count_empty: int = _count_tiles(map_view)

	var tiles_direct: Array = []
	var count_direct: int = 0
	var has_render := map_view.has_method("render_model")
	if has_render:
		map_view.call("render_model", _model(regions_full))
		await process_frame
		await process_frame
		tiles_direct = _collect_tiles(map_view, names_full)
		count_direct = _count_tiles(map_view)

	print(PREFIX, JSON.stringify({
		"map_view_found": true,
		"has_render_model": has_render,
		"regions": regions_full,
		"tiles_after_first": tiles_first,
		"tiles_after_second": tiles_second,
		"tiles_after_empty": tiles_empty,
		"tiles_after_direct_render": tiles_direct,
		"tile_count_after_first": count_first,
		"tile_count_after_second": count_second,
		"tile_count_after_empty": count_empty,
		"tile_count_after_direct_render": count_direct,
	}))
	quit(0)


func _model(regions: Array) -> SnapshotModel:
	var model := SnapshotModel.new()
	model.year = 1
	model.month = 1
	model.player_result = "ongoing"
	model.regions = regions
	return model


func _count_tiles(map_view: Node) -> int:
	# Absolute tile count under MapView (catches re-render accumulation that
	# first-label-per-name collection would miss).
	var count := 0
	for child: Node in map_view.get_children():
		if child is Control:
			count += 1
	return count


func _collect_tiles(map_view: Node, expected_names: Array[String]) -> Array:
	var tiles: Array = []
	for region_name: String in expected_names:
		var label: Label = _find_label_with_text(map_view, region_name)
		if label == null:
			continue
		var tile: Control = _tile_control(label, map_view)
		var rect: Rect2 = tile.get_global_rect()
		tiles.append({
			"name": region_name,
			"x": rect.position.x,
			"y": rect.position.y,
			"w": rect.size.x,
			"h": rect.size.y,
			"visible": tile.is_visible_in_tree() and label.is_visible_in_tree(),
			"visual": _visual_key(tile),
		})
	return tiles


func _find_label_with_text(root: Node, text: String) -> Label:
	if root is Label and (root as Label).text == text:
		return root as Label
	for child: Node in root.get_children():
		var found: Label = _find_label_with_text(child, text)
		if found != null:
			return found
	return null


func _tile_control(label: Label, map_view: Node) -> Control:
	# Tile body is the immediate Control parent under MapView (not a shared root).
	var parent: Node = label.get_parent()
	if parent is Control and parent != map_view:
		return parent as Control
	return label


func _visual_key(tile: Control) -> String:
	# Observable paint of the tile body — ColorRect.color when present, else modulate.
	if tile is ColorRect:
		return _color_key((tile as ColorRect).color)
	for child: Node in tile.get_children():
		if child is ColorRect:
			return _color_key((child as ColorRect).color)
	return _color_key(tile.modulate)


func _color_key(color: Color) -> String:
	return "%.4f,%.4f,%.4f,%.4f" % [color.r, color.g, color.b, color.a]


func _fail(message: String) -> void:
	printerr("map_view_probe: ", message)
	quit(1)
