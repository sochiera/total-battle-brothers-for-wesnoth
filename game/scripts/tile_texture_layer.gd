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
