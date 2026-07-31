extends SceneTree


const MAIN_SCENE_PATH := "res://scenes/main.tscn"
const SnapshotModel = preload("res://scripts/snapshot_model.gd")
const PREFIX := "MARCH_BUTTON_BINDING "


class StubClient extends RefCounted:
	var models: Array[Variant]
	var last_order_results: Array[Variant]
	var _last_order_result: Variant
	var orders: Array[String] = []

	func _init(next_models: Array[Variant], next_order_results: Array[Variant]) -> void:
		models = next_models
		last_order_results = next_order_results

	func send_order(order_name: String, _target: String = "") -> Variant:
		orders.append(order_name)
		_last_order_result = last_order_results.pop_front()
		return models.pop_front()

	func last_order_result() -> Variant:
		return _last_order_result


class FailingClient extends RefCounted:
	var orders: Array[String] = []

	func send_order(order_name: String, _target: String = "") -> Variant:
		orders.append(order_name)
		return null


func _init() -> void:
	var scene := ResourceLoader.load(MAIN_SCENE_PATH) as PackedScene
	if scene == null:
		_fail("cannot load main scene")
		return
	var scene_root := scene.instantiate() as Control
	if scene_root == null:
		_fail("cannot instantiate main scene")
		return
	root.add_child(scene_root)
	var button := scene_root.find_child("MarchButton", true, false) as Button
	if button == null:
		_fail("missing MarchButton")
		return

	var before_bind := _controls(scene_root)
	button.emit_signal("pressed")
	var after_unbound_press := _controls(scene_root)
	var client := StubClient.new([
		_model("ongoing"),
		_model("ongoing"),
	], [
		{"order": "march", "changed": true},
		{"order": "march", "changed": false},
	])
	scene_root.bind_client(client)
	scene_root.bind_client(client)
	button.emit_signal("pressed")
	var after_changed_press := _controls(scene_root)
	button.emit_signal("pressed")
	var after_unchanged_press := _controls(scene_root)
	var failed_client := FailingClient.new()
	scene_root.bind_client(failed_client)
	button.emit_signal("pressed")
	var after_failure_press := _controls(scene_root)

	print(PREFIX, JSON.stringify({
		"before_bind": before_bind,
		"after_unbound_press": after_unbound_press,
		"orders": client.orders,
		"after_changed_press": after_changed_press,
		"after_unchanged_press": after_unchanged_press,
		"failure_orders": failed_client.orders,
		"after_failure_press": after_failure_press,
	}))
	call_deferred("quit", 0)


func _model(result: String) -> SnapshotModel:
	var model := SnapshotModel.new()
	model.year = 3
	model.month = 4
	model.player_result = result
	model.regions = [{"name": "Północ"}]
	model.player_duchy_status = {"morale": 2, "settlements": 3, "parties": 1}
	return model


func _controls(scene_root: Control) -> Dictionary:
	var region_list := scene_root.find_child("RegionList", true, false) as ItemList
	var regions: Array[String] = []
	for index: int in region_list.item_count:
		regions.append(region_list.get_item_text(index))
	return {
		"date": (scene_root.find_child("DateLabel", true, false) as Label).text,
		"result": (scene_root.find_child("ResultContractLabel", true, false) as Label).text,
		"regions": regions,
		"duchy_status": (scene_root.find_child("PlayerDuchyStatusLabel", true, false) as Label).text,
		"order_status": (scene_root.find_child("LastOrderStatusLabel", true, false) as Label).text,
	}


func _fail(message: String) -> void:
	printerr("march_button_binding_probe: ", message)
	call_deferred("quit", 1)
