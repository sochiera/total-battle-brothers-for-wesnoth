extends SceneTree


const MAIN_SCENE_PATH := "res://scenes/main.tscn"
const SnapshotModel = preload("res://scripts/snapshot_model.gd")
const PREFIX := "SEND_ORDER_FROM_BRIDGE "


class StubClient extends RefCounted:
	var model: Variant
	var _last_order_result: Variant
	var orders: Array[String] = []

	func _init(next_model: Variant, next_order_result: Variant) -> void:
		model = next_model
		_last_order_result = next_order_result

	func send_order(order_name: String) -> Variant:
		orders.append(order_name)
		return model

	func last_order_result() -> Variant:
		return _last_order_result


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

	if not scene_root.has_method("send_order_from_bridge"):
		print(PREFIX, JSON.stringify({"available": false}))
		call_deferred("quit", 0)
		return

	var recruited_client := StubClient.new(
		_model(2, 3, "recruited", ["Po rekrutacji"]),
		{"order": "recruit", "changed": true},
	)
	var refreshed: bool = scene_root.send_order_from_bridge(recruited_client, "recruit")
	var after_recruit := _controls(scene_root)

	var failed_client := StubClient.new(null, null)
	var rejected: bool = scene_root.send_order_from_bridge(failed_client, "recruit")
	var after_failure := _controls(scene_root)

	print(PREFIX, JSON.stringify({
		"available": true,
		"refreshed": refreshed,
		"recruit_orders": recruited_client.orders,
		"after_recruit": after_recruit,
		"rejected": rejected,
		"failure_orders": failed_client.orders,
		"after_failure": after_failure,
	}))
	call_deferred("quit", 0)


func _model(year: int, month: int, result: String, names: Array[String]) -> SnapshotModel:
	var model := SnapshotModel.new()
	model.year = year
	model.month = month
	model.player_result = result
	model.regions = []
	for name: String in names:
		model.regions.append({"name": name})
	return model


func _controls(scene_root: Control) -> Dictionary:
	var region_list := scene_root.find_child("RegionList", true, false) as ItemList
	var names: Array[String] = []
	for index: int in region_list.item_count:
		names.append(region_list.get_item_text(index))
	return {
		"date": (scene_root.find_child("DateLabel", true, false) as Label).text,
		"result": (scene_root.find_child("ResultLabel", true, false) as Label).text,
		"regions": names,
		"order_status": (scene_root.find_child("LastOrderStatusLabel", true, false) as Label).text,
	}


func _fail(message: String) -> void:
	printerr("send_order_from_bridge_probe: ", message)
	call_deferred("quit", 1)
