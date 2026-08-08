extends SceneTree


## Headless probe for G116.1e: DevelopButton / RecruitButton / MusterButton
## follow MapView region selection the same way MarchButton does (K97.1f).
## Observes public Main scene controls + orders received by a bound stub client.

const MAIN_SCENE_PATH := "res://scenes/main.tscn"
const SnapshotModel = preload("res://scripts/snapshot_model.gd")
const PartyMapMark = preload("res://tests/party_map_mark_helpers.gd")
const PREFIX := "CONTEXTUAL_ECONOMIC_BUTTON "
const VIEWPORT_W := 1152.0
const VIEWPORT_H := 648.0

const REGION_A := "player lands"
const REGION_B := "player outpost"
const REGION_C := "ai lands"
const SETTLEMENT_A := "Player Keep"
const SETTLEMENT_B := "Player Outpost"
const SETTLEMENT_C := "AI Keep"
const ECONOMIC_BUTTONS := ["DevelopButton", "RecruitButton", "MusterButton"]
const MILITARY_BUTTONS := ["ReinforceButton", "AssaultButton", "EngageButton"]


class RecordingClient extends RefCounted:
	## Records every send_order(order, target) call so the probe can assert both
	## the order name and the target region that Main forwards to the bridge.
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

	var map_view: Node = scene_root.find_child("MapView", true, false)
	if map_view == null or not map_view.has_method("render_model"):
		_fail("missing MapView")
		return
	var selected_region_label := scene_root.find_child(
		"SelectedRegionDetailsLabel", true, false
	) as Label
	if selected_region_label == null:
		_fail("missing SelectedRegionDetailsLabel")
		return

	var buttons: Dictionary = {}
	for button_name: String in ECONOMIC_BUTTONS:
		var button := scene_root.find_child(button_name, true, false) as Button
		if button == null:
			_fail("missing %s" % button_name)
			return
		buttons[button_name] = button
	var military_buttons: Dictionary = {}
	for button_name: String in MILITARY_BUTTONS:
		var button := scene_root.find_child(button_name, true, false) as Button
		if button == null:
			_fail("missing %s" % button_name)
			return
		military_buttons[button_name] = button

	var model := _model()
	var client := RecordingClient.new(model)
	scene_root.bind_client(client)
	scene_root.apply_model(model)
	await process_frame
	await process_frame

	# No selection: every economic order must keep today's contract (empty target).
	var no_selection_calls := _press_all(buttons, ECONOMIC_BUTTONS, client)
	var no_selection_military_calls := _press_all(military_buttons, MILITARY_BUTTONS, client)
	await process_frame
	var no_selection_panel: String = selected_region_label.text

	# Select region A (first player settlement) → target follows selection.
	await _click_region(map_view, REGION_A)
	await process_frame
	await process_frame
	var select_a_panel: String = selected_region_label.text
	var select_a_calls := _press_all(buttons, ECONOMIC_BUTTONS, client)
	var select_a_military_calls := _press_all(military_buttons, MILITARY_BUTTONS, client)
	await process_frame

	# Select region B (second player settlement) → target updates to that region.
	await _click_region(map_view, REGION_B)
	await process_frame
	await process_frame
	var select_b_panel: String = selected_region_label.text
	var select_b_calls := _press_all(buttons, ECONOMIC_BUTTONS, client)
	await process_frame

	# Select region C (foreign, no player settlement) → target still follows
	# selection; the bridge/core decides it is a no-op, not the client.
	await _click_region(map_view, REGION_C)
	await process_frame
	await process_frame
	var select_c_panel: String = selected_region_label.text
	var select_c_calls := _press_all(buttons, ECONOMIC_BUTTONS, client)
	await process_frame

	print(PREFIX, JSON.stringify({
		"region_a": REGION_A,
		"region_b": REGION_B,
		"region_c": REGION_C,
		"settlement_a": SETTLEMENT_A,
		"settlement_b": SETTLEMENT_B,
		"settlement_c": SETTLEMENT_C,
		"viewport": [int(VIEWPORT_W), int(VIEWPORT_H)],
		"no_selection_calls": no_selection_calls,
		"no_selection_military_calls": no_selection_military_calls,
		"no_selection_panel": no_selection_panel,
		"select_a_calls": select_a_calls,
		"select_a_military_calls": select_a_military_calls,
		"select_a_panel": select_a_panel,
		"select_b_calls": select_b_calls,
		"select_b_panel": select_b_panel,
		"select_c_calls": select_c_calls,
		"select_c_panel": select_c_panel,
	}))
	quit(0)


func _press_all(buttons: Dictionary, button_names: Array, client: RecordingClient) -> Array:
	## Press each button once; return the calls recorded during this
	## batch in button-declaration order. Clears the client log first so the
	## batch is isolated from earlier presses.
	client.calls.clear()
	for button_name: String in button_names:
		(buttons[button_name] as Button).emit_signal("pressed")
	return client.calls.duplicate(true)


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
			"settlement": {"name": SETTLEMENT_A, "garrison": 1, "free": 4},
			"party": {"owner": "player"},
		},
		{
			"name": REGION_B,
			"col": 1,
			"row": 0,
			"owner": "player",
			"settlement": {"name": SETTLEMENT_B, "garrison": 1, "free": 4},
			"party": null,
		},
		{
			"name": REGION_C,
			"col": 2,
			"row": 0,
			"owner": "ai",
			"settlement": {"name": SETTLEMENT_C},
			"party": null,
		},
	]
	model.player_duchy_status = {"morale": 3, "settlements": 2, "parties": 1}
	return model


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
	printerr("contextual_economic_button_probe: ", message)
	quit(1)
