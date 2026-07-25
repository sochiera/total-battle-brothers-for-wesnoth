class_name SnapshotModel
extends RefCounted


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
	var model := preload("res://scripts/snapshot_model.gd").new()
	var calendar: Dictionary = snapshot["calendar"]
	model.year = calendar["year"]
	model.month = calendar["month"]
	model.regions = snapshot["map"]["regions"]
	model.player_result = snapshot["result"]["player_result"]
	return model
