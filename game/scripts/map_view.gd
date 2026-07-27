extends Control


const SnapshotModel = preload("res://scripts/snapshot_model.gd")
const TileTextureLayer = preload("res://scripts/tile_texture_layer.gd")
const TILE_SIZE := Vector2(124, 64)
const TILE_GAP := Vector2(12, 12)
const PLAYER_COLOR := Color(0.16, 0.38, 0.78)
const NEUTRAL_COLOR := Color(0.38, 0.38, 0.38)
const AI_COLOR := Color(0.72, 0.18, 0.16)
const GROUND_TEXTURE := preload("res://assets/map_ground.png")
const SETTLEMENT_TEXTURE := preload("res://assets/settlement.png")
const PARTY_TEXTURE := preload("res://assets/party_player.png")


func render_model(model: SnapshotModel) -> void:
	_clear_tiles()
	if model == null:
		return
	for region: Variant in model.regions:
		if region is Dictionary and region.has("col") and region.has("row"):
			_add_tile(region, model.player_party_region)


func _clear_tiles() -> void:
	for child: Node in get_children():
		if str(child.name).begins_with("RegionTile_"):
			child.free()


func _add_tile(region: Dictionary, player_party_region: Variant) -> void:
	var tile := Control.new()
	tile.name = "RegionTile_%s" % region["name"]
	tile.position = _grid_position(region)
	tile.size = TILE_SIZE
	tile.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(tile)

	var ground := TileTextureLayer.full_rect(GROUND_TEXTURE, "Ground")
	ground.modulate = _owner_color(region.get("owner"))
	tile.add_child(ground)

	if region.get("settlement") != null:
		tile.add_child(TileTextureLayer.full_rect(SETTLEMENT_TEXTURE, "Settlement"))

	var label := Label.new()
	label.text = region["name"]
	label.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	label.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	label.add_theme_color_override("font_color", Color.WHITE)
	tile.add_child(label)
	if _is_player_party_region(region, player_party_region):
		_add_player_party_marker(tile)


func _is_player_party_region(region: Dictionary, player_party_region: Variant) -> bool:
	return (
		player_party_region is String
		and not player_party_region.is_empty()
		and region.get("name") == player_party_region
	)


func _add_player_party_marker(tile: Control) -> void:
	var marker := TileTextureLayer.stretched(PARTY_TEXTURE)
	marker.name = "PlayerPartyMarker"
	marker.position = Vector2(TILE_SIZE.x - 24, 8)
	marker.size = Vector2(16, 16)
	tile.add_child(marker)


func _grid_position(region: Dictionary) -> Vector2:
	return Vector2(
		float(region["col"]) * (TILE_SIZE.x + TILE_GAP.x),
		float(region["row"]) * (TILE_SIZE.y + TILE_GAP.y),
	)


func _owner_color(owner: Variant) -> Color:
	match owner:
		"player":
			return PLAYER_COLOR
		"ai":
			return AI_COLOR
		_:
			return NEUTRAL_COLOR
