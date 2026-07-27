extends SceneTree


const MAIN_SCENE_PATH := "res://scenes/main.tscn"
const MainScene = preload("res://scripts/main.gd")
const PREFIX := "DEVELOP_BUTTON_SHARED_ORDER_PATH "


class TrackingScene extends MainScene:
	var calls: Array[String] = []

	func develop_from_bridge(_client) -> bool:
		calls.append("develop_from_bridge")
		return true

	func send_order_from_bridge(_client, order_name: String) -> bool:
		calls.append("send_order_from_bridge:%s" % order_name)
		return true


func _init() -> void:
	var packed_scene := ResourceLoader.load(MAIN_SCENE_PATH) as PackedScene
	if packed_scene == null:
		_fail("cannot load main scene")
		return
	var scene_root := packed_scene.instantiate() as Control
	if scene_root == null:
		_fail("cannot instantiate main scene")
		return
	scene_root.set_script(TrackingScene)
	root.add_child(scene_root)
	var button := scene_root.find_child("DevelopButton", true, false) as Button
	if button == null:
		_fail("missing DevelopButton")
		return
	scene_root.bind_client(RefCounted.new())
	button.emit_signal("pressed")

	print(PREFIX, JSON.stringify({"calls": scene_root.calls}))
	call_deferred("quit", 0)


func _fail(message: String) -> void:
	printerr("develop_button_shared_order_path_probe: ", message)
	call_deferred("quit", 1)
