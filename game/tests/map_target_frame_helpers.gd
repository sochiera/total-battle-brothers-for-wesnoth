extends RefCounted


## Shared observation helpers for map_target_frame.png carriers.
## Used by map_view_probe and legal_targeted_move_e2e_probe so both tests share
## one contract: a visible TextureRect/Sprite2D whose texture path ends with
## map_target_frame.png, attributed to a region tile by ancestor or geometry.
## Label→tile walk and node-belongs-to-tile attribution live in PartyMapMark
## so party marks and selection frames cannot drift on MapView hierarchy.

const PartyMapMark = preload("res://tests/party_map_mark_helpers.gd")
const TARGET_FRAME_SUFFIX := "map_target_frame.png"


static func collect_target_frame_nodes(map_view: Node) -> Array:
	var found: Array = []
	_collect_target_frame_nodes_into(map_view, found)
	return found


static func _collect_target_frame_nodes_into(node: Node, found: Array) -> void:
	var path: String = _direct_texture_path(node)
	if path.ends_with(TARGET_FRAME_SUFFIX) and node is CanvasItem:
		if (node as CanvasItem).is_visible_in_tree():
			found.append(node)
	for child: Node in node.get_children():
		_collect_target_frame_nodes_into(child, found)


## Texture path of a TextureRect/Sprite2D only (empty for other nodes).
## Private to this module; map_view_probe keeps its own copy for general layers.
static func _direct_texture_path(node: Node) -> String:
	if node is TextureRect:
		var tr: TextureRect = node as TextureRect
		if tr.texture != null:
			var p: String = tr.texture.resource_path
			return p if not p.is_empty() else "<embedded>"
	if node is Sprite2D:
		var sp: Sprite2D = node as Sprite2D
		if sp.texture != null:
			var p2: String = sp.texture.resource_path
			return p2 if not p2.is_empty() else "<embedded>"
	return ""


## Public path reader for frame overlays that already know they inspect frames.
static func direct_texture_path(node: Node) -> String:
	return _direct_texture_path(node)


## Frame attribution: shared rule with party markers (ancestor / Control center
## / Node2D position). Thin alias so map_view_probe call sites stay frame-named.
static func frame_belongs_to_tile(frame: Node, tile: Control) -> bool:
	return PartyMapMark.node_belongs_to_tile(frame, tile)


static func count_target_frames(map_view: Node) -> int:
	return collect_target_frame_nodes(map_view).size()


static func framed_regions(map_view: Node, names: Array[String]) -> Array:
	var frames: Array = collect_target_frame_nodes(map_view)
	var framed: Array = []
	for region_name: String in names:
		# Prefer RegionTile_<canonical> so Polish RegionNamePlate text is not
		# mistaken for the order/selection identity used by e2e contracts.
		var tile: Control = PartyMapMark.find_region_tile(map_view, region_name)
		if tile == null:
			var label: Label = PartyMapMark.find_label_with_text(map_view, region_name)
			if label == null:
				continue
			tile = PartyMapMark.tile_control(label, map_view)
		if tile == null:
			continue
		for frame: Node in frames:
			if not (frame is CanvasItem):
				continue
			if not (frame as CanvasItem).is_visible_in_tree():
				continue
			if frame_belongs_to_tile(frame, tile):
				if not framed.has(region_name):
					framed.append(region_name)
				break
	return framed
