extends SceneTree

const SnapshotModel = preload("res://scripts/snapshot_model.gd")


func _projection(snapshot: Dictionary) -> Dictionary:
	var model := SnapshotModel.from_response({"ok": true, "snapshot": snapshot})
	return {
		"year": model.year,
		"month": model.month,
		"regions": model.regions,
		"player_result": model.player_result,
		"player_duchy_status": model.player_duchy_status,
	}


func _init() -> void:
	var file := FileAccess.open("res://tests/fixtures/session_snapshot.json", FileAccess.READ)
	var snapshot: Dictionary = JSON.parse_string(file.get_as_text())
	var no_player: Dictionary = snapshot.duplicate(true)
	no_player["player_duchy"] = null
	var no_match: Dictionary = snapshot.duplicate(true)
	no_match["player_duchy"] = "missing"
	var empty_duchies: Dictionary = snapshot.duplicate(true)
	empty_duchies["duchies"] = []
	var missing_duchies: Dictionary = snapshot.duplicate(true)
	missing_duchies.erase("duchies")
	var float_status: Dictionary = snapshot.duplicate(true)
	float_status["duchies"][0]["morale"] = 0.5
	float_status["duchies"][0]["settlements"] = 1.5
	float_status["duchies"][0]["parties"] = 2.5
	var malformed_statuses := {}
	for leaf: String in ["morale", "settlements", "parties"]:
		var missing_leaf: Dictionary = snapshot.duplicate(true)
		missing_leaf["duchies"][0].erase(leaf)
		malformed_statuses["missing_" + leaf] = _projection(missing_leaf)
		var invalid_leaf: Dictionary = snapshot.duplicate(true)
		invalid_leaf["duchies"][0][leaf] = "not-a-number"
		malformed_statuses["invalid_" + leaf] = _projection(invalid_leaf)
	print("SNAPSHOT_MODEL_TEST ", JSON.stringify({
		"matched": _projection(snapshot),
		"no_player": _projection(no_player),
		"no_match": _projection(no_match),
		"empty_duchies": _projection(empty_duchies),
		"missing_duchies": _projection(missing_duchies),
		"float_status": _projection(float_status),
		"malformed_statuses": malformed_statuses,
	}))
	call_deferred("quit", 0)
