extends SceneTree


const MAIN_SCENE_PATH := "res://scenes/main.tscn"
const BridgeClient = preload("res://scripts/bridge_client.gd")
const BridgeConfig = preload("res://scripts/bridge_config.gd")
const PREFIX := "SAVE_LOAD_BINDING "


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
	call_deferred("_run", scene_root)


func _run(scene_root: Control) -> void:
	var config: Dictionary = BridgeConfig.from_environment()
	var save_path: String = config["save_path"]
	var state_path: String = config["state_path"]
	var command: String = config["command"]
	var seed: int = config["seed"]
	var save_button := scene_root.get_node_or_null("%SaveGameButton") as Button
	var load_button := scene_root.get_node_or_null("%LoadGameButton") as Button
	var next_button := scene_root.get_node_or_null("%NextTurnButton") as Button
	if save_button == null or load_button == null or next_button == null:
		_fail("missing SaveGameButton, LoadGameButton or NextTurnButton")
		return

	var after_start := _controls(scene_root)

	save_button.emit_signal("pressed")
	var after_save := _controls(scene_root)
	var slot_exists_after_save := FileAccess.file_exists(save_path)

	next_button.emit_signal("pressed")
	var after_turn := _controls(scene_root)

	load_button.emit_signal("pressed")
	var after_load := _controls(scene_root)

	# G86.2b durability: second bridge process on the same state_path must see
	# the loaded party (year 1 / month 1), not the post-turn state.
	var resumed := BridgeClient.create_persistent(command, state_path, seed)
	var resumed_model: Variant = resumed.snapshot_model()
	var resumed_after_load: Variant = _model_calendar(resumed_model)

	if FileAccess.file_exists(save_path):
		DirAccess.remove_absolute(save_path)
	load_button.emit_signal("pressed")
	var after_failed_load := _controls(scene_root)

	next_button.emit_signal("pressed")
	var after_turn_after_fail := _controls(scene_root)

	print(PREFIX, JSON.stringify({
		"after_start": after_start,
		"slot_exists_after_save": slot_exists_after_save,
		"after_save": after_save,
		"after_turn": after_turn,
		"after_load": after_load,
		"resumed_after_load": resumed_after_load,
		"after_failed_load": after_failed_load,
		"after_turn_after_fail": after_turn_after_fail,
	}))
	call_deferred("quit", 0)


func _model_calendar(model: Variant) -> Variant:
	if model == null:
		return null
	return {"year": model.year, "month": model.month}


func _controls(scene_root: Control) -> Dictionary:
	return {
		"date": (scene_root.find_child("DateLabel", true, false) as Label).text,
		"duchy_status": (scene_root.find_child("PlayerDuchyStatusLabel", true, false) as Label).text,
		"status": (scene_root.find_child("LastOrderStatusLabel", true, false) as Label).text,
	}


func _fail(message: String) -> void:
	printerr("save_load_binding_probe: ", message)
	call_deferred("quit", 2)
