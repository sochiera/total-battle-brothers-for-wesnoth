extends SceneTree


const BridgeClientScript = preload("res://scripts/bridge_client.gd")


func _init() -> void:
	var args: PackedStringArray = OS.get_cmdline_user_args()
	if args.is_empty():
		printerr("bridge_call_probe: missing bridge command")
		call_deferred("quit", 2)
		return

	var request_path := args[1] if args.size() > 1 else ""
	var response: Variant = BridgeClientScript.create(args[0], request_path).send({"type": "snapshot"})
	var payload := {
		"is_null": response == null,
		"keys": [],
		"ok": false,
	}
	if response is Dictionary:
		var keys: Array = response.keys()
		keys.sort()
		payload["keys"] = keys
		payload["ok"] = bool(response.get("ok", false))

	print("BRIDGE_CALL ", JSON.stringify(payload))
	call_deferred("quit", 0)
