extends SceneTree


const MAIN_SCENE_PATH := "res://scenes/main.tscn"
const PREFIX := "DEVELOP_BUTTON "


func _init() -> void:
	var scene: PackedScene = ResourceLoader.load(MAIN_SCENE_PATH) as PackedScene
	if scene == null:
		printerr("develop_button_probe: cannot load main scene")
		call_deferred("quit", 2)
		return

	var scene_root := scene.instantiate()
	root.add_child(scene_root)
	var button := scene_root.find_child("DevelopButton", true, false) as Button
	if button == null:
		printerr("develop_button_probe: missing DevelopButton")
		call_deferred("quit", 1)
		return

	var before_children := scene_root.get_child_count()
	var connections := button.get_signal_connection_list("pressed")
	button.emit_signal("pressed")
	var result := {
		"text": button.text,
		"pressed_connections": connections.size(),
		"child_count_unchanged": scene_root.get_child_count() == before_children,
	}
	print(PREFIX, JSON.stringify(result))
	call_deferred("quit", 0)
