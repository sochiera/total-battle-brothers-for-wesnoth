extends SceneTree


const CONFIG_PATH := "res://scripts/bridge_config.gd"
const PREFIX := "BRIDGE_CONFIG_ENVIRONMENT "


func _init() -> void:
	var bridge_config = load(CONFIG_PATH)
	var result: Dictionary = bridge_config.from_environment()
	print(PREFIX, JSON.stringify({
		"config": result,
		"default": bridge_config.default_values(),
		"valid": bridge_config.is_valid_session_config(result),
	}))
	call_deferred("quit", 0)
