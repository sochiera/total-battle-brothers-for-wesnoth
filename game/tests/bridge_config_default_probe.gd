extends SceneTree


const CONFIG_PATH := "res://scripts/bridge_config.gd"
const PREFIX := "BRIDGE_CONFIG_DEFAULT "


func _init() -> void:
	var result := {"available": false}
	var bridge_config = load(CONFIG_PATH)
	if bridge_config.has_method("default_values"):
		var first: Dictionary = bridge_config.default_values()
		var second: Dictionary = bridge_config.default_values()
		var user_directory := ProjectSettings.globalize_path("user://")
		result = {
			"available": true,
			"first": first,
			"second": second,
			"valid": bridge_config.is_valid_session_config(first),
			"user_directory": user_directory,
			"state_file_exists": FileAccess.file_exists(first.get("state_path", "")),
		}
	print(PREFIX, JSON.stringify(result))
	call_deferred("quit", 0)
