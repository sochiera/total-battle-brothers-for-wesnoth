extends SceneTree


## Narrow G116.1e integration probe: selected economic orders use the real
## persistent bridge and the resulting model is rendered in Main's panel.

const BridgeClient = preload("res://scripts/bridge_client.gd")
const MapOrderE2E = preload("res://tests/map_order_e2e_helpers.gd")
const PREFIX := "CONTEXTUAL_ECONOMIC_BUTTON_BRIDGE "
const VIEWPORT_W := 1152.0
const VIEWPORT_H := 648.0
const PLAYER_REGION := "player outpost"
const FOREIGN_REGION := "ai outpost"


func _init() -> void:
	call_deferred("_run")


func _run() -> void:
	var args: PackedStringArray = OS.get_cmdline_user_args()
	if args.size() != 4:
		_fail("expected command prefix, state path, request path and seed")
		return

	root.size = Vector2i(int(VIEWPORT_W), int(VIEWPORT_H))
	var scene_root := MapOrderE2E.instantiate_scene(self, VIEWPORT_W, VIEWPORT_H)
	if scene_root == null:
		return
	await process_frame
	await process_frame

	var map_view: Node = scene_root.find_child("MapView", true, false)
	if map_view == null:
		_fail("missing contextual economic controls")
		return

	var client := BridgeClient.create_persistent(args[0], args[1], args[3].to_int(), args[2])
	scene_root.bind_client(client)
	await process_frame
	await process_frame

	if not MapOrderE2E.click_region(self, map_view, PLAYER_REGION):
		return
	await process_frame
	await process_frame
	var targeted_before := MapOrderE2E.observe(scene_root, map_view)
	if not MapOrderE2E.press(self, scene_root, "DevelopButton"):
		return
	await process_frame
	await process_frame
	var targeted_after := MapOrderE2E.observe(scene_root, map_view)
	var targeted_result: Variant = client.last_order_result()

	if not MapOrderE2E.click_region(self, map_view, FOREIGN_REGION):
		return
	await process_frame
	await process_frame
	var foreign_before := MapOrderE2E.observe(scene_root, map_view)
	if not MapOrderE2E.press(self, scene_root, "DevelopButton"):
		return
	await process_frame
	await process_frame
	var foreign_after := MapOrderE2E.observe(scene_root, map_view)
	var foreign_result: Variant = client.last_order_result()

	print(PREFIX, JSON.stringify({
		"target_region": PLAYER_REGION,
		"targeted_panel_before": targeted_before["panel_text"],
		"targeted_panel_after": targeted_after["panel_text"],
		"targeted_result": targeted_result,
		"targeted_status": targeted_after["order_status"],
		"foreign_region": FOREIGN_REGION,
		"foreign_panel_before": foreign_before["panel_text"],
		"foreign_panel_after": foreign_after["panel_text"],
		"foreign_result": foreign_result,
		"foreign_status": foreign_after["order_status"],
	}))
	quit(0)


func _fail(message: String) -> void:
	printerr("contextual_economic_button_bridge_probe: ", message)
	quit(1)
