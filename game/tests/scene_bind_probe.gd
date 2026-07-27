extends SceneTree


const MAIN_SCENE_PATH := "res://scenes/main.tscn"
const SnapshotModel = preload("res://scripts/snapshot_model.gd")
const INVALID_APPLICATIONS_MESSAGE := "scene_bind_probe: applications must be a positive integer"
const CLEAR_STATUS_MODE := "clear_status"


func _init() -> void:
	var args: PackedStringArray = OS.get_cmdline_user_args()
	if args.is_empty():
		_fail("scene_bind_probe: missing response path")
		return

	var applications := 1
	if args.size() >= 2:
		var applications_arg: String = args[1]
		if not applications_arg.is_valid_int():
			_fail(INVALID_APPLICATIONS_MESSAGE)
			return
		applications = applications_arg.to_int()
		if applications <= 0:
			_fail(INVALID_APPLICATIONS_MESSAGE)
			return
	var clear_status := false
	if args.size() >= 3:
		if args[2] != CLEAR_STATUS_MODE:
			_fail("scene_bind_probe: invalid mode")
			return
		clear_status = true

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
	for _application: int in applications:
		scene_root.call("apply_model", model)
	var date_label: Label = scene_root.get_node("DateLabel") as Label
	var result_label: Label = scene_root.get_node("ResultLabel") as Label
	var duchy_status_label: Label = scene_root.get_node_or_null("PlayerDuchyStatusLabel") as Label
	var duchy_status_before_clear: Variant = duchy_status_label.text if duchy_status_label != null else null
	if clear_status:
		model.player_duchy_status = null
		scene_root.call("apply_model", model)
	var region_list: ItemList = scene_root.get_node("RegionList") as ItemList
	var region_names: Array[String] = []
	for index: int in region_list.item_count:
		region_names.append(region_list.get_item_text(index))
	print("SCENE_TEXT ", JSON.stringify({
		"date": date_label.text,
		"result": result_label.text,
		"duchy_status_before_clear": duchy_status_before_clear,
		"duchy_status": duchy_status_label.text if duchy_status_label != null else null,
		"regions": region_list.item_count,
		"region_names": region_names,
	}))
	call_deferred("quit", 0)


func _fail(message: String) -> void:
	printerr(message)
	call_deferred("quit", 2)
