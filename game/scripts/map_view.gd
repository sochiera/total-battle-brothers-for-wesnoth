extends Control


const SnapshotModel = preload("res://scripts/snapshot_model.gd")
const TILE_SIZE := Vector2(124, 64)
const TILE_GAP := Vector2(12, 12)
const PLAYER_COLOR := Color(0.16, 0.38, 0.78)
const NEUTRAL_COLOR := Color(0.38, 0.38, 0.38)
const AI_COLOR := Color(0.72, 0.18, 0.16)


func render_model(model: SnapshotModel) -> void:
	_clear_tiles()
	if model == null:
		return
	for region: Variant in model.regions:
		if region is Dictionary and region.has("col") and region.has("row"):
			_add_tile(region)


func _clear_tiles() -> void:
	for child: Node in get_children():
		if str(child.name).begins_with("RegionTile_"):
			child.free()


func _add_tile(region: Dictionary) -> void:
	var tile := ColorRect.new()
	tile.name = "RegionTile_%s" % region["name"]
	tile.color = _owner_color(region.get("owner"))
	tile.position = _grid_position(region)
	tile.size = TILE_SIZE
	tile.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(tile)

	var label := Label.new()
	label.text = region["name"]
	label.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	label.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	label.add_theme_color_override("font_color", Color.WHITE)
	tile.add_child(label)


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
