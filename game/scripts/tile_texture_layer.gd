class_name TileTextureLayer
extends RefCounted

## Single source for the tile ground/body texture layer used by MapView and
## BattleView: stretched to fill its parent, ignores mouse input.

static func stretched(texture: Texture2D) -> TextureRect:
	var rect := TextureRect.new()
	rect.texture = texture
	rect.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	rect.stretch_mode = TextureRect.STRETCH_SCALE
	rect.mouse_filter = Control.MOUSE_FILTER_IGNORE
	return rect


static func full_rect(texture: Texture2D, layer_name: String) -> TextureRect:
	var layer := stretched(texture)
	layer.name = layer_name
	layer.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	return layer


static func native_rect(texture: Texture2D, layer_name: String, container_size: Vector2) -> TextureRect:
	var layer := TextureRect.new()
	layer.name = layer_name
	layer.texture = texture
	layer.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	layer.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	layer.mouse_filter = Control.MOUSE_FILTER_IGNORE
	layer.size = texture.get_size()
	layer.position = (container_size - layer.size) * 0.5
	return layer
