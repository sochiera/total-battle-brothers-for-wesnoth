extends SceneTree


## G113.1b e2e: party strength in the „Wybrany region" panel on a live bridge.
## Two measured runs on seed 73 after K117: plain recruit×10 → muster yields a
## 4-unit party, while develop×10 → recruit×10 → muster yields a hero-only
## party with 0 units. The probe drives public Main controls only (order buttons +
## MapView click) and reports the panel text for the party region.
## Scaffolding: map_order_e2e_helpers.gd (shared with the move e2e probes).

const BridgeClient = preload("res://scripts/bridge_client.gd")
const MapOrderE2E = preload("res://tests/map_order_e2e_helpers.gd")
const PREFIX := "PARTY_STRENGTH_E2E "
const VIEWPORT_W := 1152.0
const VIEWPORT_H := 648.0

const PARTY_REGION := "player lands"
const ORDER_REPEATS := 10


func _init() -> void:
	call_deferred("_run")


func _run() -> void:
	var args := OS.get_cmdline_user_args()
	if args.size() != 5:
		_fail("expected command prefix, state path, request path, seed, mode")
		return
	var mode := args[4]
	if mode != "plain" and mode != "developed":
		_fail("unknown mode: %s (expected plain|developed)" % mode)
		return

	root.size = Vector2i(int(VIEWPORT_W), int(VIEWPORT_H))

	var scene_root := MapOrderE2E.instantiate_scene(self, VIEWPORT_W, VIEWPORT_H)
	if scene_root == null:
		return
	await process_frame
	await process_frame

	var client := BridgeClient.create_persistent(args[0], args[1], args[3].to_int(), args[2])
	scene_root.bind_client(client)
	await process_frame
	await process_frame

	var map_view: Node = scene_root.find_child("MapView", true, false)
	if map_view == null:
		_fail("missing MapView")
		return

	if mode == "developed":
		if not await _press_repeated(scene_root, "DevelopButton"):
			return
	if not await _press_repeated(scene_root, "RecruitButton"):
		return
	if not MapOrderE2E.press(self, scene_root, "MusterButton"):
		return
	await process_frame
	await process_frame

	if not MapOrderE2E.click_region(self, map_view, PARTY_REGION):
		return
	await process_frame
	await process_frame
	var after_select: Dictionary = MapOrderE2E.observe(scene_root, map_view)

	print(PREFIX, JSON.stringify({
		"mode": mode,
		"party_region": PARTY_REGION,
		"after_select": after_select,
		"state_exists": FileAccess.file_exists(args[1]),
	}))
	quit(0)


func _press_repeated(scene_root: Control, button_name: String) -> bool:
	for _i in range(ORDER_REPEATS):
		if not MapOrderE2E.press(self, scene_root, button_name):
			return false
		await process_frame
		await process_frame
	return true


func _fail(message: String) -> void:
	printerr("party_strength_e2e_probe: ", message)
	quit(2)
