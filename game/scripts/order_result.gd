class_name OrderResult
extends RefCounted

const MOVE_CHANGED_STATUS := "Oddział przemieścił się."
const MOVE_UNCHANGED_STATUS := "Ruch nie nastąpił."


static func failure_status_text() -> String:
	return "Rozkaz nie powiódł się."


static func _move_status_text(changed: bool) -> String:
	return MOVE_CHANGED_STATUS if changed else MOVE_UNCHANGED_STATUS


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
	if order_result.has("kind"):
		if order_result["kind"] != "battle" or (order != "assault" and order != "engage"):
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

	var order_name := ""
	match order:
		"develop":
			order_name = "rozwoju"
		"recruit":
			order_name = "rekrutacji"
		"muster":
			order_name = "zbiórki"
		"march":
			order_name = "marszu"
		"assault":
			order_name = "szturmu"
		"engage":
			order_name = "starcia"
		_:
			return ""

	var change_text := "zmienił stan." if changed else "nie zmienił stanu."
	return "Rozkaz %s %s" % [order_name, change_text]


static func from_response(response: Dictionary) -> Variant:
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

	match result["kind"]:
		"order":
			if not result.has("changed"):
				return null

			var changed: Variant = result["changed"]
			if not changed is bool:
				return null
			var projected = {"order": order, "changed": changed}
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
