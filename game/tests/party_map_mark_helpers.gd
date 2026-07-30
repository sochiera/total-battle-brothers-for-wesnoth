extends RefCounted


## Shared observation helpers for G84.1c player-party map marks.
## Used by map_view_probe and persistent_party_map_mark_probe so both tests
## share one contract: a visible Control named PlayerPartyMarker that marks a
## region tile either by parenting (tile is ancestor) or by geometry (marker
## center lies in the tile's global rect). Hierarchy is not forced.


static func count_party_markers(map_view: Node) -> int:
	var count := 0
	for marker: Node in find_all_named(map_view, "PlayerPartyMarker"):
		if marker is CanvasItem and (marker as CanvasItem).is_visible_in_tree():
			count += 1
	return count


## True when a visible PlayerPartyMarker carries a non-null Texture2D
## (TextureRect / Sprite2D on the marker or a descendant). ColorRect-only marks fail.
static func marker_has_texture(map_view: Node) -> bool:
	for marker: Node in find_all_named(map_view, "PlayerPartyMarker"):
		if not (marker is CanvasItem):
			continue
		if not (marker as CanvasItem).is_visible_in_tree():
			continue
		if _node_tree_has_texture(marker):
			return true
	return false


static func _node_tree_has_texture(node: Node) -> bool:
	if node is TextureRect and (node as TextureRect).texture != null:
		return true
	if node is Sprite2D and (node as Sprite2D).texture != null:
		return true
	for child: Node in node.get_children():
		if _node_tree_has_texture(child):
			return true
	return false


static func marked_party_regions(map_view: Node, expected_names: Array[String]) -> Array:
	var marked: Array = []
	var markers: Array = find_all_named(map_view, "PlayerPartyMarker")
	for region_name: String in expected_names:
		var label: Label = find_label_with_text(map_view, region_name)
		if label == null:
			continue
		var tile: Control = tile_control(label, map_view)
		for marker: Node in markers:
			if not (marker is CanvasItem):
				continue
			var item: CanvasItem = marker as CanvasItem
			if not item.is_visible_in_tree():
				continue
			if marker_belongs_to_tile(marker, tile):
				if not marked.has(region_name):
					marked.append(region_name)
				break
	return marked


## Node marks a tile when either:
## - the tile is an ancestor of the node (current MapView: under tile), or
## - the node is a Control whose global center lies inside the tile rect
##   (valid alternative: MapView child positioned over the tile), or
## - the node is a Node2D whose global position lies inside the tile rect
##   (Sprite2D selection frames / alternate marker carriers).
## Geometry alone is intentional for hierarchy-agnostic observation.
## Used by party markers and map_target_frame attribution.
static func node_belongs_to_tile(node: Node, tile: Control) -> bool:
	var walk: Node = node
	while walk != null:
		if walk == tile:
			return true
		walk = walk.get_parent()
	if node is Control:
		var rect: Rect2 = (node as Control).get_global_rect()
		var center: Vector2 = rect.position + rect.size * 0.5
		return tile.get_global_rect().has_point(center)
	if node is Node2D:
		return tile.get_global_rect().has_point((node as Node2D).global_position)
	return false


static func marker_belongs_to_tile(marker: Node, tile: Control) -> bool:
	return node_belongs_to_tile(marker, tile)


static func tile_control(label: Label, map_view: Node) -> Control:
	var parent: Node = label.get_parent()
	if parent is Control and parent != map_view:
		return parent as Control
	return label


static func find_label_with_text(root: Node, text: String) -> Label:
	if root is Label and (root as Label).text == text:
		return root as Label
	for child: Node in root.get_children():
		var found: Label = find_label_with_text(child, text)
		if found != null:
			return found
	return null


static func find_all_named(root: Node, node_name: String) -> Array:
	var found: Array = []
	if root.name == node_name:
		found.append(root)
	for child: Node in root.get_children():
		found.append_array(find_all_named(child, node_name))
	return found


## Collect region display names from MapView RegionTile_* controls.
## Recursive on descendants so a nested tile layout still works; label→tile
## attribution for markers/frames uses find_label_with_text/tile_control and
## stays hierarchy-agnostic for known names.
static func region_names_from_map(map_view: Node) -> Array[String]:
	var names: Array[String] = []
	for tile: Node in _region_tile_nodes(map_view):
		for nested: Node in tile.get_children():
			if nested is Label:
				var text: String = (nested as Label).text
				if not text.is_empty() and not names.has(text):
					names.append(text)
	return names


static func _region_tile_nodes(root: Node) -> Array:
	var found: Array = []
	if root is Control and str(root.name).begins_with("RegionTile_"):
		found.append(root)
	for child: Node in root.get_children():
		found.append_array(_region_tile_nodes(child))
	return found
