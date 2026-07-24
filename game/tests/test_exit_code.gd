extends SceneTree


func _init() -> void:
	call_deferred("quit", 1 if "--fail" in OS.get_cmdline_user_args() else 0)
