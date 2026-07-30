extends SceneTree


## Manual ad-hoc probe for R97.1 optional-target send_order (not an auto-collected
## Godot unit test). Invoked only by tests/test_godot_bridge_client_send_order.py via
## run_godot_script; reports one BRIDGE_ORDER_TARGET JSON line on stdout.

const BridgeClient = preload("res://scripts/bridge_client.gd")
const PREFIX := "BRIDGE_ORDER_TARGET "


func _request_lines(path: String) -> Array:
	if not FileAccess.file_exists(path):
		return []
	var requests: Array = []
	for line in FileAccess.get_file_as_string(path).split("\n"):
		if not line.is_empty():
			requests.append(JSON.parse_string(line))
	return requests


func _send_order_arg_count(client) -> int:
	for info in client.get_method_list():
		if str(info["name"]) == "send_order":
			return (info["args"] as Array).size()
	return 0


func _model_data(model: Variant) -> Variant:
	if model == null:
		return null
	return {
		"calendar": {"year": model.year, "month": model.month},
		"player_party_region": model.player_party_region,
		"player_result": model.player_result,
	}


func _init() -> void:
	var args := OS.get_cmdline_user_args()
	if args.size() != 4:
		printerr("bridge_order_target_probe: expected command prefix, state path, request path and seed")
		call_deferred("quit", 2)
		return

	var target_region := "player outpost"
	var unknown_target := "nowhere-on-map"
	var client := BridgeClient.create_persistent(args[0], args[1], args[3].to_int(), args[2])
	var send_order_args := _send_order_arg_count(client)

	# Setup: muster puts the hero party on the map (default world starts garrisoned).
	client.send_order("muster")

	# Untargeted order must keep the historical JSON shape (no target key).
	var untargeted_model: Variant = client.send_order("develop")
	var untargeted_order_result: Variant = client.last_order_result()
	var untargeted_requests := _request_lines(args[2])

	# Targeted move: optional canonical target on the same public send_order path.
	var move_model: Variant = null
	if send_order_args >= 2:
		move_model = client.call("send_order", "move", target_region)
	else:
		# Defect shape: client has no optional target, so move goes without it.
		move_model = client.send_order("move")
	var move_order_result: Variant = client.last_order_result()
	var move_requests := _request_lines(args[2])

	# Unknown / off-map target: still one public path; domain is no-op (changed false),
	# not a protocol reject — party stays put and the batch still persists.
	var bad_move_model: Variant = null
	if send_order_args >= 2:
		bad_move_model = client.call("send_order", "move", unknown_target)
	else:
		bad_move_model = client.send_order("move")
	var bad_move_order_result: Variant = client.last_order_result()
	var bad_move_requests := _request_lines(args[2])

	var resumed := BridgeClient.create_persistent(args[0], args[1], args[3].to_int(), args[2])
	var resumed_model: Variant = resumed.snapshot_model()

	print(PREFIX, JSON.stringify({
		"send_order_args": send_order_args,
		"untargeted": _model_data(untargeted_model),
		"untargeted_order_result": untargeted_order_result,
		"untargeted_requests": untargeted_requests,
		"move": _model_data(move_model),
		"move_order_result": move_order_result,
		"move_requests": move_requests,
		"unknown_target": unknown_target,
		"bad_move": _model_data(bad_move_model),
		"bad_move_order_result": bad_move_order_result,
		"bad_move_requests": bad_move_requests,
		"resumed": _model_data(resumed_model),
		"state_exists": FileAccess.file_exists(args[1]),
		"target_region": target_region,
	}))
	call_deferred("quit", 0)
