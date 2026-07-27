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

	print(PREFIX, JSON.stringify({"name": button.name, "text": button.text, "disabled": button.disabled}))
	call_deferred("quit", 0)


func _fail(message: String) -> void:
	printerr("next_turn_button_probe: ", message)
	call_deferred("quit", 1)
