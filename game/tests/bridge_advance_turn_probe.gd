extends SceneTree


const BridgeClient = preload("res://scripts/bridge_client.gd")
const PREFIX := "BRIDGE_ADVANCE "
const CORRUPT_OPTION := "--corrupt"


func _model_calendar(model: Variant) -> Variant:
	if model == null:
		return null
	return {"year": model.year, "month": model.month}


func _init() -> void:
	var args := OS.get_cmdline_user_args()
	if args.size() < 4:
		printerr("bridge_advance_turn_probe: expected command prefix, state path, request path and seed")
		call_deferred("quit", 2)
		return

	var client := BridgeClient.create_persistent(args[0], args[1], args[3].to_int(), args[2])
	var first: Variant = client.advance_turn()
	var after_first_snapshot: Variant = client.snapshot_model()
	var resumed := BridgeClient.create_persistent(args[0], args[1], args[3].to_int(), args[2])
	var second: Variant = resumed.advance_turn()
	var after_second_snapshot: Variant = resumed.snapshot_model()
	var payload := {
		"first": _model_calendar(first),
		"after_first_snapshot": _model_calendar(after_first_snapshot),
		"second": _model_calendar(second),
		"after_second_snapshot": _model_calendar(after_second_snapshot),
		"state_exists": FileAccess.file_exists(args[1]),
	}
	if CORRUPT_OPTION in args.slice(4):
		payload["after_second_snapshot"] = null
	if not _is_consistent(payload):
		printerr("bridge_advance_turn_probe: inconsistent advance result")
		call_deferred("quit", 1)
		return

	print(PREFIX, JSON.stringify(payload))
	call_deferred("quit", 0)


func _is_consistent(payload: Dictionary) -> bool:
	return (
		payload["first"] != null
		and payload["first"] == payload["after_first_snapshot"]
		and payload["second"] != null
		and payload["second"] == payload["after_second_snapshot"]
		and payload["state_exists"]
	)
