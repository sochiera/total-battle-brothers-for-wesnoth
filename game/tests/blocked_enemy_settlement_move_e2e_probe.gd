extends SceneTree


## G97.1f e2e: blocked targeted move into an adjacent enemy settlement.
## Seed 73 after muster: party on "player lands". Legal steps reach "border"
## (player outpost → border); "ai outpost" is then an adjacent enemy settlement.
## Public Main controls only — party mark, selection frame, panel and
## LastOrderStatusLabel after MapView select → MarchButton → JSONL → core → render.
## Scaffolding: map_order_e2e_helpers.gd (shared with legal_targeted_move_e2e).

const BridgeClient = preload("res://scripts/bridge_client.gd")
const MapOrderE2E = preload("res://tests/map_order_e2e_helpers.gd")
const PREFIX := "BLOCKED_ENEMY_SETTLEMENT_MOVE_E2E "
const VIEWPORT_W := 1152.0
const VIEWPORT_H := 648.0

const SOURCE_START := "player lands"
const STEP_OWN := "player outpost"
const SOURCE_REGION := "border"
const TARGET_REGION := "ai outpost"


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

	# Legal approach: own outpost, then empty border next to the enemy settlement.
	if not await _select_and_march(scene_root, map_view, STEP_OWN):
		return
	var after_step_own: Dictionary = MapOrderE2E.observe(scene_root, map_view)

	if not await _select_and_march(scene_root, map_view, SOURCE_REGION):
		return
	var after_step_border: Dictionary = MapOrderE2E.observe(scene_root, map_view)

	if not MapOrderE2E.click_region(self, map_view, TARGET_REGION):
		return
	await process_frame
	await process_frame
	var after_select: Dictionary = MapOrderE2E.observe(scene_root, map_view)

	if not MapOrderE2E.press(self, scene_root, "MarchButton"):
		return
	await process_frame
	await process_frame
	var after_blocked: Dictionary = MapOrderE2E.observe(scene_root, map_view)

	print(PREFIX, JSON.stringify({
		"source_start": SOURCE_START,
		"step_own": STEP_OWN,
		"source_region": SOURCE_REGION,
		"target_region": TARGET_REGION,
		"after_muster": after_muster,
		"after_step_own": after_step_own,
		"after_step_border": after_step_border,
		"after_select": after_select,
		"after_blocked": after_blocked,
		"state_exists": FileAccess.file_exists(args[1]),
	}))
	quit(0)


func _select_and_march(scene_root: Control, map_view: Node, region_name: String) -> bool:
	if not MapOrderE2E.click_region(self, map_view, region_name):
		return false
	await process_frame
	await process_frame
	if not MapOrderE2E.press(self, scene_root, "MarchButton"):
		return false
	await process_frame
	await process_frame
	return true


func _fail(message: String) -> void:
	printerr("blocked_enemy_settlement_move_e2e_probe: ", message)
	quit(2)
