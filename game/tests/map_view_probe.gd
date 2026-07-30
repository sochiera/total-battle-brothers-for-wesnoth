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
	# settlement mirrors map_state (dict or null) so G87.1b can observe settlement art.
	# Beta at col=1 (not 2) so the probe includes a horizontal grid neighbour
	# (Alpha–Beta) as well as a vertical one (Alpha–Gamma) for connected-grid checks.
	var regions_full: Array = [
		{
			"name": "Alpha",
			"col": 0,
			"row": 0,
			"owner": "player",
			"settlement": {"name": "Alpha Keep"},
		},
		{"name": "Beta", "col": 1, "row": 0, "owner": null, "settlement": null},
		{"name": "Gamma", "col": 0, "row": 1, "owner": "ai", "settlement": null},
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

	# G96.1a AI: silhouette identity from region.party.owner (not battle side roles).
	# Alpha carries a player party, Gamma an AI party; Beta has none. player_party_region
	# stays Alpha so the player mark path still works if MapView dual-keys on it;
	# AI mark must still come from party.owner == "ai" on Gamma.
	var regions_owner_parties: Array = [
		{
			"name": "Alpha",
			"col": 0,
			"row": 0,
			"owner": "player",
			"settlement": {"name": "Alpha Keep"},
			"party": {"owner": "player"},
		},
		{
			"name": "Beta",
			"col": 1,
			"row": 0,
			"owner": null,
			"settlement": null,
			"party": null,
		},
		{
			"name": "Gamma",
			"col": 0,
			"row": 1,
			"owner": "ai",
			"settlement": null,
			"party": {"owner": "ai"},
		},
	]
	var names_owner_parties: Array[String] = []
	for region: Variant in regions_owner_parties:
		names_owner_parties.append(region["name"])
	# Explicit skip marker when render_model is missing — empty {} would make
	# Python assert on Gamma silhouette and hide the real "no render" cause.
	var party_owner_silhouettes: Dictionary = {"skipped": true}
	if has_render:
		party_owner_silhouettes = await _party_owner_silhouette_sample(
			map_view, regions_owner_parties, names_owner_parties, "Alpha"
		)

	# G94.1a: five-region line matches a fresh headless party (col 0..4, row 0).
	# Real snapshot names exercise label readability; short R0.. aliases would
	# hide overflow when TILE_SIZE shrinks. Settlements on outposts/keeps match
	# the fresh map so name-vs-settlement layout is observable.
	var regions_line: Array = [
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
	var names_line: Array[String] = []
	for region: Variant in regions_line:
		names_line.append(region["name"])
	var tiles_line: Array = []
	if has_render:
		map_view.call("render_model", _model(regions_line))
		await process_frame
		await process_frame
		tiles_line = _collect_tiles(map_view, names_line)
	var map_rect: Rect2 = (map_view as Control).get_global_rect()

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
		"party_owner_silhouettes": party_owner_silhouettes,
		"line_regions": regions_line,
		"line_tiles": tiles_line,
		"map_view_rect": {
			"x": map_rect.position.x,
			"y": map_rect.position.y,
			"w": map_rect.size.x,
			"h": map_rect.size.y,
		},
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


func _party_owner_silhouette_sample(
	map_view: Node,
	regions: Array,
	names: Array[String],
	player_party_region: Variant,
) -> Dictionary:
	# Observe public unit-carrier paths under each tile after render_model.
	# Paths are the contract (party_player_unit / party_ai_unit); node names are not.
	if not map_view.has_method("render_model"):
		_fail("party-owner silhouette sample requires MapView.render_model")
		return {}
	map_view.call("render_model", _model(regions, player_party_region))
	await process_frame
	await process_frame
	var unit_paths_by_region: Dictionary = {}
	for region_name: String in names:
		var label: Label = PartyMapMark.find_label_with_text(map_view, region_name)
		if label == null:
			continue
		var tile: Control = PartyMapMark.tile_control(label, map_view)
		var unit_path: String = _party_unit_path_on_tile(tile)
		if not unit_path.is_empty():
			unit_paths_by_region[region_name] = unit_path
	return {"unit_paths_by_region": unit_paths_by_region}


func _party_unit_path_on_tile(tile: Control) -> String:
	# Public G96.1a carriers only — ignore ground/settlement/banner leftovers.
	for layer: Variant in _collect_texture_layers(tile):
		if not layer is Dictionary:
			continue
		var path: String = str(layer.get("path", ""))
		if (
			path.ends_with("party_player_unit.png")
			or path.ends_with("party_ai_unit.png")
		):
			return path
	return ""


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
	# Marker geometry (R87.1): corner mark must stay smaller than its tile, and
	# must not capture mouse — a FULL_RECT party texture would green-gate
	# marker_has_texture while covering the whole region.
	var marker_layers: Array = []
	for region_name: String in names:
		var label: Label = PartyMapMark.find_label_with_text(map_view, region_name)
		if label == null:
			continue
		var tile: Control = PartyMapMark.tile_control(label, map_view)
		for layer: Variant in _collect_texture_layers(tile):
			if (
				layer is Dictionary
				and str(layer.get("name", "")) == "PlayerPartyMarker"
			):
				var copy: Dictionary = (layer as Dictionary).duplicate()
				copy["tile_name"] = region_name
				copy["tile_w"] = tile.get_global_rect().size.x
				copy["tile_h"] = tile.get_global_rect().size.y
				marker_layers.append(copy)
	return {
		"position_label": "" if position_label == null else position_label.text,
		"marked_regions": PartyMapMark.marked_party_regions(map_view, names),
		"marker_count": PartyMapMark.count_party_markers(map_view),
		"marker_has_texture": PartyMapMark.marker_has_texture(map_view),
		"marker_layers": marker_layers,
	}


func _count_tiles(map_view: Node) -> int:
	# Absolute RegionTile_* count under MapView (catches re-render accumulation
	# that first-label-per-name collection would miss). Non-tile children
	# (e.g. a map-panel background TextureRect) must not inflate the count —
	# the public contract is one region tile per region, not all Controls.
	var count := 0
	for child: Node in map_view.get_children():
		if child is Control and str(child.name).begins_with("RegionTile_"):
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
		# Public observation: each TextureRect/Sprite2D under the tile with path,
		# size, and mouse_filter (R87.1: full-tile stretch layers must fill the
		# tile and not steal mouse; party marker stays a small corner mark).
		var texture_layers: Array = _collect_texture_layers(tile)
		# Region body textures only — exclude party marker so settlement/owner
		# comparison stays independent of whether the army is parked here.
		# Drop both player/AI unit carriers even if the layer is misnamed.
		var texture_paths: Array = []
		for layer: Variant in texture_layers:
			if not (layer is Dictionary and layer.has("path")):
				continue
			if str(layer.get("name", "")) == "PlayerPartyMarker":
				continue
			var body_path: String = str(layer["path"])
			if (
				body_path.ends_with("party_player_unit.png")
				or body_path.ends_with("party_ai_unit.png")
			):
				continue
			texture_paths.append(layer["path"])
		# Unwrapped single-line content size (ignores the FULL_RECT control size).
		# Used by G94.1a to catch names wider than the tile that spill into
		# neighbours when clip_text is off.
		var label_content: Vector2 = label.get_minimum_size()
		tiles.append({
			"name": region_name,
			"x": rect.position.x,
			"y": rect.position.y,
			"w": rect.size.x,
			"h": rect.size.y,
			"visible": tile.is_visible_in_tree() and label.is_visible_in_tree(),
			"visual": _visual_key(tile),
			"has_texture": not texture_paths.is_empty(),
			"texture_paths": texture_paths,
			"texture_layers": texture_layers,
			"tile_mouse_filter": tile.mouse_filter,
			"label_content_w": label_content.x,
			"label_content_h": label_content.y,
		})
	return tiles


func _collect_texture_layers(node: Node) -> Array:
	var layers: Array = []
	var path: String = _direct_texture_path(node)
	if not path.is_empty() and node is CanvasItem:
		var size: Vector2 = Vector2.ZERO
		var mouse_filter: int = -1
		if node is Control:
			var ctrl: Control = node as Control
			size = ctrl.get_global_rect().size
			mouse_filter = ctrl.mouse_filter
		elif node is Sprite2D:
			var sp: Sprite2D = node as Sprite2D
			if sp.texture != null:
				var tex_size: Vector2 = sp.texture.get_size()
				size = Vector2(tex_size.x * absf(sp.scale.x), tex_size.y * absf(sp.scale.y))
		layers.append({
			"path": path,
			"name": str(node.name),
			"w": size.x,
			"h": size.y,
			"mouse_filter": mouse_filter,
		})
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


func _visual_key(tile: Control) -> String:
	# Ownership paint only — not settlement/marker. Supports ColorRect.color,
	# root TextureRect.modulate, or a ground-layer child (when root is an
	# un-tinted Control so label/marker keep default color).
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
	printerr("map_view_probe: ", message)
	quit(1)
