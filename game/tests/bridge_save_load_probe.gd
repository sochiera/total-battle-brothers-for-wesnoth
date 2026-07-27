extends SceneTree


const BridgeClient = preload("res://scripts/bridge_client.gd")
const PREFIX := "BRIDGE_SAVE_LOAD "


func _model_calendar(model: Variant) -> Variant:
	if model == null:
		return null
	return {"year": model.year, "month": model.month}


func _init() -> void:
	var args := OS.get_cmdline_user_args()
	if args.size() < 5:
		printerr(
			"bridge_save_load_probe: expected command prefix, state path, request path, seed and slot path"
		)
		call_deferred("quit", 2)
		return

	var command_prefix: String = args[0]
	var state_path: String = args[1]
	var request_path: String = args[2]
	var seed := args[3].to_int()
	var slot_path: String = args[4]
	var missing_slot := slot_path + ".missing"

	var client := BridgeClient.create_persistent(command_prefix, state_path, seed, request_path)
	var has_save_party := client.has_method("save_party")
	var has_load_party := client.has_method("load_party")
	var saved: Variant = client.call("save_party", slot_path) if has_save_party else null
	var after_save: Variant = client.snapshot_model()
	var advanced: Variant = client.advance_turn()
	var loaded: Variant = client.call("load_party", slot_path) if has_load_party else null
	var missing_load: Variant = client.call("load_party", missing_slot) if has_load_party else "missing-api"
	var after_missing: Variant = client.snapshot_model()
	var resumed := BridgeClient.create_persistent(command_prefix, state_path, seed, request_path)
	var resumed_model: Variant = resumed.snapshot_model()

	var non_persistent := BridgeClient.create(command_prefix, request_path)
	var non_persistent_save: Variant = (
		non_persistent.call("save_party", slot_path) if has_save_party else "missing-api"
	)
	var non_persistent_load: Variant = (
		non_persistent.call("load_party", slot_path) if has_load_party else "missing-api"
	)

	print(PREFIX, JSON.stringify({
		"has_save_party": has_save_party,
		"has_load_party": has_load_party,
		"saved": _model_calendar(saved),
		"after_save": _model_calendar(after_save),
		"advanced": _model_calendar(advanced),
		"loaded": _model_calendar(loaded),
		"missing_load_is_null": missing_load == null,
		"after_missing": _model_calendar(after_missing),
		"resumed": _model_calendar(resumed_model),
		"slot_exists": FileAccess.file_exists(slot_path),
		"non_persistent_save_is_null": non_persistent_save == null,
		"non_persistent_load_is_null": non_persistent_load == null,
	}))
	call_deferred("quit", 0)
