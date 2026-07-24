extends SceneTree

const SnapshotModel = preload("res://scripts/snapshot_model.gd")


func _init() -> void:
	var file := FileAccess.open("res://tests/fixtures/session_snapshot.json", FileAccess.READ)
	var snapshot: Dictionary = JSON.parse_string(file.get_as_text())
	var response := {"ok": true, "snapshot": snapshot}

	var model := SnapshotModel.from_response(response)
	var expected_regions: Array = snapshot["map"]["regions"]
	var ok := model.year == 1 and model.month == 1 and model.regions == expected_regions

	call_deferred("quit", 0 if ok else 1)
