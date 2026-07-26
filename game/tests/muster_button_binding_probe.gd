extends SceneTree


const MAIN_SCENE_PATH := "res://scenes/main.tscn"
const SnapshotModel = preload("res://scripts/snapshot_model.gd")
const PREFIX := "MUSTER_BUTTON_BINDING "


class StubClient extends RefCounted:
	var models: Array[Variant]
	var last_order_results: Array[Variant]
	var last_order_result: Variant
	var orders: Array[String] = []

	func _init(next_models: Array[Variant], next_order_results: Array[Variant]) -> void:
		models = next_models
		last_order_results = next_order_results

	func send_order(order_name: String) -> Variant:
		orders.append(order_name)
		last_order_result = last_order_results.pop_front()
		return models.pop_front()


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
	var button := scene_root.get_node_or_null("MusterButton") as Button
	if button == null:
		_fail("missing MusterButton")
		return

	var before_bind := _controls(scene_root)
	button.emit_signal("pressed")
	var after_unbound_press := _controls(scene_root)
	var client := StubClient.new([
		_model("zebrano oddział"),
		_model("brak oddziału do zebrania"),
	], [
		{"order": "muster", "changed": true},
		{"order": "muster", "changed": false},
	])
	scene_root.bind_client(client)
	scene_root.bind_client(client)
	button.emit_signal("pressed")
	var after_changed_press := _controls(scene_root)
	button.emit_signal("pressed")
	var after_unchanged_press := _controls(scene_root)

	print(PREFIX, JSON.stringify({
		"before_bind": before_bind,
		"after_unbound_press": after_unbound_press,
		"orders": client.orders,
		"after_changed_press": after_changed_press,
		"after_unchanged_press": after_unchanged_press,
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
	var region_list := scene_root.get_node("RegionList") as ItemList
	var regions: Array[String] = []
	for index: int in region_list.item_count:
		regions.append(region_list.get_item_text(index))
	return {
		"date": (scene_root.get_node("DateLabel") as Label).text,
		"result": (scene_root.get_node("ResultLabel") as Label).text,
		"regions": regions,
		"duchy_status": (scene_root.get_node("PlayerDuchyStatusLabel") as Label).text,
		"order_status": (scene_root.get_node("LastOrderStatusLabel") as Label).text,
	}


func _fail(message: String) -> void:
	printerr("muster_button_binding_probe: ", message)
	call_deferred("quit", 1)
