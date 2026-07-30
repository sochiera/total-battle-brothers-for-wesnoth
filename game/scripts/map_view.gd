extends Control


const SnapshotModel = preload("res://scripts/snapshot_model.gd")
const TileTextureLayer = preload("res://scripts/tile_texture_layer.gd")
const TARGET_FRAME_TEXTURE := preload("res://assets/map_target_frame.png")
# AABB is intentionally flatter than native map_ground's pointy-top shape so
# the rendered tiles fit the stretchable map panel (minimum about 420x240;
# at 1152x648 its width comes from the scene layout).
const TILE_SIZE := Vector2(84, 48)
const GRID_PITCH := Vector2(TILE_SIZE.x, TILE_SIZE.y * 0.75)
# Tile AABBs overlap vertically; in the overlap band, the later child wins hit-testing.
# Keep the odd-row offset from the pointy-top grid while allowing the panel's
# layout-provided width to determine how much of the grid is visible.
const ODD_ROW_OFFSET := TILE_SIZE.x * 0.5
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

signal region_selected(region_name: String)

var _selected_region_name := ""
var _selected_tile: Control


func render_model(model: SnapshotModel) -> void:
	_clear_tiles()
	if model == null:
		return
	for region: Variant in model.regions:
		if region is Dictionary and region.has("col") and region.has("row"):
			_add_tile(region, model.player_party_region)


func _clear_tiles() -> void:
	_selected_tile = null
	for child: Node in get_children():
		if str(child.name).begins_with("RegionTile_"):
			child.free()


func _add_tile(region: Dictionary, player_party_region: Variant) -> void:
	var tile := Control.new()
	tile.name = "RegionTile_%s" % region["name"]
	tile.position = _grid_position(region)
	tile.size = TILE_SIZE
	# Control hit-testing uses the tile AABB; STOP lets the later overlapping child receive the click.
	tile.mouse_filter = Control.MOUSE_FILTER_STOP
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
	_selected_tile = tile
	_add_target_frame(tile)


func _add_target_frame(tile: Control) -> void:
	_remove_target_frame(tile)
	var frame := TileTextureLayer.full_rect(TARGET_FRAME_TEXTURE, TARGET_FRAME_NAME)
	frame.mouse_filter = Control.MOUSE_FILTER_IGNORE
	tile.add_child(frame)


func _remove_target_frame(tile: Node) -> void:
	for child: Node in tile.get_children():
		if child.name == TARGET_FRAME_NAME:
			child.free()


func _region_label(region_name: String) -> Label:
	var label := Label.new()
	label.text = region_name
	label.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	label.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	label.add_theme_font_size_override("font_size", REGION_LABEL_FONT_SIZE)
	label.add_theme_color_override("font_color", Color.WHITE)
	return label


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
	marker.size = PARTY_MARKER_SIZE
	tile.add_child(marker)


func _party_marker_position() -> Vector2:
	var right_edge := TILE_SIZE.x - PARTY_MARKER_MARGIN.x
	var bottom_edge := GRID_PITCH.y - PARTY_MARKER_MARGIN.y
	return Vector2(
		right_edge - PARTY_MARKER_SIZE.x,
		bottom_edge - PARTY_MARKER_SIZE.y,
	)


func _party_texture(owner: Variant) -> Texture2D:
	if owner == "ai":
		return PARTY_AI_UNIT_TEXTURE
	return PARTY_PLAYER_UNIT_TEXTURE


func _grid_position(region: Dictionary) -> Vector2:
	var col := float(region["col"])
	var row := int(region["row"])
	var row_offset := float(posmod(row, 2)) * ODD_ROW_OFFSET
	return Vector2(
		col * GRID_PITCH.x + row_offset,
		float(row) * GRID_PITCH.y,
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
