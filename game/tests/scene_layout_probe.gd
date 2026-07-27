extends SceneTree


## Headless probe: after main.tscn is in the tree and has had a chance to lay out,
## report global rects of the public status/order controls (found by name under root).
##
## Dependency: add_child runs Main._ready → start_session(BridgeConfig.from_environment()),
## so this probe exercises a full bridge autostart even though it only asserts geometry.
## The layout pytest gate (timeout=30s) therefore needs a working default bridge/env;
## it is not a pure geometry-only fixture that skips the session.

const MAIN_SCENE_PATH := "res://scenes/main.tscn"
const PREFIX := "SCENE_LAYOUT "

const CONTROL_NAMES: Array[String] = [
	"DateLabel",
	"StartStatusLabel",
	"RegionList",
	"ResultLabel",
	"PlayerDuchyStatusLabel",
	"LastOrderStatusLabel",
	"PlayerPartyPositionLabel",
	"NextTurnButton",
	"DevelopButton",
	"RecruitButton",
	"MusterButton",
	"MarchButton",
	"AssaultButton",
]


func _init() -> void:
	call_deferred("_run")


func _run() -> void:
	var scene: PackedScene = ResourceLoader.load(MAIN_SCENE_PATH) as PackedScene
	if scene == null:
		printerr("scene_layout_probe: cannot load main scene")
		quit(2)
		return

	var scene_root: Node = scene.instantiate()
	if scene_root == null:
		printerr("scene_layout_probe: cannot instantiate main scene")
		quit(2)
		return

	root.add_child(scene_root)
	# Containers and content min-sizes settle after idle frames.
	await process_frame
	await process_frame

	var controls: Dictionary = {}
	for control_name: String in CONTROL_NAMES:
		var node: Control = scene_root.find_child(control_name, true, false) as Control
		if node == null:
			controls[control_name] = null
			continue
		var rect: Rect2 = node.get_global_rect()
		controls[control_name] = {
			"x": rect.position.x,
			"y": rect.position.y,
			"w": rect.size.x,
			"h": rect.size.y,
		}

	print(PREFIX, JSON.stringify({"controls": controls}))
	quit(0)
