extends SceneTree


const MAIN_SCENE_PATH := "res://scenes/main.tscn"
const PREFIX := "ORDER_STATUS "


func _init() -> void:
	var scene: PackedScene = ResourceLoader.load(MAIN_SCENE_PATH) as PackedScene
	if scene == null:
		printerr("order_status_probe: cannot load main scene")
		call_deferred("quit", 2)
		return

	var scene_root := scene.instantiate()
	root.add_child(scene_root)
	var status_label := scene_root.get_node_or_null("LastOrderStatusLabel") as Label
	if status_label == null:
		printerr("order_status_probe: missing LastOrderStatusLabel")
		call_deferred("quit", 1)
		return

	print(PREFIX, JSON.stringify({"text": status_label.text}))
	call_deferred("quit", 0)
