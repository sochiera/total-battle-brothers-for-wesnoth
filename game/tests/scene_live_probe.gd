extends SceneTree


const MAIN_SCENE_PATH := "res://scenes/main.tscn"
const BridgeClientScript = preload("res://scripts/bridge_client.gd")


func _init() -> void:
	var args: PackedStringArray = OS.get_cmdline_user_args()
	if args.is_empty():
		_fail("scene_live_probe: missing bridge command")
		return

	var scene: PackedScene = ResourceLoader.load(MAIN_SCENE_PATH) as PackedScene
	if scene == null:
		_fail("scene_live_probe: cannot load main scene")
		return

	var scene_root: Control = scene.instantiate() as Control
	if scene_root == null:
		_fail("scene_live_probe: cannot instantiate main scene")
		return

	var request_path := args[1] if args.size() > 1 else ""
	var client = BridgeClientScript.create(args[0], request_path)
	root.add_child(scene_root)
	var refreshed: bool = scene_root.refresh_from_bridge(client)
	var date_label: Label = scene_root.get_node("DateLabel") as Label
	var result_label: Label = scene_root.get_node("ResultLabel") as Label
	var region_list: ItemList = scene_root.get_node("RegionList") as ItemList
	var region_names: Array[String] = []
	for index: int in region_list.item_count:
		region_names.append(region_list.get_item_text(index))
	print("SCENE_LIVE ", JSON.stringify({
		"refreshed": refreshed,
		"date": date_label.text,
		"result": result_label.text,
		"regions": region_list.item_count,
		"region_names": region_names,
	}))
	call_deferred("quit", 0)


func _fail(message: String) -> void:
	printerr(message)
	call_deferred("quit", 2)
