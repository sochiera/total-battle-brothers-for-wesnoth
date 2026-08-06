extends RefCounted


const NEXT_TURNS_TO_STAGE_LIVE_FRONTIER := 3


## Machine-readable entry condition for the prepared assault probes.
## The scenario may use several passive AI turns, but the assault must never
## rely on that count alone: the player party must be on border and the
## frontier settlement must still have a live garrison.
static func inspect(client) -> Dictionary:
	var model = client.snapshot_model()
	if model == null:
		return {"ready": false, "reason": "snapshot_model unavailable"}

	var border := _region(model, "border")
	var frontier := _region(model, "ai outpost")
	var border_party: Variant = border.get("party")
	var player_party_at_border: bool = (
		model.player_party_region == "border"
		and border_party is Dictionary
		and border_party.get("owner") == "player"
	)
	var frontier_settlement: Variant = frontier.get("settlement")
	var frontier_garrison := 0
	if frontier_settlement is Dictionary:
		frontier_garrison = int(frontier_settlement.get("garrison", 0))
	var ready: bool = player_party_at_border and frontier_garrison > 0
	return {
		"ready": ready,
		"player_party_at_border": player_party_at_border,
		"frontier_garrison": frontier_garrison,
		"frontier_garrison_live": frontier_garrison > 0,
	}


static func _region(model, name: String) -> Dictionary:
	for region: Variant in model.regions:
		if region is Dictionary and region.get("name") == name:
			return region
	return {}
