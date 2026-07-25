extends SceneTree


const MAIN_SCENE_PATH := "res://scenes/main.tscn"


func _init() -> void:
	var scene: PackedScene = ResourceLoader.load(MAIN_SCENE_PATH) as PackedScene
	if scene == null:
		printerr("scene_probe: cannot load main scene")
		call_deferred("quit", 2)
		return

	var scene_root: Node = scene.instantiate()
	if scene_root == null:
		printerr("scene_probe: cannot instantiate main scene")
		call_deferred("quit", 2)
		return

	root.add_child(scene_root)
	var tree: Array[Dictionary] = []
	_append_node(scene_root, scene_root, tree)
	print("SCENE_TREE ", JSON.stringify(tree))
	call_deferred("quit", 0)


func _append_node(node: Node, scene_root: Node, tree: Array[Dictionary]) -> void:
	var path: String = "." if node == scene_root else str(scene_root.get_path_to(node))
	tree.append({
		"path": path,
		"name": node.name,
		"class": node.get_class(),
	})
	for child: Node in node.get_children():
		_append_node(child, scene_root, tree)
