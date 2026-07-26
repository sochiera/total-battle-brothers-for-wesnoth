extends SceneTree


const CONFIG_PATH := "res://scripts/bridge_config.gd"


func _init() -> void:
	if not ResourceLoader.exists(CONFIG_PATH):
		print("BRIDGE_CONFIG null")
		call_deferred("quit", 0)
		return

	var bridge_config = load(CONFIG_PATH)
	var results := [
		bridge_config.from_values("  python3 -m tbbbridge serve 73  ", "\t/tmp/tbb-state.jsonl ", "73"),
		bridge_config.from_values(" bridge --serve ", "state.jsonl", "-5"),
		bridge_config.from_values(" \t ", "state.jsonl", "7"),
		bridge_config.from_values("bridge", "\n ", "7"),
		bridge_config.from_values("bridge", "state.jsonl", "7.5"),
		bridge_config.from_values("bridge", "state.jsonl", "abc"),
		bridge_config.from_values("bridge", "state.jsonl", ""),
	]
	print("BRIDGE_CONFIG ", JSON.stringify(results))
	call_deferred("quit", 0)
