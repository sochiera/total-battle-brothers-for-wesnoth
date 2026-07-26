extends SceneTree


const SnapshotModel = preload("res://scripts/snapshot_model.gd")


func _party_region(snapshot: Dictionary) -> Variant:
	var model := SnapshotModel.from_response({"ok": true, "snapshot": snapshot})
	return model.player_party_region


func _init() -> void:
	var file := FileAccess.open("res://tests/fixtures/session_snapshot.json", FileAccess.READ)
	var snapshot: Dictionary = JSON.parse_string(file.get_as_text())
	var player_party: Dictionary = snapshot.duplicate(true)
	player_party["map"]["regions"][0]["party"] = {"owner": "player"}
	var missing_player: Dictionary = player_party.duplicate(true)
	missing_player.erase("player_duchy")
	var foreign_party: Dictionary = snapshot.duplicate(true)
	foreign_party["map"]["regions"][1]["party"] = {"owner": "ai"}
	var empty_name: Dictionary = snapshot.duplicate(true)
	empty_name["map"]["regions"][0]["name"] = ""
	empty_name["map"]["regions"][0]["party"] = {"owner": "player"}
	var invalid_player: Dictionary = player_party.duplicate(true)
	invalid_player["player_duchy"] = null
	var invalid_region: Dictionary = snapshot.duplicate(true)
	invalid_region["map"]["regions"] = ["not-a-region"]
	var invalid_party: Dictionary = snapshot.duplicate(true)
	invalid_party["map"]["regions"][0]["party"] = "not-a-party"
	var party_without_owner: Dictionary = snapshot.duplicate(true)
	party_without_owner["map"]["regions"][0]["party"] = {"size": 0}
	print("SNAPSHOT_MODEL_PARTY_REGION_TEST ", JSON.stringify({
		"no_party": _party_region(snapshot),
		"player_party": _party_region(player_party),
		"missing_player": _party_region(missing_player),
		"foreign_party": _party_region(foreign_party),
		"empty_name": _party_region(empty_name),
		"invalid_player": _party_region(invalid_player),
		"invalid_region": _party_region(invalid_region),
		"invalid_party": _party_region(invalid_party),
		"party_without_owner": _party_region(party_without_owner),
	}))
	call_deferred("quit", 0)
