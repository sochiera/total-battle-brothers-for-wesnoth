extends SceneTree


const MAIN_SCENE_PATH := "res://scenes/main.tscn"
const SnapshotModel = preload("res://scripts/snapshot_model.gd")
const PREFIX := "START_SESSION_INVALID "


func _init() -> void:
	var args: PackedStringArray = OS.get_cmdline_user_args()
	if args.size() != 2:
		_fail("expected state path and bridge marker path")
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
	if not scene_root.has_method("start_session"):
		print(PREFIX, JSON.stringify({"available": false}))
		call_deferred("quit", 0)
		return

	var model := SnapshotModel.new()
	model.year = 9
	model.month = 8
	model.player_result = "preset"
	model.regions = [{"name": "Zachowany region"}]
	scene_root.apply_model(model)
	var before := _controls(scene_root)
	var command := "touch '%s'" % args[1]
	var results: Array[bool] = []
	results.append(scene_root.start_session(null))
	results.append(scene_root.start_session({}))
	results.append(scene_root.start_session({
		"command": command,
		"state_path": args[0],
	}))
	results.append(scene_root.start_session({
		"command": command,
		"seed": 73,
	}))

	print(PREFIX, JSON.stringify({
		"available": true,
		"results": results,
		"controls_unchanged": _controls(scene_root) == before,
		"bridge_started": FileAccess.file_exists(args[1]),
	}))
	call_deferred("quit", 0)


func _controls(scene_root: Control) -> Dictionary:
	var region_list := scene_root.get_node("RegionList") as ItemList
	var names: Array[String] = []
	for index: int in region_list.item_count:
		names.append(region_list.get_item_text(index))
	return {
		"date": (scene_root.get_node("DateLabel") as Label).text,
		"result": (scene_root.get_node("ResultLabel") as Label).text,
		"regions": names,
	}


func _fail(message: String) -> void:
	printerr("start_session_invalid_config_probe: ", message)
	call_deferred("quit", 2)
