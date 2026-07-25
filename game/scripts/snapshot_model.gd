class_name SnapshotModel
extends RefCounted


var year: int
var month: int
var regions: Array
var player_result: String


static func from_response(response: Dictionary) -> SnapshotModel:
	var model := preload("res://scripts/snapshot_model.gd").new()
	var calendar: Dictionary = response["snapshot"]["calendar"]
	model.year = calendar["year"]
	model.month = calendar["month"]
	model.regions = response["snapshot"]["map"]["regions"]
	model.player_result = response["snapshot"]["result"]["player_result"]
	return model
