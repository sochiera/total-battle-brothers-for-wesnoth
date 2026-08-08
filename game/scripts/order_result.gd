class_name OrderResult
extends RefCounted

const WorldPresentation = preload("res://scripts/world_presentation.gd")

const MOVE_CHANGED_STATUS := "Oddział przemieścił się."
const MOVE_UNCHANGED_STATUS := "Ruch nie nastąpił."
const MONTHLY_ACTION_EXHAUSTED_STATUS := "Oddział już działał w tym miesiącu — zakończ turę."
const REINFORCE_CHANGED_STATUS := "Oddział został wzmocniony."
const REINFORCE_UNCHANGED_STATUS := "Wzmocnienie nie zmieniło stanu oddziału."
# Fallback intentionally keys on the bridge's Polish reason strings; AC5 keeps
# the core/bridge contract unchanged, so this is not a mistaken ID lookup.
const POPULATION_REASON_STATUS_PL := {
	"brak wolnej ludności": "Brak wolnych mieszkańców — ludność przybędzie w kolejnej turze.",
	"brak wolnej ludności — osada nie wyżywi przyrostu": "Osada nie wyżywi więcej ludzi — ludność nie przybywa.",
}


static func failure_status_text() -> String:
	return "Rozkaz nie powiódł się."


static func _move_status_text(changed: bool) -> String:
	return MOVE_CHANGED_STATUS if changed else MOVE_UNCHANGED_STATUS


static func _blocked_region_status_text(order_result: Dictionary, order: String) -> String:
	if order != "move" and order != "march":
		return ""
	if not order_result.has("blocked_region") or not order_result["blocked_region"] is String:
		return ""
	var blocked_region: String = order_result["blocked_region"]
	if not WorldPresentation.REGION_PL.has(blocked_region):
		return ""
	return "Droga zablokowana w regionie %s: stoi tam wojsko wroga. Uderz na wojsko wroga." % WorldPresentation.region_label(blocked_region)


static func _is_military_order(order: String) -> bool:
	return order == "assault" or order == "engage"


static func _is_monthly_action_order(order: String) -> bool:
	return _is_military_order(order) or order == "reinforce"


static func _order_name(order: String) -> String:
	match order:
		"develop":
			return "rozwoju"
		"recruit":
			return "rekrutacji"
		"muster":
			return "zbiórki"
		"march":
			return "marszu"
		"assault":
			return "szturmu"
		"engage":
			return "starcia"
		_:
			return ""


static func _monthly_action_was_exhausted(order_result: Dictionary) -> bool:
	var exhausted: Variant = order_result.get("monthly_action_exhausted", false)
	return exhausted is bool and exhausted


static func _population_reason_status_text(order_result: Dictionary, order: String) -> String:
	if order != "develop" and order != "recruit" and order != "muster":
		return ""
	if not order_result.has("reason") or not order_result["reason"] is String:
		return ""
	return POPULATION_REASON_STATUS_PL.get(order_result["reason"], "")


static func _unchanged_status_text(
	order_result: Dictionary, order: String, is_monthly_action_order: bool
) -> String:
	if is_monthly_action_order and _monthly_action_was_exhausted(order_result):
		return MONTHLY_ACTION_EXHAUSTED_STATUS
	if order == "reinforce":
		return REINFORCE_UNCHANGED_STATUS
	var population_reason_status := _population_reason_status_text(order_result, order)
	if not population_reason_status.is_empty():
		return population_reason_status

	var order_name := _order_name(order)
	if order_name.is_empty():
		return ""
	return "Rozkaz %s nie zmienił stanu." % order_name


static func _battle_status_text(
	order: String, outcome: String, attacker_losses: int, defender_losses: int
) -> String:
	var battle_name := "Szturm" if order == "assault" else "Starcie"
	return "%s: %s (straty: %d, wróg: %d)." % [
		battle_name,
		outcome,
		attacker_losses,
		defender_losses,
	]


static func status_text(order_result: Variant) -> String:
	if not order_result is Dictionary:
		return ""
	if not order_result.has("order") or not order_result["order"] is String:
		return ""

	if order_result.has("game_over") and order_result["game_over"] is bool and order_result["game_over"]:
		return "Partia jest zakończona."

	var order: String = order_result["order"]
	var is_military_order := _is_military_order(order)
	var is_monthly_action_order := _is_monthly_action_order(order)
	if order_result.has("kind"):
		if order_result["kind"] != "battle" or not is_military_order:
			return ""
		if not order_result.has("outcome") or not order_result["outcome"] is String:
			return ""
		if not order_result.has("attacker_losses") or not order_result["attacker_losses"] is int:
			return ""
		if not order_result.has("defender_losses") or not order_result["defender_losses"] is int:
			return ""
		var outcome: String = order_result["outcome"]
		var attacker_losses: int = order_result["attacker_losses"]
		var defender_losses: int = order_result["defender_losses"]
		return _battle_status_text(order, outcome, attacker_losses, defender_losses)

	if not order_result.has("changed") or not order_result["changed"] is bool:
		return ""

	var changed: bool = order_result["changed"]
	if not changed:
		var blocked_status := _blocked_region_status_text(order_result, order)
		if not blocked_status.is_empty():
			return blocked_status
		if order == "move":
			return _move_status_text(false)
		return _unchanged_status_text(order_result, order, is_monthly_action_order)
	if order == "move":
		return _move_status_text(true)
	if order == "reinforce":
		return REINFORCE_CHANGED_STATUS

	var order_name := _order_name(order)
	if order_name.is_empty():
		return ""
	return "Rozkaz %s zmienił stan." % order_name


static func from_response(response: Dictionary, monthly_action_exhausted: bool = false) -> Variant:
	if not response.has("ok") or not response["ok"] is bool or response["ok"] != true:
		return null
	if not response.has("result") or not response["result"] is Dictionary:
		return null

	var result: Dictionary = response["result"]
	if not result.has("kind") or not result.has("order"):
		return null
	var order: Variant = result["order"]
	if not order is String:
		return null
	var is_military_order := _is_military_order(order)

	match result["kind"]:
		"order":
			if not result.has("changed"):
				return null

			var changed: Variant = result["changed"]
			if not changed is bool:
				return null
			var projected = {"order": order, "changed": changed}
			if monthly_action_exhausted and not changed and _is_monthly_action_order(order):
				projected["monthly_action_exhausted"] = true
			if result.has("blocked_region") and result["blocked_region"] is String:
				projected["blocked_region"] = result["blocked_region"]
			if result.has("reason") and result["reason"] is String:
				projected["reason"] = result["reason"]
			if result.has("game_over") and result["game_over"] is bool and result["game_over"]:
				projected["game_over"] = true
			return projected
		"battle":
			if not result.has("outcome"):
				return null
			if not result.has("attacker_losses") or not result.has("defender_losses"):
				return null

			var outcome: Variant = result["outcome"]
			var attacker_losses: Variant = result["attacker_losses"]
			var defender_losses: Variant = result["defender_losses"]
			if not outcome is String:
				return null
			if not attacker_losses is int and not attacker_losses is float:
				return null
			if not defender_losses is int and not defender_losses is float:
				return null
			if attacker_losses is float and attacker_losses != floor(attacker_losses):
				return null
			if defender_losses is float and defender_losses != floor(defender_losses):
				return null
			return {
				"kind": "battle",
				"order": order,
				"outcome": outcome,
				"attacker_losses": int(attacker_losses),
				"defender_losses": int(defender_losses),
			}
		_:
			return null
