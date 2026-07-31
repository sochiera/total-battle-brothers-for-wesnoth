class_name LabelTextureCarrier
extends RefCounted

## Single source for textured label-plate carriers used by MapView region name
## plates and BattleView HP badges: stretched TextureRect under a full-rect
## Label; both ignore mouse so tiles keep hover/selection.

static func make(texture: Texture2D, carrier_name: String) -> TextureRect:
	var carrier := TextureRect.new()
	carrier.name = carrier_name
	carrier.texture = texture
	carrier.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	carrier.stretch_mode = TextureRect.STRETCH_SCALE
	carrier.mouse_filter = Control.MOUSE_FILTER_IGNORE
	return carrier


static func attach_label(carrier: Control, label: Label) -> void:
	label.mouse_filter = Control.MOUSE_FILTER_IGNORE
	label.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	carrier.add_child(label)
