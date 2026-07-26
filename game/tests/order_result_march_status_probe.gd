extends SceneTree

const OrderResult = preload("res://scripts/order_result.gd")

const EXPECTED_STATUS_TEXT := {
	"march_changed": "Rozkaz marszu zmienił stan.",
	"march_unchanged": "Rozkaz marszu nie zmienił stanu.",
	"unknown_order": "",
	"missing_changed": "",
	"invalid_changed": "",
}


func _init() -> void:
	var status_cases: Dictionary = {
		"march_changed": {"order": "march", "changed": true},
		"march_unchanged": {"order": "march", "changed": false},
		"unknown_order": {"order": "trade", "changed": true},
		"missing_changed": {"order": "march"},
		"invalid_changed": {"order": "march", "changed": "yes"},
	}
	var status_text: Dictionary = {}
	for name: String in status_cases:
		status_text[name] = OrderResult.status_text(status_cases[name])
	if status_text != EXPECTED_STATUS_TEXT:
		printerr("order_result_march_status_probe: status text did not match the contract")
		call_deferred("quit", 1)
		return
	print("ORDER_MARCH_STATUS_TEXT ", JSON.stringify(status_text))
	call_deferred("quit", 0)
