extends SceneTree


## G97.1f e2e: legal targeted move via MapView selection + MarchButton on a
## live bridge. Public Main controls only — party mark, selection frame, panel
## and LastOrderStatusLabel after the JSONL→core→render path. Seed 73:
## muster lands the party on "player lands"; "player outpost" is the legal
## adjacent own settlement used by the bridge-level move gate (G97.1b).
## Scaffolding: map_order_e2e_helpers.gd (shared with blocked_enemy_settlement).

const BridgeClient = preload("res://scripts/bridge_client.gd")
const MapOrderE2E = preload("res://tests/map_order_e2e_helpers.gd")
const PREFIX := "LEGAL_TARGETED_MOVE_E2E "
const VIEWPORT_W := 1152.0
const VIEWPORT_H := 648.0

const SOURCE_REGION := "player lands"
const TARGET_REGION := "player outpost"


func _init() -> void:
	call_deferred("_run")


func _run() -> void:
	var args := OS.get_cmdline_user_args()
	if args.size() != 4:
		_fail("expected command prefix, state path, request path and seed")
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

	if not MapOrderE2E.press(self, scene_root, "MusterButton"):
		return
	await process_frame
	await process_frame
	var after_muster: Dictionary = MapOrderE2E.observe(scene_root, map_view)

	if not MapOrderE2E.click_region(self, map_view, TARGET_REGION):
		return
	await process_frame
	await process_frame
	var after_select: Dictionary = MapOrderE2E.observe(scene_root, map_view)

	if not MapOrderE2E.press(self, scene_root, "MarchButton"):
		return
	await process_frame
	await process_frame
	var after_move: Dictionary = MapOrderE2E.observe(scene_root, map_view)

	print(PREFIX, JSON.stringify({
		"source_region": SOURCE_REGION,
		"target_region": TARGET_REGION,
		"after_muster": after_muster,
		"after_select": after_select,
		"after_move": after_move,
		"state_exists": FileAccess.file_exists(args[1]),
		"session_command": client.session_command(),
	}))
	quit(0)


func _fail(message: String) -> void:
	printerr("legal_targeted_move_e2e_probe: ", message)
	quit(2)
