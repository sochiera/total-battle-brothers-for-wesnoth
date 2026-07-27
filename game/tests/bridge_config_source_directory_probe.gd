extends SceneTree


## Probe for BridgeConfig.resolve_source_directory(candidates):
## first existing directory wins; empty string when none exist.
## Does not touch env or res:// — candidates arrive as script args.

const CONFIG_PATH := "res://scripts/bridge_config.gd"
const PREFIX := "BRIDGE_CONFIG_SOURCE_DIR "
const METHOD := "resolve_source_directory"


func _init() -> void:
	var args: PackedStringArray = OS.get_cmdline_user_args()
	if args.size() != 3:
		print(PREFIX, JSON.stringify({"error": "expected three paths: missing, present, file"}))
		call_deferred("quit", 1)
		return

	var missing: String = args[0]
	var present: String = args[1]
	var as_file: String = args[2]

	var bridge_config = load(CONFIG_PATH)
	var available: bool = bridge_config.has_method(METHOD)
	var result := {
		"available": available,
		"first_when_present": null,
		"second_when_first_missing": null,
		"none_exist": null,
		"empty_list": null,
		"file_is_not_directory": null,
	}
	if available:
		result["first_when_present"] = bridge_config.call(
			METHOD, [present, missing]
		)
		result["second_when_first_missing"] = bridge_config.call(
			METHOD, [missing, present]
		)
		result["none_exist"] = bridge_config.call(METHOD, [missing, missing + "_also"])
		result["empty_list"] = bridge_config.call(METHOD, [])
		result["file_is_not_directory"] = bridge_config.call(
			METHOD, [as_file, present]
		)
	print(PREFIX, JSON.stringify(result))
	call_deferred("quit", 0)
