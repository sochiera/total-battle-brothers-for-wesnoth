class_name BridgeConfig
extends RefCounted


const DEFAULT_INTERPRETER := "python3"
const DEFAULT_STATE_FILE := "bridge_state.jsonl"
const DEFAULT_SEED := 0


static func default_values() -> Dictionary:
	return {
		"command": _default_command(),
		"state_path": ProjectSettings.globalize_path("user://".path_join(DEFAULT_STATE_FILE)),
		"seed": DEFAULT_SEED,
	}


static func _default_command() -> String:
	return "PYTHONPATH=%s %s -m tbbbridge" % [
		_shell_quote(_source_directory()),
		DEFAULT_INTERPRETER,
	]


static func _source_directory() -> String:
	return ProjectSettings.globalize_path("res://").path_join("../src").simplify_path()


static func _shell_quote(value: String) -> String:
	return "'%s'" % value.replace("'", "'\\''")


static func from_values(command: String, state_path: String, seed_text: String) -> Variant:
	var trimmed_command := command.strip_edges()
	var trimmed_state_path := state_path.strip_edges()
	if not seed_text.is_valid_int():
		return null

	var config := {
		"command": trimmed_command,
		"state_path": trimmed_state_path,
		"seed": seed_text.to_int(),
	}
	if not is_valid_session_config(config):
		return null
	return config


static func is_valid_session_config(config: Variant) -> bool:
	return (
		config is Dictionary
		and config.get("command") is String
		and not (config["command"] as String).strip_edges().is_empty()
		and config.get("state_path") is String
		and not (config["state_path"] as String).strip_edges().is_empty()
		and config.get("seed") is int
	)


static func from_environment() -> Variant:
	return from_values(
		OS.get_environment("TBB_BRIDGE_COMMAND"),
		OS.get_environment("TBB_STATE_PATH"),
		OS.get_environment("TBB_SEED"),
	)
