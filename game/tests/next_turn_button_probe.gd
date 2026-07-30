extends SceneTree


const MAIN_SCENE_PATH := "res://scenes/main.tscn"
const PREFIX := "NEXT_TURN_BUTTON "


func _init() -> void:
	var expected_label := "Następna tura"
	var args := OS.get_cmdline_user_args()
	if args.size() == 1:
		expected_label = args[0]
	elif args.size() > 1:
		_fail("expected at most one label argument")
		return

	var scene := ResourceLoader.load(MAIN_SCENE_PATH) as PackedScene
	if scene == null:
		_fail("cannot load main scene")
		return
	var scene_root := scene.instantiate()
	if scene_root == null:
		_fail("cannot instantiate main scene")
		return
	root.add_child(scene_root)

	var button := scene_root.find_child("NextTurnButton", true, false)
	if button == null:
		_fail("missing NextTurnButton")
		return
	if not button is Button:
		_fail("NextTurnButton is not a Button")
		return
	if button.text != expected_label:
		_fail("unexpected button label")
		return
	if button.disabled:
		_fail("NextTurnButton is disabled")
		return

	var btn := button as Button
	var icon_path := ""
	var icon_w := 0
	var icon_h := 0
	var has_icon := false
	if btn.icon != null and btn.icon is Texture2D:
		var tex := btn.icon as Texture2D
		has_icon = true
		icon_path = tex.resource_path
		icon_w = int(tex.get_width())
		icon_h = int(tex.get_height())

	print(
		PREFIX,
		JSON.stringify(
			{
				"name": btn.name,
				"text": btn.text,
				"disabled": btn.disabled,
				"has_icon": has_icon,
				"icon_path": icon_path,
				"icon_w": icon_w,
				"icon_h": icon_h,
			}
		)
	)
	call_deferred("quit", 0)


func _fail(message: String) -> void:
	printerr("next_turn_button_probe: ", message)
	call_deferred("quit", 1)
