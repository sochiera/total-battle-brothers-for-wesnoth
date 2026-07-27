extends SceneTree


const BridgeClient = preload("res://scripts/bridge_client.gd")
const BridgeConfig = preload("res://scripts/bridge_config.gd")
const PREFIX := "BRIDGE_CONFIG_DEFAULT_LIVE "


func _init() -> void:
	var config: Dictionary = BridgeConfig.default_values()
	var first := BridgeClient.create_persistent(
		config["command"], config["state_path"], config["seed"]
	)
	var initial = first.snapshot_model()
	var advanced = first.advance_turn()
	var resumed_client := BridgeClient.create_persistent(
		config["command"], config["state_path"], config["seed"]
	)
	var resumed = resumed_client.snapshot_model()
	if initial == null or advanced == null or resumed == null:
		printerr(
			"bridge_config_default_live_probe: bridge did not return a snapshot: ",
			config["command"]
		)
		call_deferred("quit", 1)
		return

	print(PREFIX, JSON.stringify({
		"initial": {"year": initial.year, "month": initial.month},
		"advanced": {"year": advanced.year, "month": advanced.month},
		"resumed": {"year": resumed.year, "month": resumed.month},
		"state_exists": FileAccess.file_exists(config["state_path"]),
	}))
	call_deferred("quit", 0)
