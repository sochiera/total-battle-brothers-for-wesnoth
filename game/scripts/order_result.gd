class_name OrderResult
extends RefCounted

const MOVE_CHANGED_STATUS := "Oddział przemieścił się."
const MOVE_UNCHANGED_STATUS := "Ruch nie nastąpił."
const MONTHLY_ACTION_EXHAUSTED_STATUS := "Oddział już działał w tym miesiącu — zakończ turę."


static func failure_status_text() -> String:
	return "Rozkaz nie powiódł się."


static func _move_status_text(changed: bool) -> String:
	return MOVE_CHANGED_STATUS if changed else MOVE_UNCHANGED_STATUS


static func _is_military_order(order: String) -> bool:
	return order == "assault" or order == "engage"


static func consumes_monthly_action(order_result: Variant) -> bool:
	if not order_result is Dictionary:
		return false
	if not order_result.has("order") or not order_result["order"] is String:
		return false

	var order: String = order_result["order"]
	if order == "move" or order == "march":
		return order_result.get("changed", false) == true
	var is_military_order := _is_military_order(order)
	if not is_military_order:
		return false
	# Battle responses have no changed flag, while ordinary order responses
	# (including their projected form) consume the action when they changed the
	# state.  The missing kind in a projected order is intentional.
	var kind: Variant = order_result.get("kind", "order")
	if kind == "battle":
		return true
	if kind != "order":
		return false
	return order_result.get("changed", false) == true


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


static func _unchanged_status_text(
	order_result: Dictionary, order: String, is_military_order: bool
) -> String:
	if order == "move":
		return _move_status_text(false)
	if is_military_order:
		var exhausted: Variant = order_result.get("monthly_action_exhausted", false)
		if exhausted is bool and exhausted:
			return MONTHLY_ACTION_EXHAUSTED_STATUS

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
	if order == "move":
		return _move_status_text(changed)
	if not changed:
		return _unchanged_status_text(order_result, order, is_military_order)

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
			if monthly_action_exhausted and not changed and is_military_order:
				projected["monthly_action_exhausted"] = true
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
