extends Control


const SnapshotModel = preload("res://scripts/snapshot_model.gd")
const TileTextureLayer = preload("res://scripts/tile_texture_layer.gd")
const TARGET_FRAME_TEXTURE := preload("res://assets/map_target_frame.png")
const MAP_THEATER_FRAME_TEXTURE := preload("res://assets/map_theater_frame.png")
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
# G99.1b / G101.1a: light owner tint on ground only (parchment stays dominant).
# Full owner identity is the textured OwnershipMark crest plus matching legend
# crests (same OWNER_MARK_* textures) — not solid colour fills on the mark.
const OWNER_GROUND_TINT_STRENGTH := 0.38
const OWNERSHIP_MARK_NAME := "OwnershipMark"
const OWNERSHIP_MARK_BASE_SIZE := Vector2(9, 9)
const OWNERSHIP_MARK_MARGIN := Vector2(4, 4)
const OWNER_MARK_PLAYER_TEXTURE := preload("res://assets/owner_mark_player.png")
const OWNER_MARK_NEUTRAL_TEXTURE := preload("res://assets/owner_mark_neutral.png")
const OWNER_MARK_AI_TEXTURE := preload("res://assets/owner_mark_ai.png")
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
# Padding inside the parchment texture for font metrics (matches content margins).
const REGION_NAME_PLATE_PAD := Vector2(4.0, 2.0)
# Dark ink on parchment — readable without the old near-black HUD fill.
const REGION_NAME_PLATE_INK := Color(0.18, 0.12, 0.08, 1.0)
const REGION_NAME_PLATE_TEXTURE := preload("res://assets/region_name_plate.png")
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
# Campaign theater under the region strip (G100.1b); not full-panel parchment.
const MAP_THEATER_FRAME_NAME := "MapTheaterFrame"
# Soft padding so the wood rim frames hex AABBs without covering neighbours.
const MAP_THEATER_FRAME_PAD := Vector2(18, 16)
# G99.1b: visible name plate on each tile; presentation text may differ from
# the canonical region id used by region_selected / orders.
const REGION_NAME_PLATE_NAME := "RegionNamePlate"
# Hidden label for legacy probes that still resolve tiles by Label.text.
const REGION_CANONICAL_ID_NAME := "RegionCanonicalId"
const WorldPresentation = preload("res://scripts/world_presentation.gd")

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
	_refresh_map_theater_frame()
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


func _refresh_map_theater_frame() -> void:
	# Dedicated board under RegionTile_* only — StrategicMapBackground stays
	# full-panel parchment; this theater tracks the fitted hex strip bounds.
	var existing := get_node_or_null(MAP_THEATER_FRAME_NAME) as TextureRect
	if _rendered_regions.is_empty():
		if existing != null:
			existing.free()
		return
	var frame := existing
	if frame == null:
		frame = TextureRect.new()
		frame.name = MAP_THEATER_FRAME_NAME
		frame.texture = MAP_THEATER_FRAME_TEXTURE
		frame.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
		frame.stretch_mode = TextureRect.STRETCH_SCALE
		frame.mouse_filter = Control.MOUSE_FILTER_IGNORE
		add_child(frame)
	else:
		frame.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_place_map_theater_frame_behind_tiles(frame)
	var theater_rect := _map_theater_frame_local_rect(_region_strip_local_rect())
	frame.position = theater_rect.position
	frame.size = theater_rect.size


func _place_map_theater_frame_behind_tiles(frame: Node) -> void:
	# After full-panel parchment, before any RegionTile_* (draw under tiles).
	var insert_at := 0
	if get_child_count() > 0 and str(get_child(0).name) == "StrategicMapBackground":
		insert_at = 1
	if frame.get_index() != insert_at:
		move_child(frame, insert_at)


func _region_strip_local_rect() -> Rect2:
	# Union of fitted RegionTile_* AABBs in MapView local space.
	var min_position := Vector2(INF, INF)
	var max_position := Vector2(-INF, -INF)
	for region: Dictionary in _rendered_regions:
		var position := _grid_position(region)
		min_position.x = minf(min_position.x, position.x)
		min_position.y = minf(min_position.y, position.y)
		max_position.x = maxf(max_position.x, position.x + _tile_size.x)
		max_position.y = maxf(max_position.y, position.y + _tile_size.y)
	return Rect2(min_position, max_position - min_position)


func _map_theater_frame_local_rect(strip_bounds: Rect2) -> Rect2:
	# Expand strip by MAP_THEATER_FRAME_PAD, but only into free margin inside
	# local Rect2(Vector2.ZERO, size) so clip_contents never cuts the rim while
	# the frame still fully covers every tile AABB.
	var desired_pad := MAP_THEATER_FRAME_PAD * _layout_scale
	var pad_left := maxf(0.0, minf(desired_pad.x, strip_bounds.position.x))
	var pad_top := maxf(0.0, minf(desired_pad.y, strip_bounds.position.y))
	var pad_right := maxf(
		0.0,
		minf(desired_pad.x, size.x - (strip_bounds.position.x + strip_bounds.size.x))
	)
	var pad_bottom := maxf(
		0.0,
		minf(desired_pad.y, size.y - (strip_bounds.position.y + strip_bounds.size.y))
	)
	return Rect2(
		strip_bounds.position - Vector2(pad_left, pad_top),
		strip_bounds.size + Vector2(pad_left + pad_right, pad_top + pad_bottom)
	)


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
	# Soft ground tint only. Owner ID: textured crest + matching legend crest.
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


func _region_name_plate(canonical: String) -> Control:
	# Public node RegionNamePlate is a textured parchment carrier (not a dark
	# StyleBoxFlat Label). Presentation text is a child Label so probes can
	# still walk plate → first Label while texture_paths reports the asset.
	# Narrow top strip — not full-tile — so settlement, army mark, and frames
	# stay readable in the tile body.
	var plate := TextureRect.new()
	plate.name = REGION_NAME_PLATE_NAME
	plate.texture = REGION_NAME_PLATE_TEXTURE
	plate.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	plate.stretch_mode = TextureRect.STRETCH_SCALE
	plate.mouse_filter = Control.MOUSE_FILTER_IGNORE

	var label := Label.new()
	label.name = "RegionNamePlateText"
	label.text = WorldPresentation.region_label(canonical)
	label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	label.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	label.mouse_filter = Control.MOUSE_FILTER_IGNORE
	label.add_theme_color_override("font_color", REGION_NAME_PLATE_INK)
	label.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	plate.add_child(label)
	_layout_region_name_plate(plate)
	return plate


func _region_name_plate_label(plate: Control) -> Label:
	if plate == null:
		return null
	for child: Node in plate.get_children():
		if child is Label:
			return child as Label
	return null


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
	var font: Font = ThemeDB.fallback_font
	if font == null:
		return Vector2(8.0, 8.0)
	var text_size := font.get_string_size(
		text, HORIZONTAL_ALIGNMENT_LEFT, -1.0, font_size
	)
	return Vector2(
		text_size.x + REGION_NAME_PLATE_PAD.x * 2.0,
		text_size.y + REGION_NAME_PLATE_PAD.y * 2.0,
	)


func _layout_region_name_plate(plate: Control) -> void:
	var label := _region_name_plate_label(plate)
	var text := label.text if label != null else ""
	var max_size := _region_name_plate_max_size()
	var font_size := _region_label_font_size_for_text(text)
	if label != null:
		label.add_theme_font_size_override("font_size", font_size)
	var content := _measure_region_name_plate(text, font_size)
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
	# Text label uses full-rect anchors; only the plate carrier is positioned.
	# Label can reapply content min after font notifications; re-clamp on the
	# next idle frame with the latest band (schedule again after each clamp).
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
	# G101.1a: crest TextureRect per owner_kind (not a solid ColorRect square).
	var mark := TextureRect.new()
	mark.name = OWNERSHIP_MARK_NAME
	mark.texture = _owner_mark_texture(owner)
	mark.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	mark.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	mark.mouse_filter = Control.MOUSE_FILTER_IGNORE
	mark.size = _ownership_mark_size()
	mark.position = _ownership_mark_position()
	# Public meta so probes can read owner without scraping paint carriers.
	mark.set_meta("owner_kind", _owner_kind(owner))
	tile.add_child(mark)


func _owner_mark_texture(owner: Variant) -> Texture2D:
	# Single table keyed by public owner_kind (player / neutral / ai).
	var by_kind := {
		"player": OWNER_MARK_PLAYER_TEXTURE,
		"ai": OWNER_MARK_AI_TEXTURE,
		"neutral": OWNER_MARK_NEUTRAL_TEXTURE,
	}
	return by_kind.get(_owner_kind(owner), OWNER_MARK_NEUTRAL_TEXTURE)


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
	# Labels only; crest textures come from the same table as OwnershipMark.
	return [
		{"kind": "player", "label": "Gracz"},
		{"kind": "neutral", "label": "Neutralny"},
		{"kind": "ai", "label": "Wróg"},
	]


func _refresh_owner_legend() -> void:
	_remove_owner_legend()
	if _rendered_regions.is_empty():
		return
	var legend := Control.new()
	legend.name = OWNER_LEGEND_NAME
	legend.mouse_filter = Control.MOUSE_FILTER_IGNORE
	# Outside tile AABBs: bottom-left of MapView with a small padding.
	var row_h := maxf(16.0, 14.0 * _layout_scale)
	var crest := maxf(12.0, 12.0 * _layout_scale)
	var rows: Array = _owner_legend_rows()
	var legend_w := maxf(108.0, 100.0 * _layout_scale)
	var legend_h := row_h * float(rows.size()) + 6.0
	legend.size = Vector2(legend_w, legend_h)
	legend.position = Vector2(4.0, maxf(4.0, size.y - legend_h - 4.0))
	# Light parchment panel (map theater), not a dark HUD slab.
	var style := StyleBoxFlat.new()
	style.bg_color = Color(0.86, 0.78, 0.62, 0.88)
	style.border_color = Color(0.42, 0.30, 0.18, 0.85)
	style.set_border_width_all(1)
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
		var y := 4.0 + float(index) * row_h
		_add_owner_legend_row(legend, row, y, crest, row_h, legend_w)
	add_child(legend)


func _add_owner_legend_row(
	legend: Control,
	row: Dictionary,
	y: float,
	crest: float,
	row_h: float,
	legend_w: float
) -> void:
	# Same crest asset as OwnershipMark on tiles (G101.1b).
	var kind := str(row["kind"])
	var chip := TextureRect.new()
	chip.name = "OwnerLegendSwatch_%s" % kind
	chip.texture = _owner_mark_texture(kind)
	chip.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	chip.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	chip.position = Vector2(6.0, y + (row_h - crest) * 0.5)
	chip.size = Vector2(crest, crest)
	chip.mouse_filter = Control.MOUSE_FILTER_IGNORE
	chip.set_meta("owner_kind", kind)
	legend.add_child(chip)
	var label := Label.new()
	label.name = "OwnerLegendLabel_%s" % kind
	label.text = str(row["label"])
	label.position = Vector2(6.0 + crest + 6.0, y)
	label.size = Vector2(legend_w - crest - 18.0, row_h)
	label.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	label.mouse_filter = Control.MOUSE_FILTER_IGNORE
	label.add_theme_color_override("font_color", Color(0.18, 0.14, 0.10))
	label.add_theme_font_size_override(
		"font_size", maxi(10, roundi(10.0 * _layout_scale))
	)
	legend.add_child(label)


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
			elif layer.name == REGION_NAME_PLATE_NAME and layer is Control:
				# Font size + geometry live in _layout_region_name_plate only.
				_layout_region_name_plate(layer as Control)
			elif layer is Label and (layer as Label).visible:
				(layer as Label).add_theme_font_size_override(
					"font_size", _region_label_font_size()
				)
	# Theater + legend follow the fitted strip after panel resize.
	_refresh_map_theater_frame()
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
	# Soft ground tint only; crest identity uses OWNER_MARK_* textures.
	match _owner_kind(owner):
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
