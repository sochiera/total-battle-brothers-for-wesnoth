extends SceneTree


## Headless probe for G97.1f: MarchButton label and order follow MapView selection.
## Observes public Main scene controls + orders received by a bound stub client.

const MAIN_SCENE_PATH := "res://scenes/main.tscn"
const SnapshotModel = preload("res://scripts/snapshot_model.gd")
const PartyMapMark = preload("res://tests/party_map_mark_helpers.gd")
const PREFIX := "CONTEXTUAL_MARCH_BUTTON "
const VIEWPORT_W := 1152.0
const VIEWPORT_H := 648.0

const REGION_A := "player lands"
const REGION_B := "ai lands"
const REGION_C := "unknown region"
const REGION_A_PL := "Ziemie gracza"
const REGION_B_PL := "Ziemie wroga"
const SETTLEMENT_A := "Player Keep"
const SETTLEMENT_B := "AI Keep"
const DEFAULT_LABEL := "Wyrusz w pole"
const MARCH_ICON_RES := "res://assets/icon_march.png"


class RecordingClient extends RefCounted:
	## Records every send_order(order, target) call. Optional target matches
	## BridgeClient.send_order public arity so a half-wired Main that still
	## calls one-arg send_order stays collectable.
	var calls: Array = []
	var _model: SnapshotModel

	func _init(model: SnapshotModel) -> void:
		_model = model

	func send_order(order_name: String, target: String = "") -> Variant:
		calls.append({"order": order_name, "target": target})
		return _model

	func last_order_result() -> Variant:
		if calls.is_empty():
			return null
		var last: Dictionary = calls[calls.size() - 1]
		return {"order": last.get("order", ""), "changed": true}


func _init() -> void:
	call_deferred("_run")


func _run() -> void:
	root.size = Vector2i(int(VIEWPORT_W), int(VIEWPORT_H))

	var scene: PackedScene = ResourceLoader.load(MAIN_SCENE_PATH) as PackedScene
	if scene == null:
		_fail("cannot load main scene")
		return
	var scene_root: Control = scene.instantiate() as Control
	if scene_root == null:
		_fail("cannot instantiate main scene")
		return

	root.add_child(scene_root)
	scene_root.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	scene_root.size = Vector2(VIEWPORT_W, VIEWPORT_H)
	await process_frame
	await process_frame

	var button := scene_root.find_child("MarchButton", true, false) as Button
	if button == null:
		_fail("missing MarchButton")
		return
	var party_position := scene_root.find_child(
		"PartyPositionContractLabel", true, false
	) as Label
	var selected_region := scene_root.find_child(
		"SelectedRegionDetailsLabel", true, false
	) as Label
	if party_position == null or selected_region == null:
		_fail("missing world-name presentation labels")
		return

	var map_view: Node = scene_root.find_child("MapView", true, false)
	if map_view == null or not map_view.has_method("render_model"):
		_fail("missing MapView")
		return

	var model := _model()
	var client := RecordingClient.new(model)
	scene_root.bind_client(client)
	scene_root.apply_model(model)
	await process_frame
	await process_frame

	var unbound_label: String = button.text
	var unbound_icon: Dictionary = _icon_info(button)

	# No selection: automatic march without target.
	client.calls.clear()
	button.emit_signal("pressed")
	await process_frame
	var after_no_selection_press: Array = client.calls.duplicate(true)
	var after_no_selection_label: String = button.text
	var after_no_selection_icon: Dictionary = _icon_info(button)

	# Select region A → contextual label; press → targeted move only.
	await _click_region(map_view, REGION_A)
	await process_frame
	await process_frame
	var after_select_a_label: String = button.text
	var after_select_a_panel: String = selected_region.text
	var after_select_a_icon: Dictionary = _icon_info(button)
	client.calls.clear()
	button.emit_signal("pressed")
	await process_frame
	var after_select_a_press: Array = client.calls.duplicate(true)

	# Change selection to B → label and next order target update once.
	await _click_region(map_view, REGION_B)
	await process_frame
	await process_frame
	var after_select_b_label: String = button.text
	var after_select_b_panel: String = selected_region.text
	var after_select_b_icon: Dictionary = _icon_info(button)
	client.calls.clear()
	button.emit_signal("pressed")
	await process_frame
	var after_select_b_press: Array = client.calls.duplicate(true)

	# Unknown region → canonical fallback remains visible and is still the target.
	await _click_region(map_view, REGION_C)
	await process_frame
	await process_frame
	var after_select_c_label: String = button.text
	var after_select_c_panel: String = selected_region.text
	client.calls.clear()
	button.emit_signal("pressed")
	await process_frame
	var after_select_c_press: Array = client.calls.duplicate(true)

	print(PREFIX, JSON.stringify({
		"default_label": DEFAULT_LABEL,
		"region_a": REGION_A,
		"region_b": REGION_B,
		"region_c": REGION_C,
		"region_a_pl": REGION_A_PL,
		"region_b_pl": REGION_B_PL,
		"settlement_a": SETTLEMENT_A,
		"settlement_b": SETTLEMENT_B,
		"party_position": party_position.text,
		"expected_label_a": "Wyrusz: %s" % REGION_A_PL,
		"expected_label_b": "Wyrusz: %s" % REGION_B_PL,
		"march_icon_res": MARCH_ICON_RES,
		"unbound_label": unbound_label,
		"unbound_icon": unbound_icon,
		"after_no_selection_label": after_no_selection_label,
		"after_no_selection_icon": after_no_selection_icon,
		"after_no_selection_press": after_no_selection_press,
		"after_select_a_label": after_select_a_label,
		"after_select_a_panel": after_select_a_panel,
		"after_select_a_icon": after_select_a_icon,
		"after_select_a_press": after_select_a_press,
		"after_select_b_label": after_select_b_label,
		"after_select_b_panel": after_select_b_panel,
		"after_select_b_icon": after_select_b_icon,
		"after_select_b_press": after_select_b_press,
		"after_select_c_label": after_select_c_label,
		"after_select_c_panel": after_select_c_panel,
		"after_select_c_press": after_select_c_press,
	}))
	quit(0)


func _model() -> SnapshotModel:
	var model := SnapshotModel.new()
	model.year = 1
	model.month = 1
	model.player_result = "ongoing"
	model.player_party_region = REGION_A
	model.regions = [
		{
			"name": REGION_A,
			"col": 0,
			"row": 0,
			"owner": "player",
			"settlement": {"name": SETTLEMENT_A},
			"party": {"owner": "player"},
		},
		{
			"name": REGION_B,
			"col": 1,
			"row": 0,
			"owner": "ai",
			"settlement": {"name": SETTLEMENT_B},
			"party": null,
		},
		{
			"name": REGION_C,
			"col": 2,
			"row": 0,
			"owner": null,
			"settlement": null,
			"party": null,
		},
	]
	return model


func _icon_info(button: Button) -> Dictionary:
	if button.icon == null or not (button.icon is Texture2D):
		return {"present": false, "path": "", "w": 0, "h": 0}
	var tex := button.icon as Texture2D
	return {
		"present": true,
		"path": tex.resource_path,
		"w": int(tex.get_width()),
		"h": int(tex.get_height()),
	}


func _click_region(map_view: Node, region_name: String) -> void:
	var tile: Control = _find_region_tile(map_view, region_name)
	if tile == null:
		return
	var center: Vector2 = tile.get_global_rect().get_center()
	var press := InputEventMouseButton.new()
	press.button_index = MOUSE_BUTTON_LEFT
	press.pressed = true
	press.position = center
	press.global_position = center
	var release := InputEventMouseButton.new()
	release.button_index = MOUSE_BUTTON_LEFT
	release.pressed = false
	release.position = center
	release.global_position = center
	var vp: Viewport = tile.get_viewport()
	if vp == null:
		return
	vp.push_input(press)
	vp.push_input(release)


func _find_region_tile(map_view: Node, region_name: String) -> Control:
	var label: Label = PartyMapMark.find_label_with_text(map_view, region_name)
	if label == null:
		return null
	return PartyMapMark.tile_control(label, map_view)


func _fail(message: String) -> void:
	printerr("contextual_march_button_probe: ", message)
	quit(1)
