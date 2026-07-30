extends Control


const SnapshotModel = preload("res://scripts/snapshot_model.gd")
const TileTextureLayer = preload("res://scripts/tile_texture_layer.gd")
const TARGET_FRAME_TEXTURE := preload("res://assets/map_target_frame.png")
# AABB is intentionally flatter than native map_ground's pointy-top shape so
# the rendered tiles fit the stretchable map panel. These are the base hex
# proportions; the actual size is fitted to the current MapView rect.
const BASE_TILE_SIZE := Vector2(84, 48)
const BASE_GRID_PITCH := Vector2(BASE_TILE_SIZE.x, BASE_TILE_SIZE.y * 0.75)
# Leave a subpixel seam between adjacent AABBs. It prevents renderer rounding
# from turning mathematically touching controls into a one-ULP overlap while
# remaining below the layout tolerance and visually connected.
const GRID_SEAM_EPSILON := 0.01
# Tile AABBs overlap vertically; in the overlap band, the later child wins hit-testing.
# Keep the odd-row offset from the pointy-top grid while allowing the panel's
# layout-provided width to determine how much of the grid is visible.
const BASE_ODD_ROW_OFFSET := BASE_TILE_SIZE.x * 0.5
const REGION_LABEL_FONT_SIZE := 11
const PLAYER_COLOR := Color(0.16, 0.38, 0.78)
const NEUTRAL_COLOR := Color(0.38, 0.38, 0.38)
const AI_COLOR := Color(0.72, 0.18, 0.16)
const GROUND_TEXTURES: Array[Texture2D] = [
	preload("res://assets/map_ground_grass.png"),
	preload("res://assets/map_ground_earth.png"),
	preload("res://assets/map_ground_stone.png"),
]
const SETTLEMENT_TEXTURE := preload("res://assets/settlement.png")
const SETTLEMENT_KEEP_TEXTURE := preload("res://assets/settlement_keep.png")
const SETTLEMENT_OUTPOST_TEXTURE := preload("res://assets/settlement_outpost.png")
const PARTY_PLAYER_UNIT_TEXTURE := preload("res://assets/party_player_unit.png")
const PARTY_AI_UNIT_TEXTURE := preload("res://assets/party_ai_unit.png")
const PARTY_MARKER_SIZE := Vector2(16, 16)
# The vertical grid pitch is shorter than a tile, so the lower-edge margin is
# measured against the visible part of this row rather than the full AABB.
const PARTY_MARKER_MARGIN := Vector2(8, 4)
const PLAYER_PARTY_MARKER_NAME := "PlayerPartyMarker"
const AI_PARTY_MARKER_NAME := "AIPartyMarker"
const TARGET_FRAME_NAME := "MapTargetFrame"
const HOVER_FRAME_NAME := "MapHoverFrame"
const HOVER_FRAME_MODULATE := Color(0.95, 0.85, 0.35, 0.72)

signal region_selected(region_name: String)

var _selected_region_name := ""
var _selected_tile: Control
var _hovered_tile: Control
var _rendered_regions: Array = []
var _player_party_region: Variant = null
var _layout_scale := 1.0
var _tile_size := BASE_TILE_SIZE
var _grid_pitch := BASE_GRID_PITCH
var _odd_row_offset := BASE_ODD_ROW_OFFSET
var _layout_origin := Vector2.ZERO

var selected_region_name: String:
	get:
		return _selected_region_name


func _notification(what: int) -> void:
	if what != NOTIFICATION_RESIZED or _rendered_regions.is_empty():
		return
	_update_layout()
	_relayout_tiles()


func _input(event: InputEvent) -> void:
	if not event is InputEventMouseMotion:
		return
	# Viewport.push_input() updates click hit-testing in headless probes but does
	# not always synthesize Control.mouse_entered/exited. Keep the same hover
	# contract by resolving the topmost tile from the motion position as well.
	var motion := event as InputEventMouseMotion
	_set_hovered_tile(_tile_at_global_position(motion.global_position))


func render_model(model: SnapshotModel) -> void:
	_rendered_regions.clear()
	_player_party_region = null
	if model != null:
		_player_party_region = model.player_party_region
		for region: Variant in model.regions:
			if region is Dictionary and region.has("col") and region.has("row"):
				_rendered_regions.append(region)
	_update_layout()
	_clear_tiles()
	for region: Dictionary in _rendered_regions:
		_add_tile(region, _player_party_region)


func _clear_tiles() -> void:
	_selected_tile = null
	_hovered_tile = null
	for child: Node in get_children():
		if str(child.name).begins_with("RegionTile_"):
			child.free()


func _add_tile(region: Dictionary, player_party_region: Variant) -> void:
	var tile := Control.new()
	tile.name = "RegionTile_%s" % region["name"]
	tile.set_meta("map_region", region)
	tile.position = _grid_position(region)
	tile.size = _tile_size
	# Control hit-testing uses the tile AABB; STOP lets the later overlapping child receive the click.
	tile.mouse_filter = Control.MOUSE_FILTER_STOP
	tile.mouse_default_cursor_shape = Control.CURSOR_POINTING_HAND
	tile.mouse_entered.connect(_on_tile_mouse_entered.bind(tile))
	tile.mouse_exited.connect(_on_tile_mouse_exited.bind(tile))
	tile.gui_input.connect(
		_on_tile_gui_input.bind(tile, str(region["name"]))
	)
	add_child(tile)

	var ground := TileTextureLayer.full_rect(_ground_texture(region), "Ground")
	ground.modulate = _owner_color(region.get("owner"))
	tile.add_child(ground)

	_add_settlement(tile, region.get("settlement"))

	tile.add_child(_region_label(str(region["name"])))
	var party_owner: Variant = _party_owner_for_region(region, player_party_region)
	if party_owner != null:
		_add_party_marker(tile, party_owner)
	if str(region["name"]) == _selected_region_name:
		_selected_tile = tile
		_add_target_frame(tile)


func _on_tile_gui_input(event: InputEvent, tile: Control, region_name: String) -> void:
	if not event is InputEventMouseButton:
		return
	var mouse_event := event as InputEventMouseButton
	if mouse_event.button_index != MOUSE_BUTTON_LEFT or not mouse_event.pressed:
		return
	# Selection is change-oriented and idempotent; a repeated click still repairs
	# its frame in case the visual state disappeared without a region change.
	if _selected_region_name == region_name:
		_refresh_target_frame(tile)
		return
	_selected_region_name = region_name
	_refresh_target_frame(tile)
	region_selected.emit(region_name)


func _refresh_target_frame(tile: Control) -> void:
	if is_instance_valid(_selected_tile) and _selected_tile != tile:
		_remove_target_frame(_selected_tile)
	_remove_hover_frame(tile)
	_selected_tile = tile
	_add_target_frame(tile)


func _add_target_frame(tile: Control) -> void:
	_remove_target_frame(tile)
	var frame := TileTextureLayer.full_rect(TARGET_FRAME_TEXTURE, TARGET_FRAME_NAME)
	frame.mouse_filter = Control.MOUSE_FILTER_IGNORE
	tile.add_child(frame)


func _on_tile_mouse_entered(tile: Control) -> void:
	_set_hovered_tile(tile)


func _on_tile_mouse_exited(tile: Control) -> void:
	if _hovered_tile == tile:
		_set_hovered_tile(null)
	else:
		_remove_hover_frame(tile)


func _set_hovered_tile(tile: Control) -> void:
	if tile == _hovered_tile:
		return
	if is_instance_valid(_hovered_tile):
		_remove_hover_frame(_hovered_tile)
	_hovered_tile = tile if is_instance_valid(tile) else null
	if _can_add_hover_frame(_hovered_tile):
		_add_hover_frame(_hovered_tile)


func _tile_at_global_position(global_position: Vector2) -> Control:
	# Children are painted and hit-tested in order; reverse iteration preserves
	# the existing overlap rule where the later row tile wins.
	for index in range(get_child_count() - 1, -1, -1):
		var child: Node = get_child(index)
		if not child is Control or not str(child.name).begins_with("RegionTile_"):
			continue
		var tile := child as Control
		if tile.visible and tile.get_global_rect().has_point(global_position):
			return tile
	return null


func _add_hover_frame(tile: Control) -> void:
	if not _can_add_hover_frame(tile):
		return
	_remove_hover_frame(tile)
	var frame := TileTextureLayer.full_rect(TARGET_FRAME_TEXTURE, HOVER_FRAME_NAME)
	frame.modulate = HOVER_FRAME_MODULATE
	frame.mouse_filter = Control.MOUSE_FILTER_IGNORE
	tile.add_child(frame)


func _can_add_hover_frame(tile: Control) -> bool:
	return is_instance_valid(tile) and tile != _selected_tile


func _remove_hover_frame(tile: Node) -> void:
	_remove_frame(tile, HOVER_FRAME_NAME)


func _remove_target_frame(tile: Node) -> void:
	_remove_frame(tile, TARGET_FRAME_NAME)


func _remove_frame(tile: Node, frame_name: String) -> void:
	for child: Node in tile.get_children():
		if child.name == frame_name:
			child.free()


func _region_label(region_name: String) -> Label:
	var label := Label.new()
	label.text = region_name
	label.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	label.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	label.add_theme_font_size_override("font_size", _region_label_font_size())
	label.add_theme_color_override("font_color", Color.WHITE)
	return label


func _region_label_font_size() -> int:
	return maxi(REGION_LABEL_FONT_SIZE, roundi(REGION_LABEL_FONT_SIZE * _layout_scale))


func _is_player_party_region(region: Dictionary, player_party_region: Variant) -> bool:
	return (
		player_party_region is String
		and not player_party_region.is_empty()
		and region.get("name") == player_party_region
	)


func _party_owner_for_region(region: Dictionary, player_party_region: Variant) -> Variant:
	var party: Variant = region.get("party")
	if party is Dictionary:
		var owner: Variant = party.get("owner")
		return owner if owner == "player" or owner == "ai" else null
	if _is_player_party_region(region, player_party_region):
		return "player"
	return null


func _add_party_marker(tile: Control, owner: Variant) -> void:
	var marker := TileTextureLayer.stretched(_party_texture(owner))
	marker.name = PLAYER_PARTY_MARKER_NAME if owner == "player" else AI_PARTY_MARKER_NAME
	marker.position = _party_marker_position()
	marker.size = _party_marker_size()
	tile.add_child(marker)


func _party_marker_size() -> Vector2:
	return PARTY_MARKER_SIZE * _layout_scale


func _party_marker_position() -> Vector2:
	var marker_size := _party_marker_size()
	var right_edge := _tile_size.x - PARTY_MARKER_MARGIN.x * _layout_scale
	var bottom_edge := _grid_pitch.y - PARTY_MARKER_MARGIN.y * _layout_scale
	return Vector2(
		right_edge - marker_size.x,
		bottom_edge - marker_size.y,
	)


func _party_texture(owner: Variant) -> Texture2D:
	if owner == "ai":
		return PARTY_AI_UNIT_TEXTURE
	return PARTY_PLAYER_UNIT_TEXTURE


func _grid_position(region: Dictionary) -> Vector2:
	var col := float(region["col"])
	var row := int(region["row"])
	var row_offset := float(posmod(row, 2)) * _odd_row_offset
	return _layout_origin + Vector2(
		col * _grid_pitch.x + row_offset,
		float(row) * _grid_pitch.y,
	)


func _base_grid_position(region: Dictionary) -> Vector2:
	var col := float(region["col"])
	var row := int(region["row"])
	var row_offset := float(posmod(row, 2)) * BASE_ODD_ROW_OFFSET
	return Vector2(
		col * BASE_GRID_PITCH.x + row_offset,
		float(row) * BASE_GRID_PITCH.y,
	)


func _update_layout() -> void:
	if _rendered_regions.is_empty():
		return
	var bounds := _layout_bounds()
	if size.x <= 0.0 or size.y <= 0.0:
		_layout_scale = 1.0
	else:
		_layout_scale = minf(size.x / bounds.size.x, size.y / bounds.size.y)
	_layout_scale = maxf(_layout_scale, 0.01)
	_tile_size = Vector2(
		maxf(1.0, BASE_TILE_SIZE.x * _layout_scale - GRID_SEAM_EPSILON),
		BASE_TILE_SIZE.y * _layout_scale,
	)
	_grid_pitch = Vector2(
		BASE_GRID_PITCH.x * _layout_scale, _tile_size.y * 0.75
	)
	_odd_row_offset = _tile_size.x * 0.5
	_layout_origin = (size - bounds.size * _layout_scale) * 0.5
	_layout_origin -= bounds.position * _layout_scale


func _layout_bounds() -> Rect2:
	var min_position := Vector2(INF, INF)
	var max_position := Vector2(-INF, -INF)
	for region: Dictionary in _rendered_regions:
		var position := _base_grid_position(region)
		min_position.x = minf(min_position.x, position.x)
		min_position.y = minf(min_position.y, position.y)
		max_position.x = maxf(max_position.x, position.x + BASE_TILE_SIZE.x)
		max_position.y = maxf(max_position.y, position.y + BASE_TILE_SIZE.y)
	return Rect2(min_position, max_position - min_position)


func _relayout_tiles() -> void:
	for child: Node in get_children():
		if not child is Control or not str(child.name).begins_with("RegionTile_"):
			continue
		var tile := child as Control
		var region: Variant = tile.get_meta("map_region", null)
		if not region is Dictionary:
			continue
		tile.position = _grid_position(region)
		tile.size = _tile_size
		for layer: Node in tile.get_children():
			if layer.name == PLAYER_PARTY_MARKER_NAME or layer.name == AI_PARTY_MARKER_NAME:
				var marker := layer as Control
				marker.position = _party_marker_position()
				marker.size = _party_marker_size()
			elif layer is Label:
				(layer as Label).add_theme_font_size_override(
					"font_size", _region_label_font_size()
				)


func _ground_texture(region: Dictionary) -> Texture2D:
	# Use only public coordinates for deterministic decoration: col + 2*row,
	# wrapped by the number of variants. This keeps a horizontal fresh-party
	# strip varied while the same col/row pair always selects the same texture.
	return GROUND_TEXTURES[_ground_variant_index(region["col"], region["row"])]


func _ground_variant_index(col: Variant, row: Variant) -> int:
	var coordinate_key := int(col) + int(row) * 2
	return posmod(coordinate_key, GROUND_TEXTURES.size())


func _add_settlement(tile: Control, settlement: Variant) -> void:
	if settlement == null:
		return
	tile.add_child(
		TileTextureLayer.full_rect(_settlement_texture(settlement), "Settlement")
	)


func _settlement_texture(settlement: Variant) -> Texture2D:
	var settlement_name := _settlement_name(settlement)
	if settlement_name.contains("outpost"):
		return SETTLEMENT_OUTPOST_TEXTURE
	if settlement_name.contains("keep"):
		return SETTLEMENT_KEEP_TEXTURE
	return SETTLEMENT_TEXTURE


func _settlement_name(settlement: Variant) -> String:
	if settlement is Dictionary:
		return str(settlement.get("name", "")).to_lower()
	return ""


func _owner_color(owner: Variant) -> Color:
	match owner:
		"player":
			return PLAYER_COLOR
		"ai":
			return AI_COLOR
		_:
			return NEUTRAL_COLOR
