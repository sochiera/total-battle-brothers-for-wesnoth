extends SceneTree


const MAIN_SCENE_PATH := "res://scenes/main.tscn"
const PREFIX := "FIELD_ORDER_ICONS "

const BUTTONS := [
	{"name": "MarchButton", "text": "Wyrusz w pole"},
	{"name": "AssaultButton", "text": "Szturmuj osadę"},
	{"name": "EngageButton", "text": "Uderz na wojsko wroga"},
]


func _init() -> void:
	var scene := ResourceLoader.load(MAIN_SCENE_PATH) as PackedScene
	if scene == null:
		_fail("cannot load main scene")
		return
	var scene_root := scene.instantiate()
	if scene_root == null:
		_fail("cannot instantiate main scene")
		return
	root.add_child(scene_root)

	var orders: Array = []
	for entry in BUTTONS:
		var button := scene_root.find_child(entry["name"], true, false)
		if button == null:
			_fail("missing %s" % entry["name"])
			return
		if not button is Button:
			_fail("%s is not a Button" % entry["name"])
			return
		var btn := button as Button
		if btn.text != entry["text"]:
			_fail("unexpected label on %s" % entry["name"])
			return

		var icon_path := ""
		var icon_w := 0
		var icon_h := 0
		if btn.icon != null:
			var tex := btn.icon as Texture2D
			icon_path = tex.resource_path
			icon_w = int(tex.get_width())
			icon_h = int(tex.get_height())

		orders.append(
			{
				"name": btn.name,
				"text": btn.text,
				"icon_path": icon_path,
				"icon_w": icon_w,
				"icon_h": icon_h,
			}
		)

	print(PREFIX, JSON.stringify({"orders": orders}))
	call_deferred("quit", 0)


func _fail(message: String) -> void:
	printerr("field_order_icons_probe: ", message)
	call_deferred("quit", 1)
