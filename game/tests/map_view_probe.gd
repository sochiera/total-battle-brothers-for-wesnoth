extends SceneTree


## Headless probe for MapView: after apply_model / render_model, report one tile
## per region (name label under MapView), global rects, and an observable visual
## key used to distinguish ownership without reading names.

const MAIN_SCENE_PATH := "res://scenes/main.tscn"
const SnapshotModel = preload("res://scripts/snapshot_model.gd")
const PartyMapMark = preload("res://tests/party_map_mark_helpers.gd")
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

	# Party-mark scenarios (G84.1c): mark derives solely from model.player_party_region.
	var party_on_alpha: Dictionary = await _party_mark_sample(
		scene_root, map_view, regions_full, names_full, "Alpha", false
	)
	var party_absent: Dictionary = await _party_mark_sample(
		scene_root, map_view, regions_full, names_full, null, false
	)
	var party_on_beta: Dictionary = await _party_mark_sample(
		scene_root, map_view, regions_full, names_full, "Beta", false
	)
	var party_direct_gamma: Dictionary = await _party_mark_sample(
		scene_root, map_view, regions_full, names_full, "Gamma", true
	)

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
		"party_on_alpha": party_on_alpha,
		"party_absent": party_absent,
		"party_on_beta": party_on_beta,
		"party_direct_gamma": party_direct_gamma,
	}))
	quit(0)


func _model(regions: Array, party_region: Variant = null) -> SnapshotModel:
	var model := SnapshotModel.new()
	model.year = 1
	model.month = 1
	model.player_result = "ongoing"
	model.regions = regions
	model.player_party_region = party_region
	return model


func _party_mark_sample(
	scene_root: Control,
	map_view: Node,
	regions: Array,
	names: Array[String],
	party_region: Variant,
	direct_render: bool,
) -> Dictionary:
	var model: SnapshotModel = _model(regions, party_region)
	if direct_render:
		if not map_view.has_method("render_model"):
			_fail("direct_render party sample requires MapView.render_model")
			return {}
		map_view.call("render_model", model)
	else:
		scene_root.apply_model(model)
	await process_frame
	await process_frame
	var position_label: Label = scene_root.find_child(
		"PlayerPartyPositionLabel", true, false
	) as Label
	return {
		"position_label": "" if position_label == null else position_label.text,
		"marked_regions": PartyMapMark.marked_party_regions(map_view, names),
		"marker_count": PartyMapMark.count_party_markers(map_view),
	}


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
		var label: Label = PartyMapMark.find_label_with_text(map_view, region_name)
		if label == null:
			continue
		var tile: Control = PartyMapMark.tile_control(label, map_view)
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
