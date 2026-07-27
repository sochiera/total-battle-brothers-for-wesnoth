extends SceneTree


const BridgeClientScript = preload("res://scripts/bridge_client.gd")
const SnapshotModel = preload("res://scripts/snapshot_model.gd")


func _init() -> void:
	var args: PackedStringArray = OS.get_cmdline_user_args()
	if args.is_empty():
		printerr("bridge_model_probe: missing bridge command")
		call_deferred("quit", 2)
		return

	var request_path := args[1] if args.size() > 1 else ""
	var client = BridgeClientScript.create(args[0], request_path)
	var model = client.snapshot_model()
	if model == null:
		print("BRIDGE_MODEL null")
		call_deferred("quit", 0)
		return

	var region_names: Array = []
	for region in model.regions:
		if region is Dictionary and region.get("name") is String:
			region_names.append(region["name"])
	print("BRIDGE_MODEL ", JSON.stringify({
		"year": model.year,
		"month": model.month,
		"regions": model.regions.size(),
		"region_names": region_names,
		"player_result": model.player_result,
	}))
	call_deferred("quit", 0)
