class_name OrderResult
extends RefCounted


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
