extends SceneTree


const MAIN_SCENE_PATH := "res://scenes/main.tscn"
const SnapshotModel = preload("res://scripts/snapshot_model.gd")
const PREFIX := "PARTY_POSITION "


class StubClient extends RefCounted:
	var model: SnapshotModel

	func _init(next_model: SnapshotModel) -> void:
		model = next_model

	func snapshot_model() -> SnapshotModel:
		return model

	func advance_turn() -> SnapshotModel:
		return model

	func send_order(_order_name: String) -> SnapshotModel:
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
	var position_label := scene_root.get_node_or_null("PlayerPartyPositionLabel") as Label
	if position_label == null:
		print(PREFIX, JSON.stringify({"available": false}))
		call_deferred("quit", 0)
		return

	scene_root.apply_model(_model("Stary Gród"))
	var present_first := position_label.text
	scene_root.apply_model(_model("Stary Gród"))
	var present_second := position_label.text
	scene_root.apply_model(_model(null))
	var missing := position_label.text
	scene_root.apply_model(_model(""))
	var empty := position_label.text
	scene_root.apply_model(_model("Nowy Gród"))
	var moved := position_label.text
	scene_root.refresh_from_bridge(StubClient.new(_model("Odświeżony Gród")))
	var refreshed := position_label.text
	scene_root.advance_turn_from_bridge(StubClient.new(_model("Gród po turze")))
	var advanced := position_label.text
	scene_root.send_order_from_bridge(
		StubClient.new(_model("Gród po rozkazie", 9)), "muster"
	)
	print(PREFIX, JSON.stringify({
		"available": true,
		"present_first": present_first,
		"present_second": present_second,
		"missing": missing,
		"empty": empty,
		"moved": moved,
		"refreshed": refreshed,
		"advanced": advanced,
		"ordered": position_label.text,
		"date_after_order": (scene_root.get_node("DateLabel") as Label).text,
	}))
	call_deferred("quit", 0)


func _model(party_region: Variant, year: int = 1) -> SnapshotModel:
	var model := SnapshotModel.new()
	model.year = year
	model.month = 1
	model.player_result = "ongoing"
	model.regions = []
	model.player_party_region = party_region
	return model


func _fail(message: String) -> void:
	printerr("party_position_probe: ", message)
	call_deferred("quit", 1)
