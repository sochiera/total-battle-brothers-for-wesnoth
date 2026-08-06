extends SceneTree


## G78/G90 next-turn e2e on a live persistent bridge.
## Default (4 args): two NextTurn presses across two scene+bridge processes.
## Phase ``survive_first_turn`` (5th arg): one NextTurn, then resume-only — G90.1b.
## Phase ``muster_then_two_turns``: muster + turn, then resume + turn — G92.1b.
## Phase ``restart_finished``: ended save → NewGame click → resumed live order — G107.1c.
## Phase ``restart_failure``: unavailable bridge → NewGame click reports failure — G107.1c.

const MAIN_SCENE_PATH := "res://scenes/main.tscn"
const BridgeClientScript = preload("res://scripts/bridge_client.gd")
const PartyMapMark = preload("res://tests/party_map_mark_helpers.gd")
const PREFIX := "PERSISTENT_NEXT_TURN "
const PLAYER_LANDS := "player lands"
const AI_LANDS := "ai lands"


func _init() -> void:
	var args: PackedStringArray = OS.get_cmdline_user_args()
	if args.size() == 5:
		match args[4]:
			"muster_then_two_turns":
				_run_muster_then_two_turns(args)
			"survive_first_turn":
				_run_survive_first_turn(args)
			"restart_finished":
				_run_restart_finished(args)
			"restart_failure":
				_run_restart_failure(args)
			_:
				_fail("unknown phase; expected survive_first_turn, muster_then_two_turns, restart_finished, or restart_failure")
		return
	if args.size() != 4:
		_fail("expected command prefix, state path, request path, seed [, phase]")
		return
	_run_two_presses(args)


func _run_muster_then_two_turns(args: PackedStringArray) -> void:
	var seed := args[3].to_int()
	var first_scene := _instantiate_scene()
	if first_scene == null:
		return
	var first_client = BridgeClientScript.create_persistent(args[0], args[1], seed, args[2])
	first_scene.bind_client(first_client)
	var before_turn := _controls_with_order_status(first_scene)
	var muster_button := first_scene.find_child("MusterButton", true, false) as Button
	var first_turn_button := first_scene.find_child("NextTurnButton", true, false) as Button
	if muster_button == null or first_turn_button == null:
		_fail("missing MusterButton or NextTurnButton")
		return
	muster_button.emit_signal("pressed")
	var after_muster := _controls_with_order_status(first_scene)
	first_turn_button.emit_signal("pressed")
	var after_first_turn := _controls_with_order_status(first_scene)
	var state_exists := FileAccess.file_exists(args[1])
	first_scene.queue_free()

	var second_scene := _instantiate_scene()
	if second_scene == null:
		return
	var second_client = BridgeClientScript.create_persistent(args[0], args[1], seed, args[2])
	second_scene.bind_client(second_client)
	var after_resume := _controls_with_order_status(second_scene)
	var second_turn_button := second_scene.find_child("NextTurnButton", true, false) as Button
	if second_turn_button == null:
		_fail("missing NextTurnButton after resume")
		return
	second_turn_button.emit_signal("pressed")

	print(PREFIX, JSON.stringify({
		"phase": "muster_then_two_turns",
		"state_exists_after_first_turn": state_exists,
		"before_turn": before_turn,
		"after_muster": after_muster,
		"after_first_turn": after_first_turn,
		"after_resume": after_resume,
		"after_second_turn": _controls_with_order_status(second_scene),
	}))
	call_deferred("quit", 0)


func _run_two_presses(args: PackedStringArray) -> void:
	var seed := args[3].to_int()
	var first_scene := _instantiate_scene()
	if first_scene == null:
		return
	var first_client = BridgeClientScript.create_persistent(args[0], args[1], seed, args[2])
	first_scene.bind_client(first_client)
	var first_button := first_scene.find_child("NextTurnButton", true, false) as Button
	if first_button == null:
		_fail("missing NextTurnButton")
		return
	first_button.emit_signal("pressed")
	var first := _controls(first_scene)
	var state_exists_after_first_press := FileAccess.file_exists(args[1])
	first_scene.queue_free()

	var second_scene := _instantiate_scene()
	if second_scene == null:
		return
	var second_client = BridgeClientScript.create_persistent(args[0], args[1], seed, args[2])
	second_scene.bind_client(second_client)
	var second_button := second_scene.find_child("NextTurnButton", true, false) as Button
	if second_button == null:
		_fail("missing NextTurnButton after resume")
		return
	second_button.emit_signal("pressed")

	print(PREFIX, JSON.stringify({
		"state_exists_after_first_press": state_exists_after_first_press,
		"first": first,
		"second": _controls(second_scene),
	}))
	call_deferred("quit", 0)


func _run_survive_first_turn(args: PackedStringArray) -> void:
	## Fresh party → one NextTurn → observe map owner paint + duchy status;
	## second scene only resumes (no second press) and must match.
	var seed := args[3].to_int()
	var first_scene := _instantiate_scene()
	if first_scene == null:
		return
	var first_client = BridgeClientScript.create_persistent(args[0], args[1], seed, args[2])
	first_scene.bind_client(first_client)
	var after_start := _survival_observation(first_scene)

	var first_button := first_scene.find_child("NextTurnButton", true, false) as Button
	if first_button == null:
		_fail("missing NextTurnButton")
		return
	first_button.emit_signal("pressed")
	var after_first_turn := _survival_observation(first_scene)
	var state_exists := FileAccess.file_exists(args[1])
	first_scene.queue_free()

	var second_scene := _instantiate_scene()
	if second_scene == null:
		return
	var second_client = BridgeClientScript.create_persistent(args[0], args[1], seed, args[2])
	second_scene.bind_client(second_client)
	var after_resume := _survival_observation(second_scene)

	print(PREFIX, JSON.stringify({
		"phase": "survive_first_turn",
		"state_exists_after_first_press": state_exists,
		"session_command_after_resume": second_client.session_command(),
		"after_start": after_start,
		"after_first_turn": after_first_turn,
		"after_resume": after_resume,
	}))
	call_deferred("quit", 0)


func _run_restart_finished(args: PackedStringArray) -> void:
	## The Python gate seeds the state file with a resolved player victory.  This
	## probes the public UI path: render finished → click NewGame → next bridge
	## process resumes fresh state and accepts an order.
	var first := _instantiate_persistent_scene(args)
	if first.is_empty():
		return
	var first_scene := first["scene_root"] as Control
	var before_restart := _controls_with_order_status(first_scene)
	var new_game_button := first_scene.find_child("NewGameButton", true, false) as Button
	if new_game_button == null:
		_fail("missing NewGameButton")
		return
	new_game_button.emit_signal("pressed")
	var after_restart := _survival_observation(first_scene)
	first_scene.queue_free()

	var second := _instantiate_persistent_scene(args)
	if second.is_empty():
		return
	var second_scene := second["scene_root"] as Control
	var after_resume := _survival_observation(second_scene)
	var recruit_button := second_scene.find_child("RecruitButton", true, false) as Button
	if recruit_button == null:
		_fail("missing RecruitButton after restart")
		return
	recruit_button.emit_signal("pressed")

	print(PREFIX, JSON.stringify({
		"phase": "restart_finished",
		"before_restart": before_restart,
		"after_restart": after_restart,
		"after_resume": after_resume,
		"after_resumed_recruit": _controls_with_order_status(second_scene),
	}))
	call_deferred("quit", 0)


func _run_restart_failure(args: PackedStringArray) -> void:
	## The public button must leave a useful Polish error after the persistent
	## bridge fails, rather than silently retaining the empty initial status.
	var persistent_scene := _instantiate_persistent_scene(args)
	if persistent_scene.is_empty():
		return
	var scene_root := persistent_scene["scene_root"] as Control
	var new_game_button := scene_root.find_child("NewGameButton", true, false) as Button
	if new_game_button == null:
		_fail("missing NewGameButton")
		return
	new_game_button.emit_signal("pressed")

	print(PREFIX, JSON.stringify({
		"phase": "restart_failure",
		"after_failed_restart": _controls_with_order_status(scene_root),
	}))
	call_deferred("quit", 0)


func _instantiate_persistent_scene(args: PackedStringArray) -> Dictionary:
	var scene_root := _instantiate_scene()
	if scene_root == null:
		return {}
	var client = BridgeClientScript.create_persistent(
		args[0], args[1], args[3].to_int(), args[2]
	)
	scene_root.bind_client(client)
	return {"scene_root": scene_root}


func _instantiate_scene() -> Control:
	var scene := ResourceLoader.load(MAIN_SCENE_PATH) as PackedScene
	if scene == null:
		_fail("cannot load main scene")
		return null
	var scene_root := scene.instantiate() as Control
	if scene_root == null:
		_fail("cannot instantiate main scene")
		return null
	root.add_child(scene_root)
	return scene_root


func _controls(scene_root: Control) -> Dictionary:
	var region_list := scene_root.find_child("RegionList", true, false) as ItemList
	var names: Array[String] = []
	for index: int in region_list.item_count:
		names.append(region_list.get_item_text(index))
	return {
		"date": (scene_root.find_child("DateLabel", true, false) as Label).text,
		"result": (scene_root.find_child("ResultContractLabel", true, false) as Label).text,
		"duchy_status": (scene_root.find_child("PlayerDuchyStatusLabel", true, false) as Label).text,
		"regions": names,
	}


func _controls_with_order_status(scene_root: Control) -> Dictionary:
	var controls := _controls(scene_root)
	controls["order_status"] = (
		scene_root.find_child("LastOrderStatusLabel", true, false) as Label
	).text
	return controls


func _survival_observation(scene_root: Control) -> Dictionary:
	var base: Dictionary = _controls_with_order_status(scene_root)
	var map_view: Node = scene_root.find_child("MapView", true, false)
	var tile_visuals: Dictionary = {}
	if map_view != null:
		for region_name: String in [PLAYER_LANDS, AI_LANDS]:
			var visual: String = _tile_visual(map_view, region_name)
			if not visual.is_empty():
				tile_visuals[region_name] = visual
	base["map_view_found"] = map_view != null
	base["tile_visuals"] = tile_visuals
	return base


func _tile_visual(map_view: Node, region_name: String) -> String:
	var label: Label = PartyMapMark.find_label_with_text(map_view, region_name)
	if label == null:
		return ""
	var tile: Control = PartyMapMark.tile_control(label, map_view)
	return _visual_key(tile)


func _visual_key(tile: Control) -> String:
	## Same ownership observation as map_view_probe: paint key without names.
	if tile is ColorRect:
		return _color_key((tile as ColorRect).color)
	if tile is TextureRect:
		var root_mod: Color = (tile as CanvasItem).modulate
		if root_mod != Color(1, 1, 1, 1):
			return _color_key(root_mod)
	for child: Node in tile.get_children():
		var child_name: String = str(child.name)
		if child_name == "PlayerPartyMarker" or child_name == "Settlement":
			continue
		if child is ColorRect:
			return _color_key((child as ColorRect).color)
		if child is TextureRect:
			return _color_key((child as CanvasItem).modulate)
	return _color_key(tile.modulate)


func _color_key(color: Color) -> String:
	return "%.4f,%.4f,%.4f,%.4f" % [color.r, color.g, color.b, color.a]


func _fail(message: String) -> void:
	printerr("persistent_next_turn_e2e_probe: ", message)
	call_deferred("quit", 2)
