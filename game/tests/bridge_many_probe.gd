extends SceneTree


const BridgeClient = preload("res://scripts/bridge_client.gd")
const PREFIX := "BRIDGE_MANY "
const TURN_REQUESTS: Array = [{"type": "next_turn"}, {"type": "next_turn"}]
const ALLOW_EMPTY_OPTION := "--allow-empty"


func _init() -> void:
	var args: PackedStringArray = OS.get_cmdline_user_args()
	if args.is_empty():
		printerr("bridge_many_probe: missing bridge command")
		call_deferred("quit", 2)
		return

	var command := args[0]
	var request_path := args[1] if args.size() > 1 else ""
	var options := args.slice(2)
	var allow_empty := ALLOW_EMPTY_OPTION in options
	var client = BridgeClient.create(command, request_path)

	if "--empty" in options:
		_report({"responses": client.send_many([])})
		return

	if "--single" in options:
		var request := {"type": "snapshot"}
		var response: Variant = client.send(request)
		var responses := client.send_many([request])
		_report({"send": response, "send_many": responses})
		return

	var responses := client.send_many(TURN_REQUESTS)
	if "--corrupt" in options:
		if not responses.is_empty():
			responses.pop_back()
	if not allow_empty and responses.size() != TURN_REQUESTS.size():
		printerr("bridge_many_probe: responses are not complete and ordered")
		call_deferred("quit", 1)
		return

	_report({"responses": responses})


func _report(payload: Dictionary) -> void:
	print(PREFIX, JSON.stringify(payload))
	call_deferred("quit", 0)
