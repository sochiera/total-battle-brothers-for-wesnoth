extends SceneTree


const MAIN_SCENE_PATH := "res://scenes/main.tscn"
const SnapshotModel = preload("res://scripts/snapshot_model.gd")
const PREFIX := "DEVELOP_BUTTON_BINDING "


class StubClient extends RefCounted:
	var models: Array[Variant]
	var orders: Array[String] = []

	func _init(next_models: Array[Variant]) -> void:
		models = next_models

	func send_order(order_name: String) -> Variant:
		orders.append(order_name)
		if models.is_empty():
			return null
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
	var button := scene_root.get_node_or_null("DevelopButton") as Button
	if button == null:
		_fail("missing DevelopButton")
		return

	var before_bind := _controls(scene_root)
	button.emit_signal("pressed")
	var after_unbound_press := _controls(scene_root)

	var client := StubClient.new([
		_model(4, 2),
		_model(5, 3),
		null,
	])
	scene_root.bind_client(client)
	scene_root.bind_client(client)
	button.emit_signal("pressed")
	var after_first_press := _controls(scene_root)
	button.emit_signal("pressed")
	var after_second_press := _controls(scene_root)
	button.emit_signal("pressed")
	var after_failed_press := _controls(scene_root)

	print(PREFIX, JSON.stringify({
		"before_bind": before_bind,
		"after_unbound_press": after_unbound_press,
		"orders": client.orders,
		"after_first_press": after_first_press,
		"after_second_press": after_second_press,
		"after_failed_press": after_failed_press,
	}))
	call_deferred("quit", 0)


func _model(morale: int, settlements: int) -> SnapshotModel:
	var model := SnapshotModel.new()
	model.year = 1
	model.month = 1
	model.player_duchy_status = {
		"morale": morale,
		"settlements": settlements,
		"parties": 1,
	}
	return model


func _controls(scene_root: Control) -> Dictionary:
	return {
		"date": (scene_root.get_node("DateLabel") as Label).text,
		"duchy_status": (scene_root.get_node("PlayerDuchyStatusLabel") as Label).text,
	}


func _fail(message: String) -> void:
	printerr("develop_button_binding_probe: ", message)
	call_deferred("quit", 1)
