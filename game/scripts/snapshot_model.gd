class_name SnapshotModel
extends RefCounted


const REQUIRED_SECTIONS := ["calendar", "map", "result"]
const PLAYER_DUCHY_STATUS_LEAVES := ["morale", "settlements", "parties"]
const NUMERIC_TYPES := [TYPE_INT, TYPE_FLOAT]
const REQUIRED_LEAVES := {
	"calendar": {
		"year": NUMERIC_TYPES,
		"month": NUMERIC_TYPES,
	},
	"map": {"regions": [TYPE_ARRAY]},
	"result": {"player_result": [TYPE_STRING]},
}


var year: int
var month: int
var regions: Array
var player_result: String
var player_duchy_status: Variant = null


static func _is_numeric(value: Variant) -> bool:
	return NUMERIC_TYPES.has(typeof(value))


static func _player_duchy_status(snapshot: Dictionary) -> Variant:
	var player_duchy: Variant = snapshot.get("player_duchy")
	var duchies: Variant = snapshot.get("duchies")
	if not player_duchy is String or not duchies is Array:
		return null
	for duchy: Variant in duchies:
		if duchy is Dictionary and duchy.get("id") == player_duchy:
			var status := {}
			for leaf_name in PLAYER_DUCHY_STATUS_LEAVES:
				if not duchy.has(leaf_name) or not _is_numeric(duchy[leaf_name]):
					return null
				status[leaf_name] = duchy[leaf_name]
			return status
	return null


static func from_response(response: Dictionary) -> SnapshotModel:
	if not response.get("ok", false):
		return null
	if not response.has("snapshot") or not response["snapshot"] is Dictionary:
		return null

	var snapshot: Dictionary = response["snapshot"]
	for section_name in REQUIRED_SECTIONS:
		if not snapshot.has(section_name) or not snapshot[section_name] is Dictionary:
			return null
	for section_name in REQUIRED_LEAVES:
		var section: Dictionary = snapshot[section_name]
		var leaves_with_allowed_types: Dictionary = REQUIRED_LEAVES[section_name]
		for leaf_name in leaves_with_allowed_types:
			if not section.has(leaf_name):
				return null
			var allowed_types: Array = leaves_with_allowed_types[leaf_name]
			if not allowed_types.has(typeof(section[leaf_name])):
				return null

	var model := preload("res://scripts/snapshot_model.gd").new()
	var calendar: Dictionary = snapshot["calendar"]
	var map: Dictionary = snapshot["map"]
	var result: Dictionary = snapshot["result"]
	model.year = int(calendar["year"])
	model.month = int(calendar["month"])
	model.regions = map["regions"]
	model.player_result = result["player_result"]
	model.player_duchy_status = _player_duchy_status(snapshot)
	return model
