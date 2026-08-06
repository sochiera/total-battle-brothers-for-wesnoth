extends SceneTree


const BridgeClient = preload("res://scripts/bridge_client.gd")
const PREFIX := "BRIDGE_NEW_GAME "


func _calendar(model: Variant) -> Variant:
	if model == null:
		return null
	return {"year": model.year, "month": model.month}


func _is_ongoing(model: Variant) -> Variant:
	if model == null:
		return null
	return model.player_result == "ongoing"


func _parse_jsonl(text: String) -> Array:
	var records: Array = []
	for line in text.split("\n"):
		var trimmed: String = line.strip_edges()
		if trimmed.is_empty():
			continue

		var parsed: Variant = JSON.parse_string(trimmed)
		if not parsed is Dictionary:
			break
		records.append(parsed)
	return records


func _init() -> void:
	var args := OS.get_cmdline_user_args()
	if args.size() < 4:
		printerr("bridge_new_game_probe: expected command prefix, state path, request path and seed")
		call_deferred("quit", 2)
		return

	var client := BridgeClient.create_persistent(args[0], args[1], args[3].to_int(), args[2])
	client.advance_turn()
	client.advance_turn()
	var before: Variant = client.snapshot_model()
	client.send_order("develop")
	var had_order_result := client.last_order_result() != null

	var fresh: Variant = client.start_new_game()
	var request_text := FileAccess.get_file_as_string(args[2])
	var resumed := BridgeClient.create_persistent(args[0], args[1], args[3].to_int(), args[2])
	var resumed_model: Variant = resumed.snapshot_model()
	print(PREFIX, JSON.stringify({
		"before": _calendar(before),
		"fresh": _calendar(fresh),
		"fresh_is_ongoing": _is_ongoing(fresh),
		"had_order_result": had_order_result,
		"last_order_result_is_null": client.last_order_result() == null,
		"resumed": _calendar(resumed_model),
		"resumed_is_ongoing": _is_ongoing(resumed_model),
		"state_exists": FileAccess.file_exists(args[1]),
		"requests": _parse_jsonl(request_text),
	}))
	call_deferred("quit", 0)
