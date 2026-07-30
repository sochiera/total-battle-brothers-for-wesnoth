extends RefCounted


## Shared scaffolding for live MapView + order-button e2e probes.
## Keeps node names, observation shape and click input identical across
## legal_targeted_move_e2e_probe and blocked_enemy_settlement_move_e2e_probe
## so UI renames cannot drift between those sequences.

const MAIN_SCENE_PATH := "res://scenes/main.tscn"
const PartyMapMark = preload("res://tests/party_map_mark_helpers.gd")
const MapTargetFrame = preload("res://tests/map_target_frame_helpers.gd")


static func instantiate_scene(tree: SceneTree, viewport_w: float, viewport_h: float) -> Control:
	var scene := ResourceLoader.load(MAIN_SCENE_PATH) as PackedScene
	if scene == null:
		_abort(tree, "cannot load main scene")
		return null
	var scene_root := scene.instantiate() as Control
	if scene_root == null:
		_abort(tree, "cannot instantiate main scene")
		return null
	tree.root.add_child(scene_root)
	scene_root.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	scene_root.size = Vector2(viewport_w, viewport_h)
	return scene_root


static func press(tree: SceneTree, scene_root: Control, button_name: String) -> bool:
	var button := scene_root.find_child(button_name, true, false) as Button
	if button == null:
		_abort(tree, "missing %s" % button_name)
		return false
	button.emit_signal("pressed")
	return true


static func observe(scene_root: Control, map_view: Node) -> Dictionary:
	var position_label := scene_root.find_child("PlayerPartyPositionLabel", true, false) as Label
	var status_label := scene_root.find_child("LastOrderStatusLabel", true, false) as Label
	var panel_label := scene_root.find_child("SelectedRegionDetailsLabel", true, false) as Label
	var march_button := scene_root.find_child("MarchButton", true, false) as Button
	var region_names: Array[String] = PartyMapMark.region_names_from_map(map_view)
	var selected := ""
	if map_view.get("selected_region_name") != null:
		selected = str(map_view.get("selected_region_name"))
	return {
		"position_label": "" if position_label == null else position_label.text,
		"order_status": "" if status_label == null else status_label.text,
		"panel_text": "" if panel_label == null else panel_label.text,
		"march_label": "" if march_button == null else march_button.text,
		"selected_region_name": selected,
		"marked_regions": PartyMapMark.marked_party_regions(map_view, region_names),
		"marker_count": PartyMapMark.count_party_markers(map_view),
		"frame_count": MapTargetFrame.count_target_frames(map_view),
		"framed_regions": MapTargetFrame.framed_regions(map_view, region_names),
		"region_names": region_names,
	}


static func click_region(tree: SceneTree, map_view: Node, region_name: String) -> bool:
	var tile: Control = find_region_tile(map_view, region_name)
	if tile == null:
		_abort(tree, "missing tile for %s" % region_name)
		return false
	var center: Vector2 = tile.get_global_rect().get_center()
	var press_ev := InputEventMouseButton.new()
	press_ev.button_index = MOUSE_BUTTON_LEFT
	press_ev.pressed = true
	press_ev.position = center
	press_ev.global_position = center
	var release_ev := InputEventMouseButton.new()
	release_ev.button_index = MOUSE_BUTTON_LEFT
	release_ev.pressed = false
	release_ev.position = center
	release_ev.global_position = center
	var vp: Viewport = tile.get_viewport()
	if vp == null:
		_abort(tree, "missing viewport for tile %s" % region_name)
		return false
	vp.push_input(press_ev)
	vp.push_input(release_ev)
	return true


static func find_region_tile(map_view: Node, region_name: String) -> Control:
	var label: Label = PartyMapMark.find_label_with_text(map_view, region_name)
	if label == null:
		return null
	return PartyMapMark.tile_control(label, map_view)


static func _abort(tree: SceneTree, message: String) -> void:
	printerr("map_order_e2e_helpers: ", message)
	tree.quit(2)
