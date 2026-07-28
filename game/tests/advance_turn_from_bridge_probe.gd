extends SceneTree


const MAIN_SCENE_PATH := "res://scenes/main.tscn"
const SnapshotModel = preload("res://scripts/snapshot_model.gd")
const PREFIX := "ADVANCE_TURN_FROM_BRIDGE "


class StubClient extends RefCounted:
	var advance_model: Variant
	var snapshot: Variant
	var advance_calls := 0
	var snapshot_calls := 0

	func _init(next_model: Variant, snapshot_model: Variant) -> void:
		advance_model = next_model
		snapshot = snapshot_model

	func advance_turn() -> Variant:
		advance_calls += 1
		return advance_model

	func snapshot_model() -> Variant:
		snapshot_calls += 1
		return snapshot


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

	if not scene_root.has_method("advance_turn_from_bridge"):
		print(PREFIX, JSON.stringify({"available": false}))
		call_deferred("quit", 0)
		return

	var after_turn := _model(8, 4, "ongoing", ["Po turze"])
	var stale_snapshot := _model(1, 1, "defeat", ["Przed turą"])
	var successful_client := StubClient.new(after_turn, stale_snapshot)
	var refreshed: bool = scene_root.advance_turn_from_bridge(successful_client)
	var after_success := _controls(scene_root)

	var failed_client := StubClient.new(null, stale_snapshot)
	var rejected: bool = scene_root.advance_turn_from_bridge(failed_client)
	var after_failure := _controls(scene_root)

	print(PREFIX, JSON.stringify({
		"available": true,
		"refreshed": refreshed,
		"success_calls": successful_client.advance_calls,
		"success_snapshot_calls": successful_client.snapshot_calls,
		"after_success": after_success,
		"rejected": rejected,
		"failure_calls": failed_client.advance_calls,
		"failure_snapshot_calls": failed_client.snapshot_calls,
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
	}


func _fail(message: String) -> void:
	printerr("advance_turn_from_bridge_probe: ", message)
	call_deferred("quit", 1)
