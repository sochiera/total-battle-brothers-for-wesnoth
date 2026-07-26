class_name BridgeConfig
extends RefCounted


static func from_values(command: String, state_path: String, seed_text: String) -> Variant:
	var trimmed_command := command.strip_edges()
	var trimmed_state_path := state_path.strip_edges()
	if trimmed_command.is_empty() or trimmed_state_path.is_empty() or not seed_text.is_valid_int():
		return null

	return {
		"command": trimmed_command,
		"state_path": trimmed_state_path,
		"seed": seed_text.to_int(),
	}


static func from_environment() -> Variant:
	return from_values(
		OS.get_environment("TBB_BRIDGE_COMMAND"),
		OS.get_environment("TBB_STATE_PATH"),
		OS.get_environment("TBB_SEED"),
	)
