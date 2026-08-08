extends RefCounted


const NEXT_TURNS_TO_STAGE_LIVE_FRONTIER := 3
const NEXT_TURNS_AFTER_ENGAGE_TO_STAGE_LIVE_FRONTIER := 2


## Shared live bridge sequence for the prepared assault probes.
## Returns the order results so the persistent e2e can retain its diagnostics;
## the visual capture only needs the success flag and then settles the scene.
static func stage_live_frontier(scene_root: Control) -> Dictionary:
	var client: Variant = scene_root.get("_client")
	var order_results: Array = []
	# Keep the player force ahead of an AI party that now remains in its own
	# settlement after consuming the garrison through reinforcement.
	var sequence: Array[String] = [
		"RecruitButton",
		"RecruitButton",
		"RecruitButton",
		"MusterButton",
		"MarchButton",
	]
	sequence.append_array(
		_array_repeated("NextTurnButton", NEXT_TURNS_TO_STAGE_LIVE_FRONTIER)
	)
	sequence.append("EngageButton")
	sequence.append_array(
		_array_repeated("NextTurnButton", NEXT_TURNS_AFTER_ENGAGE_TO_STAGE_LIVE_FRONTIER)
	)
	for button_name: String in sequence:
		var button := scene_root.find_child(button_name, true, false) as Button
		if button == null or button.disabled:
			return {
				"ok": false,
				"button": button_name,
				"order_results": order_results,
			}
		button.emit_signal("pressed")
		if client != null and client.has_method("last_order_result"):
			order_results.append(client.call("last_order_result"))
	return {"ok": true, "order_results": order_results}


static func _array_repeated(value: String, count: int) -> Array[String]:
	var values: Array[String] = []
	for _index in count:
		values.append(value)
	return values


## Machine-readable entry condition for the prepared assault probes.
## The scenario may use several passive AI turns, but the assault must never
## rely on that count alone: the player party must be on border and the
## frontier settlement must still have live defenders.
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
	var frontier_defenders := frontier_garrison
	var frontier_party: Variant = frontier.get("party")
	if (
		frontier_party is Dictionary
		and frontier_settlement is Dictionary
		and frontier_party.get("owner") == frontier_settlement.get("owner")
	):
		frontier_defenders += 1 + int(frontier_party.get("size", 0))
	var ready: bool = player_party_at_border and frontier_defenders > 0
	return {
		"ready": ready,
		"player_party_at_border": player_party_at_border,
		"frontier_garrison": frontier_garrison,
		"frontier_defenders": frontier_defenders,
		"frontier_defenders_live": frontier_defenders > 0,
	}


static func _region(model, name: String) -> Dictionary:
	for region: Variant in model.regions:
		if region is Dictionary and region.get("name") == name:
			return region
	return {}
