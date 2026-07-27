extends SceneTree


const BridgeClient = preload("res://scripts/bridge_client.gd")


func _read_requests(path: String) -> Array:
	var file := FileAccess.open(path, FileAccess.READ)
	if file == null:
		return []
	var requests: Array = []
	while not file.eof_reached():
		var line := file.get_line().strip_edges()
		if line.is_empty():
			continue
		var parsed: Variant = JSON.parse_string(line)
		if parsed is Dictionary:
			requests.append(parsed)
	return requests


func _init() -> void:
	var args := OS.get_cmdline_user_args()
	if args.size() < 4:
		printerr("bridge_persisted_sequence_probe: expected command, state and two request paths")
		call_deferred("quit", 2)
		return

	var advance_client := BridgeClient.create_persistent(args[0], args[1], 73, args[2])
	var order_client := BridgeClient.create_persistent(args[0], args[1], 73, args[3])
	var advance_model = advance_client.advance_turn()
	var order_model = order_client.send_order("develop")
	print("BRIDGE_PERSISTED_SEQUENCE ", JSON.stringify({
		"model_is_null": [advance_model == null, order_model == null],
		"requests": [_read_requests(args[2]), _read_requests(args[3])],
	}))
	call_deferred("quit", 0)
