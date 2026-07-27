class_name BridgeConfig
extends RefCounted


const DEFAULT_INTERPRETER := "python3"
const DEFAULT_STATE_FILE := "bridge_state.jsonl"
const DEFAULT_SAVE_FILE := "party_save.json"
const DEFAULT_SEED := 0


static func default_values() -> Dictionary:
	return {
		"command": _default_command(),
		"state_path": ProjectSettings.globalize_path("user://".path_join(DEFAULT_STATE_FILE)),
		"save_path": ProjectSettings.globalize_path("user://".path_join(DEFAULT_SAVE_FILE)),
		"seed": DEFAULT_SEED,
	}


static func _default_command() -> String:
	return "PYTHONPATH=%s %s -m tbbbridge" % [
		_shell_quote(_source_directory()),
		DEFAULT_INTERPRETER,
	]


static func _source_directory() -> String:
	var executable_directory := OS.get_executable_path().get_base_dir()
	var source_tree_directory := (
		ProjectSettings.globalize_path("res://").path_join("../src").simplify_path()
	)
	return resolve_source_directory([
		executable_directory.path_join("src"),
		source_tree_directory,
	])


static func resolve_source_directory(candidates: Array) -> String:
	for candidate in candidates:
		if DirAccess.dir_exists_absolute(String(candidate)):
			return String(candidate)
	return ""


static func _shell_quote(value: String) -> String:
	return "'%s'" % value.replace("'", "'\\''")


static func from_values(
	command: String, state_path: String, seed_text: String, save_path: String = ""
) -> Variant:
	var trimmed_command := command.strip_edges()
	var trimmed_state_path := state_path.strip_edges()
	var trimmed_save_path := save_path.strip_edges()
	if trimmed_save_path.is_empty():
		trimmed_save_path = default_values()["save_path"]
	if not seed_text.is_valid_int():
		return null

	var config := {
		"command": trimmed_command,
		"state_path": trimmed_state_path,
		"save_path": trimmed_save_path,
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
		and config.get("save_path") is String
		and not (config["save_path"] as String).strip_edges().is_empty()
		and config.get("seed") is int
	)


static func _environment_text_or_default(variable: String, fallback: String) -> String:
	var value := OS.get_environment(variable).strip_edges()
	return fallback if value.is_empty() else value


static func _environment_seed_or_default(variable: String, fallback: int) -> int:
	var seed_text := OS.get_environment(variable).strip_edges()
	return seed_text.to_int() if seed_text.is_valid_int() else fallback


static func from_environment() -> Dictionary:
	var defaults := default_values()
	var command := _environment_text_or_default("TBB_BRIDGE_COMMAND", defaults["command"])
	var state_path := _environment_text_or_default("TBB_STATE_PATH", defaults["state_path"])
	var save_path := _environment_text_or_default("TBB_SAVE_PATH", defaults["save_path"])
	var seed: int = _environment_seed_or_default("TBB_SEED", defaults["seed"])
	return {
		"command": command,
		"state_path": state_path,
		"save_path": save_path,
		"seed": seed,
	}
