extends SceneTree


const SnapshotModel = preload("res://scripts/snapshot_model.gd")


func _battle(snapshot: Dictionary) -> Variant:
	var model := SnapshotModel.from_response({"ok": true, "snapshot": snapshot})
	if model == null:
		return {"model": null}
	# Public contract: SnapshotModel.battle (Object.get tolerates undeclared field → null).
	return model.get("battle")


func _model_alive_without_battle(snapshot: Dictionary) -> bool:
	var model := SnapshotModel.from_response({"ok": true, "snapshot": snapshot})
	return model != null and model.get("battle") == null and model.player_result is String


func _init() -> void:
	var file := FileAccess.open("res://tests/fixtures/session_snapshot.json", FileAccess.READ)
	var snapshot: Dictionary = JSON.parse_string(file.get_as_text())

	var with_battle: Dictionary = snapshot.duplicate(true)
	with_battle["battle"] = {
		"hexes": [
			{"q": 1, "r": 0, "terrain": "Plains", "side": "attacker", "hp": 0, "stunned": true},
			{"q": 2, "r": 0, "terrain": "Plains", "side": "defender", "hp": 15, "stunned": false},
		],
		"result": "defender_win",
	}

	var float_coords: Dictionary = snapshot.duplicate(true)
	float_coords["battle"] = {
		"hexes": [
			{"q": 1.0, "r": 0.0, "terrain": "Forest", "side": "attacker", "hp": 3.0},
		],
		"result": "attacker_win",
	}

	var skips_bad_hexes: Dictionary = snapshot.duplicate(true)
	skips_bad_hexes["battle"] = {
		"hexes": [
			{"q": 1, "r": 0, "terrain": "Plains", "side": "attacker", "hp": 5},
			{"q": "x", "r": 0, "terrain": "Plains", "side": "defender", "hp": 5},
			{"q": 2, "r": 0, "terrain": "Plains", "side": 1, "hp": 5},
			{"q": 2, "r": 0, "terrain": "Plains", "hp": 5},
			{"r": 0, "terrain": "Plains", "side": "defender", "hp": 5},
			{"q": 3, "r": 1, "terrain": "Hills", "side": "defender", "hp": 7},
			"not-a-hex",
		],
		"result": "draw",
	}

	var empty_hexes: Dictionary = snapshot.duplicate(true)
	empty_hexes["battle"] = {"hexes": [], "result": "draw"}

	var missing_result: Dictionary = snapshot.duplicate(true)
	missing_result["battle"] = {
		"hexes": [{"q": 0, "r": 0, "terrain": "Plains", "side": "attacker", "hp": 1}],
	}

	var bad_battle_type: Dictionary = snapshot.duplicate(true)
	bad_battle_type["battle"] = "not-a-dict"

	var missing_hexes: Dictionary = snapshot.duplicate(true)
	missing_hexes["battle"] = {"result": "draw"}

	print("SNAPSHOT_MODEL_BATTLE_TEST ", JSON.stringify({
		"no_battle": _battle(snapshot),
		"with_battle": _battle(with_battle),
		"float_coords": _battle(float_coords),
		"skips_bad_hexes": _battle(skips_bad_hexes),
		"empty_hexes": _battle(empty_hexes),
		"missing_result": _battle(missing_result),
		"bad_battle_type": _battle(bad_battle_type),
		"missing_hexes": _battle(missing_hexes),
		"bad_battle_keeps_model": _model_alive_without_battle(bad_battle_type),
		"missing_hexes_keeps_model": _model_alive_without_battle(missing_hexes),
	}))
	call_deferred("quit", 0)
