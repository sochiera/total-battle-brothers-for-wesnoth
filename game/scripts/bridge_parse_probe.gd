extends SceneTree


const BridgeClient = preload("res://scripts/bridge_client.gd")


func _init() -> void:
	var args: PackedStringArray = OS.get_cmdline_user_args()
	if args.is_empty():
		printerr("bridge_parse_probe: missing stdout path")
		call_deferred("quit", 2)
		return

	var path: String = args[0]
	var file: FileAccess = FileAccess.open(path, FileAccess.READ)
	if file == null:
		printerr("bridge_parse_probe: cannot open stdout file: ", path)
		call_deferred("quit", 2)
		return

	var output: String = file.get_as_text()
	file.close()
	print("BRIDGE_PARSE ", JSON.stringify({
		"request": BridgeClient.request_line({"type": "snapshot"}),
		"response": BridgeClient.first_response(output),
	}))
	call_deferred("quit", 0)
