extends SceneTree


const MAIN_SCENE_PATH := "res://scenes/main.tscn"
const SnapshotModel = preload("res://scripts/snapshot_model.gd")


func _init() -> void:
	var args: PackedStringArray = OS.get_cmdline_user_args()
	if args.is_empty():
		_fail("scene_bind_probe: missing response path")
		return

	var path: String = args[0]
	var file: FileAccess = FileAccess.open(path, FileAccess.READ)
	if file == null:
		_fail("scene_bind_probe: cannot open response file: " + path)
		return

	var response_text: String = file.get_as_text()
	file.close()
	var parsed: Variant = JSON.parse_string(response_text)
	if not parsed is Dictionary:
		_fail("scene_bind_probe: invalid response JSON")
		return

	var model: SnapshotModel = SnapshotModel.from_response(parsed)
	if model == null:
		_fail("scene_bind_probe: response has no usable snapshot")
		return

	var scene: PackedScene = ResourceLoader.load(MAIN_SCENE_PATH) as PackedScene
	if scene == null:
		_fail("scene_bind_probe: cannot load main scene")
		return

	var scene_root: Control = scene.instantiate() as Control
	if scene_root == null:
		_fail("scene_bind_probe: cannot instantiate main scene")
		return

	root.add_child(scene_root)
	scene_root.call("apply_model", model)
	var date_label: Label = scene_root.get_node("DateLabel") as Label
	var result_label: Label = scene_root.get_node("ResultLabel") as Label
	var region_list: ItemList = scene_root.get_node("RegionList") as ItemList
	print("SCENE_TEXT ", JSON.stringify({
		"date": date_label.text,
		"result": result_label.text,
		"regions": region_list.item_count,
	}))
	call_deferred("quit", 0)


func _fail(message: String) -> void:
	printerr(message)
	call_deferred("quit", 2)
