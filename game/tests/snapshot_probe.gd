extends SceneTree


const SnapshotModel = preload("res://scripts/snapshot_model.gd")


func _init() -> void:
	var args: PackedStringArray = OS.get_cmdline_user_args()
	if args.is_empty():
		printerr("snapshot_probe: missing response path")
		call_deferred("quit", 2)
		return

	var path: String = args[0]
	var file: FileAccess = FileAccess.open(path, FileAccess.READ)
	if file == null:
		printerr("snapshot_probe: cannot open response file: ", path)
		call_deferred("quit", 2)
		return

	var response_text: String = file.get_as_text()
	file.close()
	var response: Dictionary = JSON.parse_string(response_text)
	var model: SnapshotModel = SnapshotModel.from_response(response)
	if model == null:
		print("SNAPSHOT_MODEL null")
		call_deferred("quit", 0)
		return

	print("SNAPSHOT_MODEL ", JSON.stringify({
		"year": model.year,
		"month": model.month,
		"regions": model.regions,
		"player_result": model.player_result,
	}))
	call_deferred("quit", 0)
