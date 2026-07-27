extends SceneTree


const BridgeClient = preload("res://scripts/bridge_client.gd")


func _init() -> void:
	var args := OS.get_cmdline_user_args()
	if args.size() < 3:
		printerr("bridge_order_failure_probe: expected command, state path and request path")
		call_deferred("quit", 2)
		return

	var options := args.slice(3)
	var non_persistent := "--non-persistent" in options
	var order_name := "unknown" if "--unknown-order" in options else "develop"
	var client = BridgeClient.create(args[0], args[2]) if non_persistent else BridgeClient.create_persistent(args[0], args[1], 73, args[2])
	var model = client.send_order(order_name)
	print("BRIDGE_ORDER_FAILURE ", JSON.stringify({"model_is_null": model == null}))
	call_deferred("quit", 0)
