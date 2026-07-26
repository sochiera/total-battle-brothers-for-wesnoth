extends SceneTree


const BridgeClientScript = preload("res://scripts/bridge_client.gd")


func _init() -> void:
	var client = BridgeClientScript.new()
	if not client.has_method("session_command"):
		printerr("bridge_persistent_api_probe: missing session_command")
		call_deferred("quit", 1)
		return
	var script: Variant = BridgeClientScript
	if not script.has_method("create_persistent"):
		printerr("bridge_persistent_api_probe: missing create_persistent")
		call_deferred("quit", 1)
		return
	call_deferred("quit", 0)
