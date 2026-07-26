extends RefCounted
class_name BridgeClient


var _command: String
var _request_path: String


static func create(command: String, request_path: String = "") -> BridgeClient:
	var client = load("res://scripts/bridge_client.gd").new()
	client._command = command
	client._request_path = request_path
	if client._request_path.is_empty():
		client._request_path = ProjectSettings.globalize_path("user://bridge_request.jsonl")
	return client


static func request_line(command: Dictionary) -> String:
	return JSON.stringify(command)


static func first_response(output: String) -> Variant:
	for line in output.split("\n"):
		var trimmed: String = line.strip_edges()
		if trimmed.is_empty():
			continue

		var parsed: Variant = JSON.parse_string(trimmed)
		return parsed if parsed is Dictionary else null
	return null


func send(request: Dictionary) -> Variant:
	var file := FileAccess.open(_request_path, FileAccess.WRITE)
	if file == null:
		return null

	file.store_line(request_line(request))
	file.close()

	var output: Array = []
	var quoted_request_path := _request_path.replace("'", "'\\''")
	var shell_command := "%s < '%s'" % [_command, quoted_request_path]
	var exit_code := OS.execute("sh", ["-c", shell_command], output, false, false)
	if exit_code != 0 or output.is_empty():
		return null

	return first_response(str(output[0]))
