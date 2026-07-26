extends SceneTree


const BridgeClient = preload("res://scripts/bridge_client.gd")
const PREFIX := "BRIDGE_ORDER "


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
	var order_requests := _request_lines(args[2])
	var resumed := BridgeClient.create_persistent(args[0], args[1], args[3].to_int(), args[2])
	var resumed_model: Variant = resumed.snapshot_model()
	print(PREFIX, JSON.stringify({
		"has_send_order": has_send_order,
		"order": _model_data(order_model),
		"resumed": _model_data(resumed_model),
		"state_exists": FileAccess.file_exists(args[1]),
		"requests": order_requests,
	}))
	call_deferred("quit", 0)
