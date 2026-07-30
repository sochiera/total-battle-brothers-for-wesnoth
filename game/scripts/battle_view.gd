extends Control


const SnapshotModel = preload("res://scripts/snapshot_model.gd")
const TileTextureLayer = preload("res://scripts/tile_texture_layer.gd")
const BASE_HEX_SIZE := Vector2(120, 140)
const AXIAL_ROW_PITCH := BASE_HEX_SIZE.y * 0.75
const RESULT_LABEL_GAP := 8.0

const TERRAIN_PLAINS := preload("res://assets/terrain_plains.png")
const TERRAIN_FOREST := preload("res://assets/terrain_forest.png")
const TERRAIN_HILLS := preload("res://assets/terrain_hills.png")

const SIDE_ATTACKER_TEXTURE := preload("res://assets/side_attacker.png")
const SIDE_DEFENDER_TEXTURE := preload("res://assets/side_defender.png")
const SIDE_SILHOUETTE_MARGIN := Vector2(20, 14)
const HP_MARKER_MARGIN := Vector2(16, 5)
const HP_MARKER_SIZE := Vector2(88, 24)


func render_model(model: SnapshotModel) -> void:
	_reset_and_hide_view()
	var battle: Variant = _battle_data(model)
	if battle == null:
		return

	visible = true
	%BattleResultLabel.text = _result_text(battle.get("result"))
	var hexes: Variant = battle.get("hexes")
	if not hexes is Array:
		return
	_render_hexes(hexes)


func _render_hexes(hexes: Array) -> void:
	var max_bottom := 0.0
	for hex: Variant in hexes:
		if hex is Dictionary:
			_add_tile(hex)
			var q: int = int(hex.get("q", 0))
			var r: int = int(hex.get("r", 0))
			max_bottom = maxf(max_bottom, _axial_position(q, r).y + BASE_HEX_SIZE.y)
	_layout_result_label(max_bottom)


func _layout_result_label(max_hex_bottom: float) -> void:
	var result_label: Control = %BattleResultLabel
	var result_top := max_hex_bottom + RESULT_LABEL_GAP
	result_label.position.y = result_top
	var required_height: float = result_top + result_label.size.y
	custom_minimum_size.y = required_height
	size.y = required_height


func _reset_and_hide_view() -> void:
	visible = false
	for child: Node in get_children():
		if str(child.name).begins_with("HexTile_"):
			child.free()
	%BattleResultLabel.text = ""


func _battle_data(model: SnapshotModel) -> Variant:
	if model == null or not model.battle is Dictionary:
		return null
	return model.battle


func _add_tile(hex: Dictionary) -> void:
	if not hex.has("q") or not hex.has("r"):
		return

	var q: int = int(hex["q"])
	var r: int = int(hex["r"])
	var tile := Control.new()
	tile.name = "HexTile_%d_%d" % [q, r]
	tile.position = _axial_position(q, r)
	tile.size = BASE_HEX_SIZE
	_apply_hex_paint_order(tile, r)
	tile.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(tile)
	_add_terrain_layers(tile, hex.get("terrain"))
	_add_unit_overlay(tile, hex.get("side"), hex.get("hp"))


func _add_unit_overlay(tile: Control, side: Variant, hp: Variant) -> void:
	var silhouette_texture: Texture2D = _side_silhouette_texture(side)
	if silhouette_texture != null:
		var silhouette := TextureRect.new()
		silhouette.name = "SideSilhouette"
		silhouette.texture = silhouette_texture
		silhouette.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
		silhouette.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
		silhouette.mouse_filter = Control.MOUSE_FILTER_IGNORE
		silhouette.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
		silhouette.offset_left += SIDE_SILHOUETTE_MARGIN.x
		silhouette.offset_right -= SIDE_SILHOUETTE_MARGIN.x
		silhouette.offset_top += SIDE_SILHOUETTE_MARGIN.y
		silhouette.offset_bottom -= SIDE_SILHOUETTE_MARGIN.y
		tile.add_child(silhouette)
	_add_hp_marker(tile, side, hp)


func _add_hp_marker(tile: Control, side: Variant, hp: Variant) -> void:
	if side != "attacker" and side != "defender":
		return
	if not hp is int and not hp is float:
		return

	var marker := Label.new()
	marker.name = "HpMarker"
	marker.text = "PŻ %d" % int(hp)
	marker.position = Vector2(
		HP_MARKER_MARGIN.x,
		BASE_HEX_SIZE.y - HP_MARKER_MARGIN.y - HP_MARKER_SIZE.y,
	)
	marker.size = HP_MARKER_SIZE
	marker.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	marker.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	marker.mouse_filter = Control.MOUSE_FILTER_IGNORE
	marker.add_theme_font_size_override("font_size", 13)
	marker.add_theme_color_override("font_color", Color(0.98, 0.98, 0.94, 1))
	marker.add_theme_stylebox_override("normal", _hp_marker_style(side))
	tile.add_child(marker)


func _hp_marker_style(side: Variant) -> StyleBoxFlat:
	var style := StyleBoxFlat.new()
	style.bg_color = Color(0.04, 0.05, 0.08, 0.92)
	style.border_width_left = 2
	style.border_width_top = 2
	style.border_width_right = 2
	style.border_width_bottom = 2
	style.border_color = _side_marker_color(side)
	style.corner_radius_top_left = 5
	style.corner_radius_top_right = 5
	style.corner_radius_bottom_right = 5
	style.corner_radius_bottom_left = 5
	style.content_margin_left = 4
	style.content_margin_right = 4
	return style


func _side_marker_color(side: Variant) -> Color:
	if side == "attacker":
		return Color(0.95, 0.34, 0.22, 1)
	return Color(0.30, 0.66, 1.0, 1)


func _add_terrain_layers(tile: Control, terrain: Variant) -> void:
	var base := TileTextureLayer.full_rect(TERRAIN_PLAINS, "Base")
	tile.add_child(base)

	var decoration_texture: Texture2D = _terrain_decoration_texture(terrain)
	if decoration_texture != null:
		tile.add_child(
			TileTextureLayer.native_rect(decoration_texture, "TerrainDecoration", BASE_HEX_SIZE)
		)


func _apply_hex_paint_order(tile: Control, row: int) -> void:
	# Pointy-top rows overlap vertically; higher rows must paint above lower rows.
	tile.z_index = row


func _axial_position(q: int, r: int) -> Vector2:
	return Vector2(
		float(q) * BASE_HEX_SIZE.x + float(r) * BASE_HEX_SIZE.x * 0.5,
		float(r) * AXIAL_ROW_PITCH,
	)


func _terrain_decoration_texture(terrain: Variant) -> Texture2D:
	match terrain:
		"Forest":
			return TERRAIN_FOREST
		"Hills":
			return TERRAIN_HILLS
		_:
			return null


func _side_silhouette_texture(side: Variant) -> Texture2D:
	match side:
		"attacker":
			return SIDE_ATTACKER_TEXTURE
		"defender":
			return SIDE_DEFENDER_TEXTURE
		_:
			return null


func _result_text(result: Variant) -> String:
	match result:
		"attacker_win":
			return "Bitwa: zwycięstwo"
		"defender_win":
			return "Bitwa: porażka"
		"draw":
			return "Bitwa: remis"
		_:
			return ""
