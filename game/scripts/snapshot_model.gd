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
	"result": {"player_result": [TYPE_STRING, TYPE_NIL]},
}


var year: int
var month: int
var regions: Array
var player_result: String
var player_duchy_status: Variant = null
var player_party_region: Variant = null
var player_party_acted_this_month: Variant = null
var battle: Variant = null


static func _is_numeric(value: Variant) -> bool:
	return NUMERIC_TYPES.has(typeof(value))


static func _placeable_regions(regions: Array) -> Array:
	var valid_regions: Array = []
	for region: Variant in regions:
		if not region is Dictionary:
			continue
		var name: Variant = region.get("name")
		if not name is String or name.is_empty():
			continue
		if not region.has("col") or not _is_numeric(region["col"]):
			continue
		if not region.has("row") or not _is_numeric(region["row"]):
			continue
		if not region.has("owner") or (region["owner"] != null and not region["owner"] is String):
			continue
		var projected: Dictionary = region.duplicate()
		projected["col"] = int(region["col"])
		projected["row"] = int(region["row"])
		valid_regions.append(projected)
	return valid_regions


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


static func _player_party(snapshot: Dictionary) -> Variant:
	var player_duchy: Variant = snapshot.get("player_duchy")
	var map: Variant = snapshot.get("map")
	if not player_duchy is String or player_duchy.is_empty() or not map is Dictionary:
		return null
	var regions: Variant = map.get("regions")
	if not regions is Array:
		return null
	for region: Variant in regions:
		if not region is Dictionary:
			continue
		var party: Variant = region.get("party")
		if not party is Dictionary or party.get("owner") != player_duchy:
			continue
		return region
	return null


static func _player_party_region(snapshot: Dictionary) -> Variant:
	var region: Variant = _player_party(snapshot)
	if not region is Dictionary:
		return null
	var region_name: Variant = region.get("name")
	return region_name if region_name is String else null


static func _player_party_acted_this_month(snapshot: Dictionary) -> Variant:
	var region: Variant = _player_party(snapshot)
	if not region is Dictionary:
		return null
	var party: Variant = region.get("party")
	if not party is Dictionary:
		return null
	var acted_this_month: Variant = party.get("acted_this_month")
	return acted_this_month if acted_this_month is bool else null


static func _battle(snapshot: Dictionary) -> Variant:
	var battle_snapshot: Variant = snapshot.get("battle")
	if not battle_snapshot is Dictionary:
		return null
	if not battle_snapshot.has("result"):
		return null
	var result: Variant = battle_snapshot["result"]
	if result != null and not result is String:
		return null
	if not battle_snapshot.has("hexes") or not battle_snapshot["hexes"] is Array:
		return null

	var hexes: Array = []
	for hex: Variant in battle_snapshot["hexes"]:
		var projected_hex: Variant = _project_battle_hex(hex, result == null)
		if projected_hex != null:
			hexes.append(projected_hex)
	var battle := {"result": result, "hexes": hexes}
	var projected_targets := _project_attack_targets(battle_snapshot.get("attack_targets"))
	if not projected_targets.is_empty():
		battle["attack_targets"] = projected_targets
	return battle


static func _project_attack_targets(value: Variant) -> Array:
	var projected_targets: Array = []
	if not value is Array:
		return projected_targets
	for pair: Variant in value:
		var projected_pair: Variant = _project_attack_target(pair)
		if projected_pair != null:
			projected_targets.append(projected_pair)
	return projected_targets


static func _project_attack_target(pair: Variant) -> Variant:
	if not pair is Dictionary:
		return null
	var attacker: Variant = _project_battle_coordinates(pair.get("attacker"))
	var target: Variant = _project_battle_coordinates(pair.get("target"))
	if attacker == null or target == null:
		return null
	return {"attacker": attacker, "target": target}


static func _project_battle_coordinates(value: Variant) -> Variant:
	if not value is Dictionary:
		return null
	if not _is_numeric(value.get("q")) or not _is_numeric(value.get("r")):
		return null
	return {"q": int(value["q"]), "r": int(value["r"])}


static func _project_battle_hex(hex: Variant, pending: bool) -> Variant:
	if not hex is Dictionary:
		return null
	if not hex.has("q") or not _is_numeric(hex["q"]):
		return null
	if not hex.has("r") or not _is_numeric(hex["r"]):
		return null
	if not hex.has("side") or not hex["side"] is String:
		return null
	if not hex.has("terrain") or not hex["terrain"] is String:
		return null
	if not hex.has("hp") or not _is_numeric(hex["hp"]):
		return null
	if pending and (not hex.has("stunned") or not hex["stunned"] is bool):
		return null
	var projected := {
		"q": int(hex["q"]),
		"r": int(hex["r"]),
		"terrain": hex["terrain"],
		"side": hex["side"],
		"hp": int(hex["hp"]),
	}
	if pending:
		projected["stunned"] = hex["stunned"]
	return projected


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
	model.regions = _placeable_regions(map["regions"])
	model.player_result = "" if result["player_result"] == null else result["player_result"]
	model.player_duchy_status = _player_duchy_status(snapshot)
	model.player_party_region = _player_party_region(snapshot)
	model.player_party_acted_this_month = _player_party_acted_this_month(snapshot)
	model.battle = _battle(snapshot)
	return model
