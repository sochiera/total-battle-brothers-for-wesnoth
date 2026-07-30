extends SceneTree


const BridgeClient = preload("res://scripts/bridge_client.gd")
const PREFIX := "BRIDGE_ORDER "
# G92.2a: two keeps × four develops each; first send_order is one of eight, so
# seven more productive develops precede the first no-op probe below.
const REPEATED_DEVELOPS_BEFORE_NO_CHANGE := 7


func _model_data(model: Variant) -> Variant:
	if model == null:
		return null
	return {
		"calendar": {"year": model.year, "month": model.month},
		"regions": model.regions,
		"player_result": model.player_result,
		"player_duchy_status": model.player_duchy_status,
	}


func _request_lines(path: String) -> Array:
	if not FileAccess.file_exists(path):
		return []
	var requests: Array = []
	for line in FileAccess.get_file_as_string(path).split("\n"):
		if not line.is_empty():
			requests.append(JSON.parse_string(line))
	return requests


func _init() -> void:
	var args := OS.get_cmdline_user_args()
	if args.size() != 4:
		printerr("bridge_order_probe: expected command prefix, state path, request path and seed")
		call_deferred("quit", 2)
		return

	var client := BridgeClient.create_persistent(args[0], args[1], args[3].to_int(), args[2])
	var has_send_order := client.has_method("send_order")
	var order_model: Variant = client.call("send_order", "develop") if has_send_order else null
	var has_last_order_result_api := client.has_method("last_order_result")
	var last_order_result: Variant = client.call("last_order_result") if has_last_order_result_api else null
	var order_requests := _request_lines(args[2])
	for _step in REPEATED_DEVELOPS_BEFORE_NO_CHANGE:
		client.send_order("develop")
	var unchanged_model: Variant = client.send_order("develop")
	var unchanged_order_result: Variant = client.call("last_order_result") if has_last_order_result_api else null
	var rejected_model: Variant = client.send_order("nope")
	var rejected_order_result: Variant = client.call("last_order_result") if has_last_order_result_api else null
	var resumed := BridgeClient.create_persistent(args[0], args[1], args[3].to_int(), args[2])
	var resumed_model: Variant = resumed.snapshot_model()
	print(PREFIX, JSON.stringify({
		"has_send_order": has_send_order,
		"order": _model_data(order_model),
		"has_last_order_result_api": has_last_order_result_api,
		"last_order_result": last_order_result,
		"unchanged_order": _model_data(unchanged_model),
		"unchanged_order_result": unchanged_order_result,
		"rejected_order_is_null": rejected_model == null,
		"rejected_order_result": rejected_order_result,
		"resumed": _model_data(resumed_model),
		"state_exists": FileAccess.file_exists(args[1]),
		"requests": order_requests,
	}))
	call_deferred("quit", 0)
