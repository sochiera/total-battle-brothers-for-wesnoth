extends Control


const SnapshotModel = preload("res://scripts/snapshot_model.gd")
const TileTextureLayer = preload("res://scripts/tile_texture_layer.gd")
const LabelTextureCarrier = preload("res://scripts/label_texture_carrier.gd")
const BASE_HEX_SIZE := Vector2(120, 140)
const AXIAL_ROW_PITCH := BASE_HEX_SIZE.y * 0.75
const FALLBACK_BATTLE_HEADER_HEIGHT := 34.0
const HEADER_GAP := 8.0
const RESULT_LABEL_GAP := 8.0
const RESULT_BANNER_PAD := 4.0
const BATTLE_RESULT_TEXTS := {
	"attacker_win": "Zwycięstwo",
	"defender_win": "Porażka",
	"draw": "Remis",
}

# Battle base fill (G103.1d): muted parchment plains hex, same family as map grounds.
const TERRAIN_PLAINS := preload("res://assets/terrain_plains.png")
# G104.1b: native-size decorations on plains (not full-hex fills); muted family.
const TERRAIN_FOREST := preload("res://assets/terrain_forest.png")
const TERRAIN_HILLS := preload("res://assets/terrain_hills.png")
# terrain field → optional overlay; Plains / unknown → no decoration.
const TERRAIN_DECORATIONS := {
	"Forest": TERRAIN_FOREST,
	"Hills": TERRAIN_HILLS,
}

# G105.1b: public side silhouettes — same isometric/¾ family as map armies
# (48×56, distinct files; muted parchment; not residual top-down RTS 64×64).
const SIDE_ATTACKER_TEXTURE := preload("res://assets/side_attacker.png")
const SIDE_DEFENDER_TEXTURE := preload("res://assets/side_defender.png")
const SIDE_SILHOUETTES := {
	"attacker": SIDE_ATTACKER_TEXTURE,
	"defender": SIDE_DEFENDER_TEXTURE,
}
# G104.1d: side-specific parchment plates (not shared badge + StyleBoxFlat rim).
const HP_BADGE_ATTACKER := preload("res://assets/battle_hp_badge_attacker.png")
const HP_BADGE_DEFENDER := preload("res://assets/battle_hp_badge_defender.png")
const HP_BADGE_BY_SIDE := {
	"attacker": HP_BADGE_ATTACKER,
	"defender": HP_BADGE_DEFENDER,
}
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
	# G105.1c: centre the occupied cluster horizontally in the panel without
	# inventing empty hexes or changing native 120×140 base geometry.
	var origin_x := _occupied_cluster_origin_x(hexes)
	var max_bottom := 0.0
	for hex: Variant in hexes:
		if not hex is Dictionary:
			continue
		var qr: Variant = _hex_qr(hex)
		if qr == null:
			continue
		_add_tile(int(qr.x), int(qr.y), hex, origin_x)
		max_bottom = maxf(max_bottom, _hex_tile_bottom(int(qr.y)))
	_layout_result_label(max_bottom)


func _hex_qr(hex: Dictionary) -> Variant:
	if not hex.has("q") or not hex.has("r"):
		return null
	return Vector2i(int(hex["q"]), int(hex["r"]))


func _occupied_cluster_origin_x(hexes: Array) -> float:
	## Horizontal origin so the AABB of occupied hexes is centred in this view.
	var bounds: Variant = _occupied_cluster_x_bounds(hexes)
	if bounds == null:
		return 0.0
	var min_left: float = bounds.x
	var max_right: float = bounds.y
	var cluster_w := max_right - min_left
	return (_panel_width_for_cluster() - cluster_w) * 0.5 - min_left


func _occupied_cluster_x_bounds(hexes: Array) -> Variant:
	## Local (pre-origin) left/right of the occupied hex AABB, or null if empty.
	var min_left := INF
	var max_right := -INF
	var any := false
	for hex: Variant in hexes:
		if not hex is Dictionary:
			continue
		var qr: Variant = _hex_qr(hex)
		if qr == null:
			continue
		any = true
		var local_x := _axial_local_x(int(qr.x), int(qr.y))
		min_left = minf(min_left, local_x)
		max_right = maxf(max_right, local_x + BASE_HEX_SIZE.x)
	if not any:
		return null
	return Vector2(min_left, max_right)


func _panel_width_for_cluster() -> float:
	## Prefer the laid-out panel width. Headless / early render can still report
	## only custom_minimum_size.x on this Control while MapAndBattle is wider —
	## parent width (and min size) keep centering against the real parchment.
	var view_w := size.x
	var parent_ctrl := get_parent() as Control
	if parent_ctrl != null:
		view_w = maxf(view_w, parent_ctrl.size.x)
	if view_w <= 0.0:
		view_w = custom_minimum_size.x
	return view_w


func _hex_tile_bottom(row: int) -> float:
	return _battle_header_band_height() + float(row) * AXIAL_ROW_PITCH + BASE_HEX_SIZE.y


func _layout_result_label(max_hex_bottom: float) -> void:
	var result_label: Control = %BattleResultLabel
	var result_banner: Control = %BattleResultBanner
	var result_top := max_hex_bottom + RESULT_LABEL_GAP
	result_label.position.y = result_top
	# Parchment carrier tracks the outcome text band (not a fixed scene offset).
	result_banner.position.y = result_top - RESULT_BANNER_PAD
	result_banner.size.y = result_label.size.y + RESULT_BANNER_PAD * 2.0
	var required_height: float = maxf(
		result_top + result_label.size.y,
		result_banner.position.y + result_banner.size.y,
	)
	custom_minimum_size.y = required_height
	size.y = required_height


func _reset_and_hide_view() -> void:
	visible = false
	_clear_hex_tiles()
	%BattleResultLabel.text = ""


func _clear_hex_tiles() -> void:
	for child: Node in get_children():
		if str(child.name).begins_with("HexTile_"):
			child.free()


func _battle_data(model: SnapshotModel) -> Variant:
	if model == null or not model.battle is Dictionary:
		return null
	return model.battle


func _add_tile(q: int, r: int, hex: Dictionary, origin_x: float) -> void:
	var tile := Control.new()
	tile.name = "HexTile_%d_%d" % [q, r]
	tile.position = _axial_position(q, r, origin_x)
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
	if not hp is int and not hp is float:
		return
	var badge_tex: Texture2D = _hp_badge_texture(side)
	if badge_tex == null:
		return

	# Side-specific parchment plate under PŻ (G102.1b / G104.1d). Side cue is
	# the texture path, not a StyleBoxFlat rim. Carrier: LabelTextureCarrier
	# (R102.1 / task-578), same as MapView region name plates.
	var badge := LabelTextureCarrier.make(badge_tex, "HpBadge")
	badge.position = Vector2(
		HP_MARKER_MARGIN.x,
		BASE_HEX_SIZE.y - HP_MARKER_MARGIN.y - HP_MARKER_SIZE.y,
	)
	badge.size = HP_MARKER_SIZE
	LabelTextureCarrier.attach_label(badge, _make_hp_marker_label(int(hp)))
	tile.add_child(badge)


func _make_hp_marker_label(hp: int) -> Label:
	var marker := Label.new()
	marker.name = "HpMarker"
	marker.text = "PŻ %d" % hp
	marker.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	marker.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	marker.add_theme_font_size_override("font_size", 13)
	marker.add_theme_color_override("font_color", Color(0.18, 0.12, 0.08, 1))
	# Transparent fill only — no residual flat border as side cue (G104.1d).
	marker.add_theme_stylebox_override("normal", _hp_marker_fill_style())
	return marker


func _hp_marker_fill_style() -> StyleBoxFlat:
	var style := StyleBoxFlat.new()
	style.bg_color = Color(0, 0, 0, 0)
	style.content_margin_left = 4
	style.content_margin_right = 4
	return style


func _hp_badge_texture(side: Variant) -> Texture2D:
	return HP_BADGE_BY_SIDE.get(side)


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


func _axial_local_x(q: int, r: int) -> float:
	## Pointy-top axial X without panel origin (cluster centering is separate).
	return float(q) * BASE_HEX_SIZE.x + float(r) * BASE_HEX_SIZE.x * 0.5


func _axial_position(q: int, r: int, origin_x: float = 0.0) -> Vector2:
	return Vector2(
		origin_x + _axial_local_x(q, r),
		_battle_header_band_height() + float(r) * AXIAL_ROW_PITCH,
	)


func _battle_header_band_height() -> float:
	return _battle_header_height() + HEADER_GAP


func _battle_header_height() -> float:
	var header := get_node_or_null("BattleHeaderLabel") as Control
	if header == null:
		return FALLBACK_BATTLE_HEADER_HEIGHT

	var header_height := maxf(header.size.y, header.offset_bottom - header.offset_top)
	if header_height <= 0.0:
		header_height = FALLBACK_BATTLE_HEADER_HEIGHT
	return header_height


func _terrain_decoration_texture(terrain: Variant) -> Texture2D:
	return TERRAIN_DECORATIONS.get(terrain)


func _side_silhouette_texture(side: Variant) -> Texture2D:
	return SIDE_SILHOUETTES.get(side)


func _result_text(result: Variant) -> String:
	return BATTLE_RESULT_TEXTS.get(result, "")
