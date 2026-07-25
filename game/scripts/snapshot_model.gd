class_name SnapshotModel
extends RefCounted


const REQUIRED_SECTIONS := ["calendar", "map", "result"]


var year: int
var month: int
var regions: Array
var player_result: String


static func from_response(response: Dictionary) -> SnapshotModel:
	if not response.get("ok", false):
		return null
	if not response.has("snapshot") or not response["snapshot"] is Dictionary:
		return null

	var snapshot: Dictionary = response["snapshot"]
	for section_name in REQUIRED_SECTIONS:
		if not snapshot.has(section_name) or not snapshot[section_name] is Dictionary:
			return null

	var model := preload("res://scripts/snapshot_model.gd").new()
	var calendar: Dictionary = snapshot["calendar"]
	var map: Dictionary = snapshot["map"]
	var result: Dictionary = snapshot["result"]
	model.year = calendar["year"]
	model.month = calendar["month"]
	model.regions = map["regions"]
	model.player_result = result["player_result"]
	return model
