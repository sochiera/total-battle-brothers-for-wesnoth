extends SceneTree


const MAIN_SCENE_PATH := "res://scenes/main.tscn"
const SnapshotModel = preload("res://scripts/snapshot_model.gd")
const PREFIX := "BIND_CLIENT "


class StubClient extends RefCounted:
	var models: Array[Variant]
	var advance_calls := 0

	func _init(next_models: Array[Variant]) -> void:
		models = next_models

	func advance_turn() -> Variant:
		advance_calls += 1
		if models.is_empty():
			return null
		return models.pop_front()


func _init() -> void:
	if "--force-failure" in OS.get_cmdline_user_args():
		_fail("forced failure")
		return

	var scene := ResourceLoader.load(MAIN_SCENE_PATH) as PackedScene
	if scene == null:
		_fail("cannot load main scene")
		return
	var scene_root := scene.instantiate() as Control
	if scene_root == null:
		_fail("cannot instantiate main scene")
		return
	root.add_child(scene_root)
	var button := scene_root.find_child("NextTurnButton", true, false) as Button
	if button == null:
		_fail("missing NextTurnButton")
		return

	var before_bind := _controls(scene_root)
	button.emit_signal("pressed")
	var after_unbound_press := _controls(scene_root)

	if not scene_root.has_method("bind_client"):
		print(PREFIX, JSON.stringify({
			"available": false,
			"before_bind": before_bind,
			"after_unbound_press": after_unbound_press,
		}))
		call_deferred("quit", 0)
		return

	var first_client := StubClient.new([
		_model(2, 3, "ongoing", ["Pierwsza"]),
		_model(2, 4, "victory", ["Druga"]),
	])
	scene_root.bind_client(first_client)
	button.emit_signal("pressed")
	var after_first_press := _controls(scene_root)
	button.emit_signal("pressed")
	var after_second_press := _controls(scene_root)

	var second_client := StubClient.new([_model(7, 8, "draw", ["Nowa"]), null])
	scene_root.bind_client(second_client)
	button.emit_signal("pressed")
	var after_rebind_press := _controls(scene_root)
	button.emit_signal("pressed")
	var after_failed_press := _controls(scene_root)

	print(PREFIX, JSON.stringify({
		"available": true,
		"before_bind": before_bind,
		"after_unbound_press": after_unbound_press,
		"first_calls": first_client.advance_calls,
		"after_first_press": after_first_press,
		"after_second_press": after_second_press,
		"second_calls": second_client.advance_calls,
		"after_rebind_press": after_rebind_press,
		"after_failed_press": after_failed_press,
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
	}


func _fail(message: String) -> void:
	printerr("bind_client_probe: ", message)
	call_deferred("quit", 1)
