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
var _last_command_result: Variant = null
var _last_battle_order: String = ""


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


static func _responses_are_ok(responses: Array) -> bool:
	for response in responses:
		if not response is Dictionary or not response.get("ok", false):
			return false
	return true


func _write_requests(requests: Array) -> bool:
	if requests.is_empty():
		return false
	var file := FileAccess.open(_request_path, FileAccess.WRITE)
	if file == null:
		return false
	file.store_string(request_lines(requests))
	file.close()
	return true


func send(request: Dictionary) -> Variant:
	if not _write_requests([request]):
		return null

	var stdout: Variant = _run_request_file()
	if stdout == null:
		return null

	return first_response(str(stdout))


func send_many(requests: Array) -> Array:
	if requests.is_empty():
		return []
	if not _write_requests(requests):
		return []

	var stdout: Variant = _run_request_file()
	if stdout == null:
		return []

	var responses := all_responses(str(stdout))
	return responses if responses.size() == requests.size() else []


func _send_persisted_sequence(
	command: Dictionary,
	project_order_result: bool = false,
) -> SnapshotModel:
	if not _is_persistent:
		return null

	var command_and_save: Array = [
		command,
		{"type": "save", "path": state_path},
	]
	var responses := send_many(command_and_save)
	if responses.size() != command_and_save.size() or not _responses_are_ok(responses):
		return null

	var first_response: Dictionary = responses[0]
	_last_command_result = first_response.get("result")
	var model := SnapshotModel.from_response(first_response)
	var order_result: Variant = null
	if project_order_result:
		order_result = OrderResult.from_response(
			first_response, _party_acted_this_month_from_model(model)
		)
		_last_order_result = order_result
	return model


func advance_turn() -> SnapshotModel:
	return _send_persisted_sequence({"type": "next_turn"})


func start_new_game() -> SnapshotModel:
	_last_order_result = null
	return _send_persisted_sequence({"type": "new_game"})


static func _order_command(order_name: String, target: String) -> Dictionary:
	var command := {"type": "order", "order": order_name}
	if not target.is_empty():
		command["target"] = target
	return command


static func _is_battle_order(order_name: String) -> bool:
	return order_name == "assault" or order_name == "engage"


static func _party_acted_this_month_from_model(model: SnapshotModel) -> bool:
	return (
		model != null
		and model.player_party_acted_this_month is bool
		and model.player_party_acted_this_month
	)


func send_order(order_name: String, target: String = "") -> SnapshotModel:
	_last_order_result = null
	_last_battle_order = order_name if _is_battle_order(order_name) else ""
	return _send_persisted_sequence(_order_command(order_name, target), true)


func battle_advance() -> SnapshotModel:
	return _send_persisted_sequence({"type": "battle_advance"})


func battle_auto() -> SnapshotModel:
	return _send_persisted_sequence({"type": "battle_auto"})


func battle_target(attacker: Dictionary, target: Dictionary) -> SnapshotModel:
	_last_command_result = null
	return _send_persisted_sequence({
		"type": "battle_target",
		"attacker": attacker,
		"target": target,
	})


func save_party(path: String) -> SnapshotModel:
	return _send_persisted_sequence({"type": "save", "path": path})


func load_party(path: String) -> SnapshotModel:
	return _send_persisted_sequence({"type": "load", "path": path})


func last_order_result() -> Variant:
	return _last_order_result


func last_battle_result() -> Variant:
	if (
		_last_battle_order.is_empty()
		or not _last_command_result is Dictionary
		or _last_command_result.get("kind") != "battle"
	):
		return null
	var result: Dictionary = _last_command_result.duplicate()
	result["order"] = _last_battle_order
	result["attacker_losses"] = int(result["attacker_losses"])
	result["defender_losses"] = int(result["defender_losses"])
	return result


func last_battle_target_result() -> Variant:
	if (
		not _last_command_result is Dictionary
		or _last_command_result.get("kind") != "battle_target"
	):
		return null
	return _last_command_result.duplicate()


func snapshot_model() -> SnapshotModel:
	var response: Variant = send({"type": "snapshot"})
	if response == null or not response is Dictionary:
		return null
	var model := SnapshotModel.from_response(response)
	_restore_battle_order_from_pending_state(model)
	return model


func persist_snapshot() -> SnapshotModel:
	return _send_persisted_sequence({"type": "snapshot"})


func _restore_battle_order_from_pending_state(model: SnapshotModel) -> void:
	"""Restore the military order name lost when a persistent client resumes.

	The public snapshot intentionally carries only the battle board.  The
	persistent bridge state still has the pending battle context, whose kind is
	stable enough to distinguish the two player battle orders.
	"""
	if (
		model == null
		or not model.battle is Dictionary
		or model.battle.get("result") != null
		or not _last_battle_order.is_empty()
		or not _is_persistent
		or state_path.is_empty()
		or not FileAccess.file_exists(state_path)
	):
		return

	var file := FileAccess.open(state_path, FileAccess.READ)
	if file == null:
		return
	var persisted: Variant = JSON.parse_string(file.get_as_text())
	file.close()
	if not persisted is Dictionary or not persisted.get("pending_battle") is Dictionary:
		return

	var pending: Dictionary = persisted["pending_battle"]
	match pending.get("kind"):
		"party":
			_last_battle_order = "engage"
		"settlement", "settlement_at":
			_last_battle_order = "assault"
