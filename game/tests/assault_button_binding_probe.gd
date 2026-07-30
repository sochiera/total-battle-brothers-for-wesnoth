extends SceneTree


const MAIN_SCENE_PATH := "res://scenes/main.tscn"
const SnapshotModel = preload("res://scripts/snapshot_model.gd")
const PREFIX := "ASSAULT_BUTTON_BINDING "


class StubClient extends RefCounted:
	var orders: Array[String] = []
	var _last_order_result: Variant

	func send_order(order_name: String, _target: String = "") -> Variant:
		orders.append(order_name)
		_last_order_result = {
			"kind": "battle",
			"order": "assault",
			"outcome": "porażka",
			"attacker_losses": 0,
			"defender_losses": 0,
		}
		return _model()

	func last_order_result() -> Variant:
		return _last_order_result

	func _model() -> SnapshotModel:
		var model := SnapshotModel.new()
		model.year = 1
		model.month = 1
		model.player_result = "ongoing"
		model.regions = [{"name": "Północ"}]
		model.player_duchy_status = {"morale": 2, "settlements": 1, "parties": 1}
		return model


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
	var button := scene_root.find_child("AssaultButton", true, false) as Button
	if button == null:
		_fail("missing AssaultButton")
		return
	var client := StubClient.new()
	scene_root.bind_client(client)
	scene_root.bind_client(client)
	button.emit_signal("pressed")

	print(PREFIX, JSON.stringify({
		"orders": client.orders,
		"date": (scene_root.find_child("DateLabel", true, false) as Label).text,
		"result": (scene_root.find_child("ResultLabel", true, false) as Label).text,
		"regions": _regions(scene_root),
		"duchy_status": (scene_root.find_child("PlayerDuchyStatusLabel", true, false) as Label).text,
		"order_status": (scene_root.find_child("LastOrderStatusLabel", true, false) as Label).text,
	}))
	call_deferred("quit", 0)


func _regions(scene_root: Control) -> Array[String]:
	var region_list := scene_root.find_child("RegionList", true, false) as ItemList
	var regions: Array[String] = []
	for index: int in region_list.item_count:
		regions.append(region_list.get_item_text(index))
	return regions


func _fail(message: String) -> void:
	printerr("assault_button_binding_probe: ", message)
	call_deferred("quit", 1)
