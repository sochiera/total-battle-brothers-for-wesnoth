extends SceneTree


const BridgeClient = preload("res://scripts/bridge_client.gd")


func _fail(message: String) -> void:
	printerr("bridge_persistent_probe: ", message)
	call_deferred("quit", 1)


func _init() -> void:
	var args := OS.get_cmdline_user_args()
	if args.size() != 4:
		_fail("expected command prefix, state path, saved state and seed")
		return

	var command_prefix: String = args[0]
	var state_path: String = args[1]
	var saved_state_path: String = args[2]
	var seed: int = args[3].to_int()
	var default_request_path := ProjectSettings.globalize_path("user://bridge_request.jsonl")
	if FileAccess.file_exists(default_request_path):
		DirAccess.remove_absolute(default_request_path)

	var client := BridgeClient.create_persistent(command_prefix, state_path, seed)
	if client.state_path != state_path or client.seed != seed:
		_fail("persistent fields are not observable")
		return
	var fresh_command := client.session_command()
	if fresh_command != "%s serve %d" % [command_prefix, seed]:
		_fail("fresh command is wrong: " + fresh_command)
		return

	var saved_bytes := FileAccess.get_file_as_bytes(saved_state_path)
	var state_file := FileAccess.open(state_path, FileAccess.WRITE)
	if state_file == null:
		_fail("cannot create state file")
		return
	state_file.store_buffer(saved_bytes)
	state_file.close()

	var resumed_command := client.session_command()
	if not resumed_command.contains(" serve --resume ") or not resumed_command.contains("'\\''"):
		_fail("resume command does not quote the state path: " + resumed_command)
		return
	var response: Variant = client.send({"type": "snapshot"})
	if not response is Dictionary or not bool(response.get("ok", false)):
		_fail("resumed command did not execute successfully")
		return
	if not FileAccess.file_exists(default_request_path):
		_fail("persistent client did not use the default request path")
		return
	print("PERSISTENT_BRIDGE ", JSON.stringify({"fresh": fresh_command, "resumed": resumed_command}))
	call_deferred("quit", 0)
