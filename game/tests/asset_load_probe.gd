extends SceneTree


## Headless probe: each CLI path must load as Texture2D (not null / wrong type).
## Prints one ASSET_LOAD line with a JSON array of {path, ok, class}.


func _init() -> void:
	call_deferred("_run")


func _run() -> void:
	var paths: PackedStringArray = OS.get_cmdline_user_args()
	if paths.is_empty():
		printerr("asset_load_probe: no asset paths given")
		quit(2)
		return

	var results: Array = []
	var all_ok := true
	for path_variant: Variant in paths:
		var path: String = str(path_variant)
		var resource: Resource = load(path)
		var ok: bool = resource is Texture2D
		if not ok:
			all_ok = false
		var class_name_str: String = "null"
		if resource != null:
			class_name_str = resource.get_class()
		results.append({
			"path": path,
			"ok": ok,
			"class": class_name_str,
		})

	print("ASSET_LOAD ", JSON.stringify(results))
	quit(0 if all_ok else 1)
