extends SceneTree


## Headless probe: each CLI path must load as Texture2D (not null / wrong type).
## Prints one ASSET_LOAD line with a JSON array of
## {path, ok, class, width, height, alpha} (size/alpha when Texture2D yields Image).


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
		var width: int = 0
		var height: int = 0
		# Image.AlphaMode: NONE=0, BIT=1, BLEND=2; -1 if no image.
		var alpha: int = -1
		if resource is Texture2D:
			var tex: Texture2D = resource as Texture2D
			var img: Image = tex.get_image()
			if img != null:
				width = img.get_width()
				height = img.get_height()
				alpha = int(img.detect_alpha())
		results.append({
			"path": path,
			"ok": ok,
			"class": class_name_str,
			"width": width,
			"height": height,
			"alpha": alpha,
		})

	print("ASSET_LOAD ", JSON.stringify(results))
	quit(0 if all_ok else 1)
