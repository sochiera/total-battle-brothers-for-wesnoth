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
	var date_label: Label = scene_root.find_child("DateLabel", true, false) as Label
	var result_label: Label = scene_root.find_child("ResultLabel", true, false) as Label
	# Historical G90.2b single-line contract lives on the hidden mirror.
	var result_contract: Label = scene_root.find_child("ResultContractLabel", true, false) as Label
	var duchy_status_label: Label = scene_root.find_child("PlayerDuchyStatusLabel", true, false) as Label
	var duchy_status_before_clear: Variant = duchy_status_label.text if duchy_status_label != null else null
	if clear_status:
		model.player_duchy_status = null
		scene_root.call("apply_model", model)
	var region_list: ItemList = scene_root.find_child("RegionList", true, false) as ItemList
	var region_names: Array[String] = []
	for index: int in region_list.item_count:
		region_names.append(region_list.get_item_text(index))
	var result_modulate: Color = result_label.modulate
	var result_font_color: Color = result_label.get_theme_color("font_color")
	var status_card: Node = scene_root.find_child("StatusCardContent", true, false)
	var result_export: String = (
		result_contract.text if result_contract != null else result_label.text
	)
	print("SCENE_TEXT ", JSON.stringify({
		"date": date_label.text,
		"result": result_export,
		"result_visible": result_label.text,
		"result_modulate": [
			result_modulate.r,
			result_modulate.g,
			result_modulate.b,
			result_modulate.a,
		],
		"result_font_color": [
			result_font_color.r,
			result_font_color.g,
			result_font_color.b,
			result_font_color.a,
		],
		"duchy_status_before_clear": duchy_status_before_clear,
		"duchy_status": duchy_status_label.text if duchy_status_label != null else null,
		"regions": region_list.item_count,
		"region_names": region_names,
		"status_card_labels": _visible_label_records(status_card),
		"status_card_separators": _visible_separator_count(status_card),
	}))
	call_deferred("quit", 0)


func _visible_label_records(node: Node) -> Array[Dictionary]:
	var records: Array[Dictionary] = []
	if node == null:
		return records
	_collect_visible_label_records(node, records)
	return records


func _collect_visible_label_records(
	node: Node, records: Array[Dictionary]
) -> void:
	if node is Label and (node as Label).visible:
		var parent: Node = node.get_parent()
		records.append({
			"name": str(node.name),
			"text": (node as Label).text,
			"parent": str(parent.name) if parent != null else "",
			"parent_type": parent.get_class() if parent != null else "",
		})
	for child: Node in node.get_children():
		_collect_visible_label_records(child, records)


func _visible_separator_count(node: Node) -> int:
	if node == null:
		return 0
	var count := 0
	if (node is HSeparator or node is VSeparator) and (node as CanvasItem).visible:
		count += 1
	for child: Node in node.get_children():
		count += _visible_separator_count(child)
	return count


func _fail(message: String) -> void:
	printerr(message)
	call_deferred("quit", 2)
