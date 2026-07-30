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
# G99.1b: ground keeps a light owner tint so parchment/ground art stays dominant;
# strong owner colour lives only on the small OwnershipMark + legend swatches.
const OWNER_GROUND_TINT_STRENGTH := 0.38
const OWNERSHIP_MARK_NAME := "OwnershipMark"
const OWNERSHIP_MARK_BASE_SIZE := Vector2(9, 9)
const OWNERSHIP_MARK_MARGIN := Vector2(4, 4)
const OWNER_LEGEND_NAME := "OwnerLegend"
const REGION_NAME_PLATE_TOP_MARGIN := 2.0
const REGION_NAME_PLATE_SIDE_MARGIN := 3.0
# Vertical gap between the plate bottom and the party-mark top (scaled).
const REGION_NAME_PLATE_PARTY_GAP := 2.0
# Plate stays in a shallow top band of the tile AABB (fraction of tile height).
const REGION_NAME_PLATE_MAX_TILE_FRACTION := 0.32
const REGION_NAME_PLATE_BAND_META := "region_name_plate_band"
const REGION_NAME_PLATE_BAND_BOUND_META := "region_name_plate_band_bound"
const REGION_NAME_PLATE_FONT_FLOOR := 7
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
# G99.1b: visible name plate on each tile; presentation text may differ from
# the canonical region id used by region_selected / orders.
const REGION_NAME_PLATE_NAME := "RegionNamePlate"
# Hidden label for legacy probes that still resolve tiles by Label.text.
const REGION_CANONICAL_ID_NAME := "RegionCanonicalId"
const REGION_PRESENTATION_PL: Dictionary = {
	"player lands": "Ziemie gracza",
	"player outpost": "Posterunek gracza",
	"border": "Pogranicze",
	"ai outpost": "Posterunek wroga",
	"ai lands": "Ziemie wroga",
}

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
	_refresh_owner_legend()


func _clear_tiles() -> void:
	_selected_tile = null
	_hovered_tile = null
	for child: Node in get_children():
		if str(child.name).begins_with("RegionTile_"):
			child.free()
	_remove_owner_legend()


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
	# Light tint only — full owner chroma is reserved for OwnershipMark + legend.
	ground.modulate = _owner_ground_modulate(region.get("owner"))
	tile.add_child(ground)

	_add_settlement(tile, region.get("settlement"))

	var canonical_name := str(region["name"])
	_add_region_identity_and_plate(tile, canonical_name)
	_add_ownership_mark(tile, region.get("owner"))
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


func _add_region_identity_and_plate(tile: Control, canonical: String) -> void:
	# Visible presentation plate + hidden identity for label-text probes.
	# Selection / orders always use ``canonical`` via gui_input bind, not plate text.
	tile.add_child(_region_name_plate(canonical))
	tile.add_child(_region_identity_label(canonical))


func _region_presentation_name(canonical: String) -> String:
	if REGION_PRESENTATION_PL.has(canonical):
		return str(REGION_PRESENTATION_PL[canonical])
	return canonical


func _region_name_plate(canonical: String) -> Label:
	# Plate is the Label itself (public node name RegionNamePlate) so tile
	# identity via parent RegionTile_* stays intact for probes that walk
	# label→parent, while presentation text can be Polish.
	# Narrow top strip — not full-tile — so settlement, army mark, and frames
	# stay readable in the tile body.
	var plate := Label.new()
	plate.name = REGION_NAME_PLATE_NAME
	plate.text = _region_presentation_name(canonical)
	plate.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	plate.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	plate.mouse_filter = Control.MOUSE_FILTER_IGNORE
	plate.add_theme_color_override("font_color", Color.WHITE)
	plate.add_theme_stylebox_override("normal", _region_name_plate_style())
	var font_size := _region_label_font_size_for_text(plate.text)
	plate.add_theme_font_size_override("font_size", font_size)
	_layout_region_name_plate(plate)
	return plate


func _region_name_plate_max_size() -> Vector2:
	# Width: tile inset by side margins. Height: shallow top band that clears
	# the bottom-right party mark AABB (and ownership mark lives bottom-left).
	var max_w := maxf(8.0, _tile_size.x - 2.0 * REGION_NAME_PLATE_SIDE_MARGIN * _layout_scale)
	var top := REGION_NAME_PLATE_TOP_MARGIN * _layout_scale
	var clear_of_party := (
		_party_marker_position().y - top - REGION_NAME_PLATE_PARTY_GAP * _layout_scale
	)
	var shallow_band := _tile_size.y * REGION_NAME_PLATE_MAX_TILE_FRACTION
	# Cap by party clearance (non-negative) and shallow top band. Do not
	# maxf(..., 8): that floor can exceed clear_of_party at small scales and
	# invade the party mark. An 8px minimum is only meaningful when available
	# height is already ≥ 8 (then available_h itself is the size).
	var max_h := minf(maxf(0.0, clear_of_party), shallow_band)
	return Vector2(max_w, max_h)


func _measure_region_name_plate(text: String, font_size: int) -> Vector2:
	# Font metrics — not a detached Label.get_minimum_size() — so headless
	# layout matches in-tree theme resolution and does not over-report height.
	var style := _region_name_plate_style()
	var font: Font = ThemeDB.fallback_font
	if font == null:
		return Vector2(8.0, 8.0)
	var text_size := font.get_string_size(
		text, HORIZONTAL_ALIGNMENT_LEFT, -1.0, font_size
	)
	var pad_x := (
		style.content_margin_left
		+ style.content_margin_right
		+ float(style.get_border_width(SIDE_LEFT) + style.get_border_width(SIDE_RIGHT))
	)
	var pad_y := (
		style.content_margin_top
		+ style.content_margin_bottom
		+ float(style.get_border_width(SIDE_TOP) + style.get_border_width(SIDE_BOTTOM))
	)
	return Vector2(text_size.x + pad_x, text_size.y + pad_y)


func _layout_region_name_plate(plate: Label) -> void:
	var max_size := _region_name_plate_max_size()
	var font_size := _region_label_font_size_for_text(plate.text)
	plate.add_theme_font_size_override("font_size", font_size)
	var content := _measure_region_name_plate(plate.text, font_size)
	# Always clamp both axes — including when max is 0 — so a collapsed party
	# clearance band cannot leave the plate oversized over the mark.
	var plate_w := minf(max_size.x, maxf(content.x, 8.0))
	var plate_h := minf(max_size.y, maxf(content.y, 1.0))
	# Keep the plate in the upper band of the tile AABB (away from party mark
	# bottom-right and the central settlement art).
	var band_pos := Vector2(
		(_tile_size.x - plate_w) * 0.5,
		REGION_NAME_PLATE_TOP_MARGIN * _layout_scale,
	)
	var band_size := Vector2(plate_w, plate_h)
	plate.position = band_pos
	plate.size = band_size
	# Label reapplies content min after font/style notifications and can grow
	# past the party-clearance band; re-clamp on the next idle frame with the
	# latest band (schedule again after each completed clamp).
	plate.set_meta(REGION_NAME_PLATE_BAND_META, {"pos": band_pos, "size": band_size})
	_schedule_region_name_plate_band_clamp(plate)


func _schedule_region_name_plate_band_clamp(plate: Control) -> void:
	# At most one pending deferred pass; later layouts only refresh band meta
	# until the clamp runs and clears the bound flag.
	if plate.has_meta(REGION_NAME_PLATE_BAND_BOUND_META):
		return
	plate.set_meta(REGION_NAME_PLATE_BAND_BOUND_META, true)
	# Do not use call_deferred("method", plate): MessageQueue fails typed Node
	# args with "Cannot convert argument 1 from Object to Object". Bound
	# Callable + untyped receiver is safe and keeps the clamp re-entrant.
	_clamp_region_name_plate_band.bind(plate).call_deferred()


func _clamp_region_name_plate_band(plate: Variant) -> void:
	if plate == null or not is_instance_valid(plate) or not (plate is Control):
		return
	if plate.has_meta(REGION_NAME_PLATE_BAND_BOUND_META):
		plate.remove_meta(REGION_NAME_PLATE_BAND_BOUND_META)
	var band: Variant = plate.get_meta(REGION_NAME_PLATE_BAND_META, null)
	if not band is Dictionary:
		return
	plate.position = band.get("pos", plate.position)
	plate.size = band.get("size", plate.size)


func _region_identity_label(canonical: String) -> Label:
	var identity := Label.new()
	identity.name = REGION_CANONICAL_ID_NAME
	identity.text = canonical
	identity.visible = false
	identity.mouse_filter = Control.MOUSE_FILTER_IGNORE
	return identity


func _region_name_plate_style() -> StyleBoxFlat:
	var style := StyleBoxFlat.new()
	style.bg_color = Color(0.06, 0.07, 0.10, 0.82)
	style.border_color = Color(0.92, 0.90, 0.82, 0.55)
	style.set_border_width_all(1)
	style.set_corner_radius_all(2)
	style.content_margin_left = 2.0
	style.content_margin_right = 2.0
	style.content_margin_top = 1.0
	style.content_margin_bottom = 1.0
	return style


func _region_label_font_size() -> int:
	return maxi(REGION_LABEL_FONT_SIZE, roundi(REGION_LABEL_FONT_SIZE * _layout_scale))


func _region_label_font_size_for_text(text: String) -> int:
	# Unwrapped content must fit the plate band: tile width and clearance above
	# the party mark (G94.1a / G99.1b longer PL labels). Floor stays absolute so
	# scaled lower bounds cannot block shrinking under a short party gap.
	var font_size := _region_label_font_size()
	var floor_size := REGION_NAME_PLATE_FONT_FLOOR
	var max_size := _region_name_plate_max_size()
	if max_size.x <= 0.0 or max_size.y <= 0.0:
		return floor_size
	while font_size > floor_size:
		var measured := _measure_region_name_plate(text, font_size)
		if measured.x <= max_size.x and measured.y <= max_size.y:
			break
		font_size -= 1
	return font_size


func _add_ownership_mark(tile: Control, owner: Variant) -> void:
	var mark := ColorRect.new()
	mark.name = OWNERSHIP_MARK_NAME
	mark.color = _owner_color(owner)
	mark.mouse_filter = Control.MOUSE_FILTER_IGNORE
	mark.size = _ownership_mark_size()
	mark.position = _ownership_mark_position()
	# Public meta so probes can read owner without scraping ColorRect order.
	mark.set_meta("owner_kind", _owner_kind(owner))
	tile.add_child(mark)


func _ownership_mark_size() -> Vector2:
	return OWNERSHIP_MARK_BASE_SIZE * _layout_scale


func _ownership_mark_position() -> Vector2:
	# Bottom-left corner: opposite the party mark (bottom-right) and below the
	# name plate (top strip).
	var mark_size := _ownership_mark_size()
	var margin := OWNERSHIP_MARK_MARGIN * _layout_scale
	var bottom_edge := _grid_pitch.y - margin.y
	return Vector2(margin.x, bottom_edge - mark_size.y)


func _owner_kind(owner: Variant) -> String:
	match owner:
		"player":
			return "player"
		"ai":
			return "ai"
		_:
			return "neutral"


func _remove_owner_legend() -> void:
	for child: Node in get_children():
		if child.name == OWNER_LEGEND_NAME:
			child.free()


func _owner_legend_rows() -> Array:
	return [
		{"kind": "player", "label": "Gracz", "color": PLAYER_COLOR},
		{"kind": "neutral", "label": "Neutralny", "color": NEUTRAL_COLOR},
		{"kind": "ai", "label": "Wróg", "color": AI_COLOR},
	]


func _refresh_owner_legend() -> void:
	_remove_owner_legend()
	if _rendered_regions.is_empty():
		return
	var legend := Control.new()
	legend.name = OWNER_LEGEND_NAME
	legend.mouse_filter = Control.MOUSE_FILTER_IGNORE
	# Outside tile AABBs: bottom-left of MapView with a small padding.
	var row_h := maxf(14.0, 12.0 * _layout_scale)
	var swatch := maxf(8.0, 8.0 * _layout_scale)
	var rows: Array = _owner_legend_rows()
	var legend_w := maxf(96.0, 88.0 * _layout_scale)
	var legend_h := row_h * float(rows.size()) + 4.0
	legend.size = Vector2(legend_w, legend_h)
	legend.position = Vector2(4.0, maxf(4.0, size.y - legend_h - 4.0))
	var style := StyleBoxFlat.new()
	style.bg_color = Color(0.08, 0.08, 0.10, 0.78)
	style.set_corner_radius_all(3)
	style.set_content_margin_all(3.0)
	var panel := Panel.new()
	panel.name = "OwnerLegendPanel"
	panel.mouse_filter = Control.MOUSE_FILTER_IGNORE
	panel.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	panel.add_theme_stylebox_override("panel", style)
	legend.add_child(panel)
	for index in range(rows.size()):
		var row: Dictionary = rows[index]
		var y := 3.0 + float(index) * row_h
		var chip := ColorRect.new()
		chip.name = "OwnerLegendSwatch_%s" % str(row["kind"])
		chip.color = row["color"]
		chip.position = Vector2(6.0, y + (row_h - swatch) * 0.5)
		chip.size = Vector2(swatch, swatch)
		chip.mouse_filter = Control.MOUSE_FILTER_IGNORE
		chip.set_meta("owner_kind", str(row["kind"]))
		legend.add_child(chip)
		var label := Label.new()
		label.name = "OwnerLegendLabel_%s" % str(row["kind"])
		label.text = str(row["label"])
		label.position = Vector2(6.0 + swatch + 4.0, y)
		label.size = Vector2(legend_w - swatch - 16.0, row_h)
		label.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
		label.mouse_filter = Control.MOUSE_FILTER_IGNORE
		label.add_theme_color_override("font_color", Color(0.95, 0.93, 0.88))
		label.add_theme_font_size_override(
			"font_size", maxi(10, roundi(10.0 * _layout_scale))
		)
		legend.add_child(label)
	add_child(legend)


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
			elif layer.name == OWNERSHIP_MARK_NAME and layer is Control:
				var mark := layer as Control
				mark.position = _ownership_mark_position()
				mark.size = _ownership_mark_size()
			elif layer.name == REGION_NAME_PLATE_NAME and layer is Label:
				var plate := layer as Label
				plate.add_theme_font_size_override(
					"font_size", _region_label_font_size_for_text(plate.text)
				)
				_layout_region_name_plate(plate)
			elif layer is Label and (layer as Label).visible:
				(layer as Label).add_theme_font_size_override(
					"font_size", _region_label_font_size()
				)
	# Legend sits on MapView (not under RegionTile_*); rebuild after tile layout.
	if not _rendered_regions.is_empty():
		_refresh_owner_legend()


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


func _owner_ground_modulate(owner: Variant) -> Color:
	# Soft blend toward white: ground texture remains readable; pairwise
	# visual keys stay distinct for owner_paint probes.
	return Color.WHITE.lerp(_owner_color(owner), OWNER_GROUND_TINT_STRENGTH)
