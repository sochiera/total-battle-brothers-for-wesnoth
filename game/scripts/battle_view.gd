extends Control


const SnapshotModel = preload("res://scripts/snapshot_model.gd")
const TileTextureLayer = preload("res://scripts/tile_texture_layer.gd")
const TILE_SIZE := Vector2(96, 56)
const TILE_GAP := Vector2(12, 12)
const ATTACKER_COLOR := Color(0.78, 0.22, 0.16)
const DEFENDER_COLOR := Color(0.16, 0.38, 0.78)
const OTHER_SIDE_COLOR := Color(0.38, 0.38, 0.38)

const TERRAIN_PLAINS := preload("res://assets/terrain_plains.png")
const TERRAIN_FOREST := preload("res://assets/terrain_forest.png")
const TERRAIN_HILLS := preload("res://assets/terrain_hills.png")
const DEFAULT_TERRAIN_TEXTURE := TERRAIN_PLAINS

const SIDE_ATTACKER_TEXTURE := preload("res://assets/side_attacker.png")
const SIDE_DEFENDER_TEXTURE := preload("res://assets/side_defender.png")
const SIDE_SILHOUETTE_MARGIN := Vector2(20, 14)


func render_model(model: SnapshotModel) -> void:
	_clear_view()
	if model == null:
		return

	var battle: Variant = model.battle
	if not battle is Dictionary:
		return

	%BattleResultLabel.text = _result_text(battle.get("result"))
	var hexes: Variant = battle.get("hexes")
	if not hexes is Array:
		return
	_render_hexes(hexes)


func _render_hexes(hexes: Array) -> void:
	for hex: Variant in hexes:
		if hex is Dictionary:
			_add_tile(hex)


func _clear_view() -> void:
	for child: Node in get_children():
		if str(child.name).begins_with("HexTile_"):
			child.free()
	%BattleResultLabel.text = ""


func _add_tile(hex: Dictionary) -> void:
	if not hex.has("q") or not hex.has("r"):
		return

	var q: int = int(hex["q"])
	var r: int = int(hex["r"])
	var tile := Control.new()
	tile.name = "HexTile_%d_%d" % [q, r]
	tile.position = _axial_position(q, r)
	tile.size = TILE_SIZE
	tile.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(tile)

	var ground := TileTextureLayer.full_rect(_terrain_texture(hex.get("terrain")), "Ground")
	ground.modulate = _side_color(hex.get("side"))
	tile.add_child(ground)

	var label := Label.new()
	label.text = str(hex.get("terrain", ""))
	label.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	label.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	label.add_theme_color_override("font_color", Color.WHITE)
	tile.add_child(label)

	var silhouette_texture: Texture2D = _side_silhouette_texture(hex.get("side"))
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


func _axial_position(q: int, r: int) -> Vector2:
	return Vector2(
		float(q) * (TILE_SIZE.x + TILE_GAP.x),
		float(r) * (TILE_SIZE.y + TILE_GAP.y),
	)


func _terrain_texture(terrain: Variant) -> Texture2D:
	match terrain:
		"Plains":
			return TERRAIN_PLAINS
		"Forest":
			return TERRAIN_FOREST
		"Hills":
			return TERRAIN_HILLS
		_:
			return DEFAULT_TERRAIN_TEXTURE


func _side_color(side: Variant) -> Color:
	match side:
		"attacker":
			return ATTACKER_COLOR
		"defender":
			return DEFENDER_COLOR
		_:
			return OTHER_SIDE_COLOR


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
