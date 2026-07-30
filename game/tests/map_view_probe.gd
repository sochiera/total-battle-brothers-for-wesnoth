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

	# G96.1a complete army projection: own before/after samples (not the AI
	# silhouette gate's party_owner_silhouettes). Before: player@Alpha, AI@Gamma.
	# After: player@Beta, AI@Alpha (Gamma empty). player_party_region null so
	# marks come only from regions[*].party. After is a deep copy of before with
	# only party fields changed — geometry/settlement stay fixed.
	var regions_army_before_move: Array = []
	for region: Variant in regions_owner_parties:
		regions_army_before_move.append((region as Dictionary).duplicate(true))
	var regions_army_after_move: Array = []
	for region: Variant in regions_army_before_move:
		regions_army_after_move.append((region as Dictionary).duplicate(true))
	for region: Variant in regions_army_after_move:
		var r: Dictionary = region
		match str(r["name"]):
			"Alpha":
				r["party"] = {"owner": "ai"}
			"Beta":
				r["party"] = {"owner": "player"}
			"Gamma":
				r["party"] = null
	var party_army_before_move: Dictionary = {"skipped": true}
	var party_army_after_move: Dictionary = {"skipped": true}
	if has_render:
		party_army_before_move = await _party_owner_silhouette_sample(
			map_view, regions_army_before_move, names_owner_parties, null
		)
		party_army_after_move = await _party_owner_silhouette_sample(
			map_view, regions_army_after_move, names_owner_parties, null
		)

	# G96.1a composition: silhouettes on keep / outpost / bare region at once.
	# Public contract is scale + placement (not snapshot rules) — synthetic
	# multi-party is OK so one render exposes all three settlement states.
	# Row-1 "south" (listed after row-0) exposes vertical grid pitch: MapView
	# paints in model.regions order, so later children cover the lower
	# TILE_SIZE.y - GRID_PITCH.y strip of the row above.
	var regions_composition: Array = [
		{
			"name": "player lands",
			"col": 0,
			"row": 0,
			"owner": "player",
			"settlement": {"name": "Player Keep"},
			"party": {"owner": "player"},
		},
		{
			"name": "player outpost",
			"col": 1,
			"row": 0,
			"owner": "player",
			"settlement": {"name": "Player Outpost"},
			"party": {"owner": "ai"},
		},
		{
			"name": "border",
			"col": 2,
			"row": 0,
			"owner": null,
			"settlement": null,
			"party": {"owner": "player"},
		},
		{
			"name": "south",
			"col": 0,
			"row": 1,
			"owner": null,
			"settlement": null,
			"party": null,
		},
	]
	var names_composition: Array[String] = []
	for region: Variant in regions_composition:
		names_composition.append(region["name"])
	var party_silhouette_composition: Dictionary = {"skipped": true}
	if has_render:
		party_silhouette_composition = await _party_silhouette_composition_sample(
			map_view, regions_composition, names_composition
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

	# G97.1c: click selects one region (canonical name + single target frame).
	# Own sample after layout probes so selection does not pollute tile lists.
	var region_selection: Dictionary = {"skipped": true}
	if has_render:
		region_selection = await _region_selection_sample(
			map_view, regions_full, names_full
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
		"party_owner_silhouettes": party_owner_silhouettes,
		"party_army_before_move": party_army_before_move,
		"party_army_after_move": party_army_after_move,
		"party_silhouette_composition": party_silhouette_composition,
		"line_regions": regions_line,
		"line_tiles": tiles_line,
		"map_view_rect": {
			"x": map_rect.position.x,
			"y": map_rect.position.y,
			"w": map_rect.size.x,
			"h": map_rect.size.y,
		},
		"region_selection": region_selection,
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


const TARGET_FRAME_SUFFIX := "map_target_frame.png"


func _region_selection_sample(
	map_view: Node,
	regions: Array,
	names: Array[String],
) -> Dictionary:
	# Public G97.1c contract observed via MapView only:
	# - signal region_selected(String) with the tile's canonical name
	# - one map_target_frame.png overlay on the selected region
	# - re-select and re-render never multiply frames
	if not map_view.has_method("render_model"):
		return {"skipped": true}
	map_view.call("render_model", _model(regions))
	await process_frame
	await process_frame

	var has_signal: bool = map_view.has_signal("region_selected")
	var emitted: Array = []
	if has_signal:
		map_view.connect(
			"region_selected",
			func(region_name: Variant) -> void:
				emitted.append(str(region_name))
		)

	var tile_filters: Dictionary = {}
	for region_name: String in names:
		var tile: Control = _find_region_tile(map_view, region_name)
		if tile != null:
			tile_filters[region_name] = tile.mouse_filter

	# Click Alpha, then Beta; observe frame placement + emissions.
	await _simulate_region_click(map_view, "Alpha")
	await process_frame
	await process_frame
	var after_alpha: Dictionary = _observe_target_frames(map_view, names)
	var emitted_after_alpha: Array = emitted.duplicate()

	await _simulate_region_click(map_view, "Beta")
	await process_frame
	await process_frame
	var after_beta: Dictionary = _observe_target_frames(map_view, names)
	var emitted_after_beta: Array = emitted.duplicate()

	# Re-render same snapshot: durable selection must restore without stacking.
	map_view.call("render_model", _model(regions))
	await process_frame
	await process_frame
	var after_rerender: Dictionary = _observe_target_frames(map_view, names)

	# Second click on the already-selected region must not add another frame.
	await _simulate_region_click(map_view, "Beta")
	await process_frame
	await process_frame
	var after_reclick: Dictionary = _observe_target_frames(map_view, names)

	return {
		"skipped": false,
		"has_region_selected_signal": has_signal,
		"tile_mouse_filters": tile_filters,
		"emitted_after_alpha": emitted_after_alpha,
		"emitted_after_beta": emitted_after_beta,
		"after_alpha": after_alpha,
		"after_beta": after_beta,
		"after_rerender": after_rerender,
		"after_reclick": after_reclick,
	}


func _find_region_tile(map_view: Node, region_name: String) -> Control:
	var label: Label = PartyMapMark.find_label_with_text(map_view, region_name)
	if label == null:
		return null
	return PartyMapMark.tile_control(label, map_view)


func _simulate_region_click(map_view: Node, region_name: String) -> void:
	var tile: Control = _find_region_tile(map_view, region_name)
	if tile == null:
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
	# Viewport only: push_input respects mouse_filter and hit-testing.
	# Do not also gui_input.emit — that dual path greened selection even when
	# the tile was covered or would not receive real mouse input. If headless
	# viewport delivery is ever proven broken, add an explicitly named fallback
	# (e.g. _simulate_region_click_direct_gui_input), not a silent second path.
	var vp: Viewport = tile.get_viewport()
	if vp == null:
		return
	vp.push_input(press)
	vp.push_input(release)



func _observe_target_frames(map_view: Node, names: Array[String]) -> Dictionary:
	# Hierarchy-agnostic: frame may live under the tile or as a MapView child
	# positioned over the region. Attribute by ancestor-or-center-in-tile.
	var frames: Array = _collect_target_frame_nodes(map_view)
	var frames_by_region: Dictionary = {}
	for region_name: String in names:
		var tile: Control = _find_region_tile(map_view, region_name)
		if tile == null:
			continue
		for frame: Node in frames:
			if not (frame is CanvasItem):
				continue
			if not (frame as CanvasItem).is_visible_in_tree():
				continue
			if _frame_belongs_to_tile(frame, tile):
				var path: String = _direct_texture_path(frame)
				frames_by_region[region_name] = path
				break
	return {
		"frame_count": frames.size(),
		"frames_by_region": frames_by_region,
	}


func _collect_target_frame_nodes(map_view: Node) -> Array:
	var found: Array = []
	_collect_target_frame_nodes_into(map_view, found)
	return found


func _collect_target_frame_nodes_into(node: Node, found: Array) -> void:
	var path: String = _direct_texture_path(node)
	if path.ends_with(TARGET_FRAME_SUFFIX) and node is CanvasItem:
		if (node as CanvasItem).is_visible_in_tree():
			found.append(node)
	for child: Node in node.get_children():
		_collect_target_frame_nodes_into(child, found)


func _frame_belongs_to_tile(frame: Node, tile: Control) -> bool:
	var walk: Node = frame
	while walk != null:
		if walk == tile:
			return true
		walk = walk.get_parent()
	if frame is Control:
		var rect: Rect2 = (frame as Control).get_global_rect()
		var center: Vector2 = rect.position + rect.size * 0.5
		return tile.get_global_rect().has_point(center)
	if frame is Node2D:
		return tile.get_global_rect().has_point((frame as Node2D).global_position)
	return false


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


func _party_silhouette_composition_sample(
	map_view: Node,
	regions: Array,
	names: Array[String],
) -> Dictionary:
	# Geometry of unit silhouettes for composition review: local rect inside the
	# tile, unit path (player vs AI), observed Settlement layer path. Placement
	# and scale are the public contract; node names are not.
	#
	# Occlusion of local y ∈ [GRID_PITCH.y, TILE_SIZE.y) assumes MapView paint
	# order: later children cover earlier ones, and model.regions is iterated
	# without sorting by row. This fixture therefore lists row=1 after row=0 so
	# the lower band of row 0 is covered by the south tile's opaque Ground.
	# A snapshot that places a higher row before a lower one would reverse
	# z-order; that is a pre-existing MapView stacking contract, not asserted
	# here as a product policy.
	if not map_view.has_method("render_model"):
		_fail("silhouette composition sample requires MapView.render_model")
		return {}
	map_view.call("render_model", _model(regions, null))
	await process_frame
	await process_frame
	# One pass: markers per region + observed vertical pitch from row 0→1.
	var markers_by_region: Dictionary = {}
	var grid_pitch_y: Variant = null
	var row0_y: Variant = null
	var row1_y: Variant = null
	for region: Variant in regions:
		if not region is Dictionary:
			continue
		var region_name: String = str(region["name"])
		var label: Label = PartyMapMark.find_label_with_text(map_view, region_name)
		if label == null:
			continue
		var tile: Control = PartyMapMark.tile_control(label, map_view)
		var tile_rect: Rect2 = tile.get_global_rect()
		var row: int = int(region.get("row", 0))
		var gy: float = tile_rect.position.y
		if row == 0 and row0_y == null:
			row0_y = gy
		elif row == 1 and row1_y == null:
			row1_y = gy
		var settlement_path: Variant = _settlement_layer_path_on_tile(tile)
		var unit_markers: Array = []
		for layer: Variant in _collect_texture_layers(tile):
			if not layer is Dictionary:
				continue
			var path: String = str(layer.get("path", ""))
			if not (
				path.ends_with("party_player_unit.png")
				or path.ends_with("party_ai_unit.png")
			):
				continue
			var copy: Dictionary = (layer as Dictionary).duplicate()
			copy["tile_name"] = region_name
			copy["tile_w"] = tile_rect.size.x
			copy["tile_h"] = tile_rect.size.y
			copy["settlement_path"] = settlement_path
			unit_markers.append(copy)
		if not unit_markers.is_empty():
			markers_by_region[region_name] = unit_markers
	if row0_y != null and row1_y != null:
		grid_pitch_y = float(row1_y) - float(row0_y)
	return {
		"markers_by_region": markers_by_region,
		"grid_pitch_y": grid_pitch_y,
	}


func _settlement_layer_path_on_tile(tile: Control) -> Variant:
	# Observed Settlement TextureRect path, or null when the tile has no settlement.
	for layer: Variant in _collect_texture_layers(tile):
		if not layer is Dictionary:
			continue
		if str(layer.get("name", "")) != "Settlement":
			continue
		var spath: String = str(layer.get("path", ""))
		return spath if not spath.is_empty() else null
	return null


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
		# Local position relative to immediate parent (RegionTile_* for markers).
		var local_x: float = 0.0
		var local_y: float = 0.0
		if node is Control:
			var ctrl: Control = node as Control
			size = ctrl.get_global_rect().size
			mouse_filter = ctrl.mouse_filter
			local_x = ctrl.position.x
			local_y = ctrl.position.y
		elif node is Sprite2D:
			var sp: Sprite2D = node as Sprite2D
			if sp.texture != null:
				var tex_size: Vector2 = sp.texture.get_size()
				size = Vector2(tex_size.x * absf(sp.scale.x), tex_size.y * absf(sp.scale.y))
			local_x = sp.position.x
			local_y = sp.position.y
		layers.append({
			"path": path,
			"name": str(node.name),
			# Local to parent (RegionTile_* for markers). w/h are global rect size.
			"local_x": local_x,
			"local_y": local_y,
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
