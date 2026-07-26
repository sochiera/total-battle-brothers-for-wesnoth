extends SceneTree


const BridgeClientScript = preload("res://scripts/bridge_client.gd")


func _init() -> void:
	var args: PackedStringArray = OS.get_cmdline_user_args()
	if args.is_empty():
		printerr("bridge_model_status_probe: missing bridge command")
		call_deferred("quit", 2)
		return

	var request_path := args[1] if args.size() > 1 else ""
	var client = BridgeClientScript.create(args[0], request_path)
	var model = client.snapshot_model()
	if model == null:
		print("BRIDGE_MODEL_STATUS null")
	else:
		print("BRIDGE_MODEL_STATUS ", JSON.stringify(model.player_duchy_status))
	call_deferred("quit", 0)
