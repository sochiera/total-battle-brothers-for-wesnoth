extends SceneTree


const CONFIG_PATH := "res://scripts/bridge_config.gd"
const PREFIX := "BRIDGE_CONFIG_ENVIRONMENT "


func _init() -> void:
	var result: Variant = null
	if ResourceLoader.exists(CONFIG_PATH):
		var bridge_config = load(CONFIG_PATH)
		if bridge_config.has_method("from_environment"):
			result = bridge_config.from_environment()
	print(PREFIX, JSON.stringify(result))
	call_deferred("quit", 0)
