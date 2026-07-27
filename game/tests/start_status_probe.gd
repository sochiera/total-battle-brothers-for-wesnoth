extends SceneTree


const MAIN_SCENE_PATH := "res://scenes/main.tscn"
const BridgeConfig = preload("res://scripts/bridge_config.gd")
const PREFIX := "START_STATUS "


func _init() -> void:
	var args: PackedStringArray = OS.get_cmdline_user_args()
	var scene := ResourceLoader.load(MAIN_SCENE_PATH) as PackedScene
	if scene == null:
		_fail("cannot load main scene")
		return
	var scene_root := scene.instantiate() as Control
	if scene_root == null:
		_fail("cannot instantiate main scene")
		return
	root.add_child(scene_root)

	if args.is_empty():
		call_deferred("_observe_autostart", scene_root)
		return

	if args.size() != 3:
		_fail("expected no args (autostart) or command, state path and seed")
		return
	if not scene_root.has_method("start_session"):
		print(PREFIX, JSON.stringify({"available": false}))
		call_deferred("quit", 0)
		return

	var config: Variant = BridgeConfig.from_values(args[0], args[1], args[2])
	var started: bool = scene_root.start_session(config)
	print(PREFIX, JSON.stringify(_payload(scene_root, started, args[1])))
	call_deferred("quit", 0)


func _observe_autostart(scene_root: Control) -> void:
	var config: Dictionary = BridgeConfig.from_environment()
	var state_path: String = str(config.get("state_path", ""))
	print(PREFIX, JSON.stringify(_payload(scene_root, null, state_path)))
	call_deferred("quit", 0)


func _payload(scene_root: Control, started: Variant, state_path: String) -> Dictionary:
	var status_label := scene_root.get_node_or_null("StartStatusLabel") as Label
	var region_list := scene_root.get_node("RegionList") as ItemList
	var names: Array[String] = []
	for index: int in region_list.item_count:
		names.append(region_list.get_item_text(index))
	return {
		"available": true,
		"has_start_status_label": status_label != null,
		"start_status": "" if status_label == null else status_label.text,
		"order_status": (scene_root.get_node("LastOrderStatusLabel") as Label).text,
		"date": (scene_root.get_node("DateLabel") as Label).text,
		"duchy_status": (scene_root.get_node("PlayerDuchyStatusLabel") as Label).text,
		"regions": names,
		"started": started,
		"state_exists": (
			not state_path.is_empty() and FileAccess.file_exists(state_path)
		),
	}


func _fail(message: String) -> void:
	printerr("start_status_probe: ", message)
	call_deferred("quit", 2)
