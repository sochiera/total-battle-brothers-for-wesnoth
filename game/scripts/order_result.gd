class_name OrderResult
extends RefCounted


static func status_text(order_result: Variant) -> String:
	if not order_result is Dictionary:
		return ""
	if not order_result.has("order") or not order_result["order"] is String:
		return ""
	if not order_result.has("changed") or not order_result["changed"] is bool:
		return ""

	var order: String = order_result["order"]
	var changed: bool = order_result["changed"]
	var order_name := ""
	match order:
		"develop":
			order_name = "rozwoju"
		"recruit":
			order_name = "rekrutacji"
		_:
			return ""

	if changed:
		return "Rozkaz %s zmienił stan." % order_name
	return "Rozkaz %s nie zmienił stanu." % order_name


static func from_response(response: Dictionary) -> Variant:
	if not response.has("ok") or not response["ok"] is bool or response["ok"] != true:
		return null
	if not response.has("result") or not response["result"] is Dictionary:
		return null

	var result: Dictionary = response["result"]
	if not result.has("kind") or result["kind"] != "order":
		return null
	if not result.has("order"):
		return null
	if not result.has("changed"):
		return null

	var order: Variant = result["order"]
	var changed: Variant = result["changed"]
	if not order is String or not changed is bool:
		return null
	return {"order": order, "changed": changed}
