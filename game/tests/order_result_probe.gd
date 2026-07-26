extends SceneTree

const OrderResult = preload("res://scripts/order_result.gd")
const EXPECTED := {
	"changed": {"order": "develop", "changed": true},
	"unchanged": {"order": "develop", "changed": false},
	"missing_ok": null,
	"not_ok": null,
	"missing_result": null,
	"turn_result": null,
	"save_result": null,
	"missing_order": null,
	"invalid_order": null,
	"missing_changed": null,
	"invalid_changed": null,
}


func _init() -> void:
	var cases := {
		"changed": {"ok": true, "result": {"kind": "order", "order": "develop", "changed": true}},
		"unchanged": {"ok": true, "result": {"kind": "order", "order": "develop", "changed": false}},
		"missing_ok": {"result": {"kind": "order", "order": "develop", "changed": true}},
		"not_ok": {"ok": false, "result": {"kind": "order", "order": "develop", "changed": true}},
		"missing_result": {"ok": true},
		"turn_result": {"ok": true, "result": {"kind": "turn", "date": {}}},
		"save_result": {"ok": true, "result": {"kind": "save", "path": "state.json"}},
		"missing_order": {"ok": true, "result": {"kind": "order", "changed": true}},
		"invalid_order": {"ok": true, "result": {"kind": "order", "order": 1, "changed": true}},
		"missing_changed": {"ok": true, "result": {"kind": "order", "order": "develop"}},
		"invalid_changed": {"ok": true, "result": {"kind": "order", "order": "develop", "changed": "yes"}},
	}
	var projected: Dictionary = {}
	for name: String in cases:
		projected[name] = OrderResult.from_response(cases[name])
	if projected != EXPECTED:
		printerr("order_result_probe: projection did not match the contract")
		call_deferred("quit", 1)
		return
	print("ORDER_RESULT ", JSON.stringify(projected))
	call_deferred("quit", 0)
