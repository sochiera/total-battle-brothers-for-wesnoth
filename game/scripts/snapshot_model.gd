class_name SnapshotModel
extends RefCounted


var year: int
var month: int


static func from_response(response: Dictionary) -> SnapshotModel:
	var model := preload("res://scripts/snapshot_model.gd").new()
	var calendar: Dictionary = response["snapshot"]["calendar"]
	model.year = calendar["year"]
	model.month = calendar["month"]
	return model
