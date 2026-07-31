extends SceneTree


const MAIN_SCENE_PATH := "res://scenes/main.tscn"
const BridgeClient = preload("res://scripts/bridge_client.gd")
const PREFIX := "PERSISTENT_FAILED_ORDER "
const DEVELOP_ORDER := "develop"
const UNKNOWN_ORDER := "nope"


func _init() -> void:
	var args: PackedStringArray = OS.get_cmdline_user_args()
	if args.size() != 4:
		_fail("expected command prefix, state path, request path and seed")
		return

	var seed := args[3].to_int()
	var first_scene := _instantiate_scene()
	if first_scene == null:
		return
	var first_client := BridgeClient.create_persistent(args[0], args[1], seed, args[2])
	first_scene.bind_client(first_client)
	first_scene.send_order_from_bridge(first_client, DEVELOP_ORDER)
	var before_failure := _controls(first_scene)
	var rejected: bool = first_scene.send_order_from_bridge(first_client, UNKNOWN_ORDER)
	var after_failure := _controls(first_scene)
	var state_exists_after_failure := FileAccess.file_exists(args[1])
	first_scene.queue_free()

	var resumed_scene := _instantiate_scene()
	if resumed_scene == null:
		return
	var resumed_client := BridgeClient.create_persistent(args[0], args[1], seed, args[2])
	resumed_scene.bind_client(resumed_client)
	var resumed: bool = resumed_scene.send_order_from_bridge(resumed_client, DEVELOP_ORDER)

	print(PREFIX, JSON.stringify({
		"rejected": rejected,
		"before_failure": before_failure,
		"after_failure": after_failure,
		"state_exists_after_failure": state_exists_after_failure,
		"resumed_command": resumed_client.session_command(),
		"resumed": resumed,
		"after_resume": _controls(resumed_scene),
	}))
	call_deferred("quit", 0)


func _instantiate_scene() -> Control:
	var scene := ResourceLoader.load(MAIN_SCENE_PATH) as PackedScene
	if scene == null:
		_fail("cannot load main scene")
		return null
	var scene_root := scene.instantiate() as Control
	if scene_root == null:
		_fail("cannot instantiate main scene")
		return null
	root.add_child(scene_root)
	return scene_root


func _controls(scene_root: Control) -> Dictionary:
	var region_list := scene_root.find_child("RegionList", true, false) as ItemList
	var names: Array[String] = []
	for index: int in region_list.item_count:
		names.append(region_list.get_item_text(index))
	return {
		"date": (scene_root.find_child("DateLabel", true, false) as Label).text,
		"result": (scene_root.find_child("ResultContractLabel", true, false) as Label).text,
		"duchy_status": (scene_root.find_child("PlayerDuchyStatusLabel", true, false) as Label).text,
		"regions": names,
		"order_status": (scene_root.find_child("LastOrderStatusLabel", true, false) as Label).text,
	}


func _fail(message: String) -> void:
	printerr("persistent_failed_order_e2e_probe: ", message)
	call_deferred("quit", 2)
