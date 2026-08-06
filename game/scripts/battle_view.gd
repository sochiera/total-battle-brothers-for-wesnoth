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
# Floor when Main with-battle fit must shrink the cluster so MapView stays readable.
const MIN_CLUSTER_LAYOUT_SCALE := 0.45
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

# 1.0 = native G98/G105 geometry; Main may lower this under with-battle chrome fit.
var _layout_scale := 1.0
var _last_hexes: Array = []
# INF = no vertical budget from Main; finite = fit_vertical_budget last request.
var _vertical_budget := INF


func _notification(what: int) -> void:
	if what != NOTIFICATION_RESIZED or not visible or _last_hexes.is_empty():
		return
	# Container layout can change the panel size after Main rendered the model;
	# re-fit then so a first frame cannot retain a cluster sized for stale bounds.
	fit_vertical_budget(_vertical_budget)


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
	_last_hexes = hexes.duplicate()
	_layout_scale = 1.0
	_render_hexes(_last_hexes)
	# Apply the horizontal panel fit even before Main supplies a vertical budget;
	# probes and early layout frames can render this view with only its minimum
	# width available. A later Main fit then adds the viewport-height constraint.
	fit_vertical_budget(_vertical_budget)


func fit_vertical_budget(max_height: float) -> void:
	## Scale occupied hex cluster so it fits both panel axes and max_height.
	## Native 120×140 when budget allows; used only when MapView readability floor
	## would otherwise be crushed by multi-row battle chrome.
	_vertical_budget = max_height
	if not visible or _last_hexes.is_empty():
		return
	if max_height <= 0.0:
		return
	var native_h := _required_height_at_scale(1.0)
	var target_scale := _horizontal_fit_scale()
	if native_h > max_height:
		# Header + result label/pad stay fixed; hex geometry and result gap scale.
		var fixed_h := _battle_header_band_height() + _result_label_and_banner_pad()
		var variable_h := maxf(1.0, native_h - fixed_h)
		var room := maxf(0.0, max_height - fixed_h)
		target_scale = minf(
			target_scale, clampf(room / variable_h, MIN_CLUSTER_LAYOUT_SCALE, 1.0)
		)
	target_scale = clampf(target_scale, MIN_CLUSTER_LAYOUT_SCALE, 1.0)
	if absf(target_scale - _layout_scale) < 0.001:
		return
	_layout_scale = target_scale
	_clear_hex_tiles()
	_render_hexes(_last_hexes)


func clear_vertical_budget() -> void:
	_vertical_budget = INF
	if _layout_scale == 1.0:
		return
	_layout_scale = 1.0
	if visible and not _last_hexes.is_empty():
		_clear_hex_tiles()
		_render_hexes(_last_hexes)


func _hex_size() -> Vector2:
	return BASE_HEX_SIZE * _layout_scale


func _row_pitch() -> float:
	return _hex_size().y * 0.75


func _result_label_and_banner_pad() -> float:
	## Fixed (non-scaling) part of the result band: label height + bottom banner pad.
	var result_label: Control = %BattleResultLabel
	return result_label.size.y + RESULT_BANNER_PAD


func _result_band_height_at_scale(scale: float) -> float:
	## result_top = max_hex_bottom + GAP*scale; panel bottom = result_top + label_h + PAD.
	return RESULT_LABEL_GAP * scale + _result_label_and_banner_pad()


func _panel_height_for_hex_bottom(max_hex_bottom: float, scale: float) -> float:
	## Shared by fit (`_required_height_at_scale`) and `_layout_result_label`.
	return max_hex_bottom + _result_band_height_at_scale(scale)


func _required_height_at_scale(scale: float) -> float:
	## Panel height required at layout scale — same closed form as layout.
	var saved := _layout_scale
	_layout_scale = scale
	var max_r := -1
	for hex: Variant in _last_hexes:
		if not hex is Dictionary:
			continue
		var qr: Variant = _hex_qr(hex)
		if qr == null:
			continue
		max_r = maxi(max_r, int(qr.y))
	var height: float
	if max_r >= 0:
		height = _panel_height_for_hex_bottom(_hex_tile_bottom(max_r), scale)
	else:
		height = _panel_height_for_hex_bottom(_battle_header_band_height(), scale)
	_layout_scale = saved
	return height


func _render_hexes(hexes: Array) -> void:
	# G105.1c: centre the occupied cluster horizontally in the panel without
	# inventing empty hexes. Scale may be < 1 under with-battle chrome fit.
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
		max_right = maxf(max_right, local_x + _hex_size().x)
	if not any:
		return null
	return Vector2(min_left, max_right)


func _horizontal_fit_scale() -> float:
	## Keep the full occupied AABB inside BattleView; the parent container may
	## be wider than this panel, so centring against it would leak tiles out of
	## the visible parchment by the excess parent width.
	if _last_hexes.is_empty():
		return 1.0
	var saved := _layout_scale
	_layout_scale = 1.0
	var bounds: Variant = _occupied_cluster_x_bounds(_last_hexes)
	_layout_scale = saved
	if bounds == null:
		return 1.0
	var cluster_w: float = maxf(1.0, bounds.y - bounds.x)
	return clampf(_panel_width_for_cluster() / cluster_w, 0.01, 1.0)


func _panel_width_for_cluster() -> float:
	## Use the actual panel width. MapAndBattle can be wider than BattleView;
	## using the parent here centres the cluster partly outside this panel.
	var view_w := size.x
	if view_w <= 0.0:
		view_w = custom_minimum_size.x
	return view_w


func _hex_tile_bottom(row: int) -> float:
	return _battle_header_band_height() + float(row) * _row_pitch() + _hex_size().y


func _layout_result_label(max_hex_bottom: float) -> void:
	var result_label: Control = %BattleResultLabel
	var result_banner: Control = %BattleResultBanner
	var result_top := max_hex_bottom + RESULT_LABEL_GAP * _layout_scale
	result_label.position.y = result_top
	# Parchment carrier tracks the outcome text band (not a fixed scene offset).
	result_banner.position.y = result_top - RESULT_BANNER_PAD
	result_banner.size.y = result_label.size.y + RESULT_BANNER_PAD * 2.0
	var required_height: float = _panel_height_for_hex_bottom(max_hex_bottom, _layout_scale)
	custom_minimum_size.y = required_height
	size.y = required_height


func _reset_and_hide_view() -> void:
	visible = false
	# Drop vertical minimum so MapAndBattle can collapse (G94.1d). Height is set
	# by _layout_result_label when a battle is shown; zero here clears that
	# content-driven minimum (not a scene default of 240).
	custom_minimum_size.y = 0.0
	_layout_scale = 1.0
	_last_hexes = []
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
	tile.size = _hex_size()
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
		var margin := SIDE_SILHOUETTE_MARGIN * _layout_scale
		silhouette.offset_left += margin.x
		silhouette.offset_right -= margin.x
		silhouette.offset_top += margin.y
		silhouette.offset_bottom -= margin.y
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
	var margin := HP_MARKER_MARGIN * _layout_scale
	var badge_size := HP_MARKER_SIZE * _layout_scale
	badge.position = Vector2(
		margin.x,
		_hex_size().y - margin.y - badge_size.y,
	)
	badge.size = badge_size
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
		var decor_host := _hex_size()
		tile.add_child(
			TileTextureLayer.native_rect(decoration_texture, "TerrainDecoration", decor_host)
		)


func _apply_hex_paint_order(tile: Control, row: int) -> void:
	# Pointy-top rows overlap vertically; higher rows must paint above lower rows.
	tile.z_index = row


func _axial_local_x(q: int, r: int) -> float:
	## Pointy-top axial X without panel origin (cluster centering is separate).
	var hex_w := _hex_size().x
	return float(q) * hex_w + float(r) * hex_w * 0.5


func _axial_position(q: int, r: int, origin_x: float = 0.0) -> Vector2:
	return Vector2(
		origin_x + _axial_local_x(q, r),
		_battle_header_band_height() + float(r) * _row_pitch(),
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
