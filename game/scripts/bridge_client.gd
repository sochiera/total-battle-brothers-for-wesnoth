extends RefCounted
class_name BridgeClient


const SnapshotModel = preload("res://scripts/snapshot_model.gd")
const OrderResult = preload("res://scripts/order_result.gd")


var _command: String
var _request_path: String
var _is_persistent: bool = false
var state_path: String
var seed: int
var _last_order_result: Variant = null


static func create(command: String, request_path: String = "") -> BridgeClient:
	var client = load("res://scripts/bridge_client.gd").new()
	client._command = command
	client._request_path = request_path
	if client._request_path.is_empty():
		client._request_path = ProjectSettings.globalize_path("user://bridge_request.jsonl")
	return client


static func create_persistent(command_prefix: String, state_path: String, seed: int, request_path: String = "") -> BridgeClient:
	var client := create(command_prefix, request_path)
	client._is_persistent = true
	client.state_path = state_path
	client.seed = seed
	return client


func session_command() -> String:
	if not _is_persistent:
		return _command
	if FileAccess.file_exists(state_path):
		return "%s serve --resume %s" % [_command, _shell_quote(state_path)]
	return "%s serve %d" % [_command, seed]


static func _shell_quote(value: String) -> String:
	return "'%s'" % value.replace("'", "'\\''")


static func request_line(command: Dictionary) -> String:
	return JSON.stringify(command)


static func request_lines(commands: Array) -> String:
	if commands.is_empty():
		return ""

	var lines: PackedStringArray = []
	for command in commands:
		var request: Dictionary = command
		lines.append(request_line(request))
	return "\n".join(lines) + "\n"


static func first_response(output: String) -> Variant:
	for line in output.split("\n"):
		var trimmed: String = line.strip_edges()
		if trimmed.is_empty():
			continue

		var parsed: Variant = JSON.parse_string(trimmed)
		return parsed if parsed is Dictionary else null
	return null


static func all_responses(output: String) -> Array:
	var responses: Array = []
	for line in output.split("\n"):
		var trimmed: String = line.strip_edges()
		if trimmed.is_empty():
			continue

		var parsed: Variant = JSON.parse_string(trimmed)
		if not parsed is Dictionary:
			break
		responses.append(parsed)
	return responses


func _run_request_file() -> Variant:
	var output: Array = []
	var shell_command := "%s < %s" % [session_command(), _shell_quote(_request_path)]
	var exit_code := OS.execute("sh", ["-c", shell_command], output, false, false)
	if exit_code != 0 or output.is_empty():
		return null
	return str(output[0])


func send(request: Dictionary) -> Variant:
	var file := FileAccess.open(_request_path, FileAccess.WRITE)
	if file == null:
		return null

	file.store_line(request_line(request))
	file.close()

	var stdout: Variant = _run_request_file()
	if stdout == null:
		return null

	return first_response(str(stdout))


func send_many(requests: Array) -> Array:
	if requests.is_empty():
		return []

	var file := FileAccess.open(_request_path, FileAccess.WRITE)
	if file == null:
		return []

	file.store_string(request_lines(requests))
	file.close()

	var stdout: Variant = _run_request_file()
	if stdout == null:
		return []

	var responses := all_responses(str(stdout))
	return responses if responses.size() == requests.size() else []


func _send_persisted_sequence(command: Dictionary, project_order_result: bool = false) -> SnapshotModel:
	if not _is_persistent:
		return null

	var command_and_save: Array = [
		command,
		{"type": "save", "path": state_path},
	]
	var responses := send_many(command_and_save)
	if responses.size() != command_and_save.size():
		return null
	for response in responses:
		if not response is Dictionary or not response.get("ok", false):
			return null

	var first_response: Dictionary = responses[0]
	if project_order_result:
		_last_order_result = OrderResult.from_response(first_response)
	return SnapshotModel.from_response(first_response)


func advance_turn() -> SnapshotModel:
	return _send_persisted_sequence({"type": "next_turn"})


func send_order(order_name: String) -> SnapshotModel:
	_last_order_result = null
	return _send_persisted_sequence({"type": "order", "order": order_name}, true)


func save_party(path: String) -> SnapshotModel:
	return _send_persisted_sequence({"type": "save", "path": path})


func load_party(path: String) -> SnapshotModel:
	return _send_persisted_sequence({"type": "load", "path": path})


func last_order_result() -> Variant:
	return _last_order_result


func snapshot_model() -> SnapshotModel:
	var response: Variant = send({"type": "snapshot"})
	if response == null or not response is Dictionary:
		return null
	return SnapshotModel.from_response(response)
