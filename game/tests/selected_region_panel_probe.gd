extends SceneTree


## Headless probe for G97.1e: strategic panel „Wybrany region” presents the
## clicked snapshot region (name / owner / settlement / party) in Polish.
## Observes public Main scene controls only — no private MapView fields.

const MAIN_SCENE_PATH := "res://scenes/main.tscn"
const SnapshotModel = preload("res://scripts/snapshot_model.gd")
const PartyMapMark = preload("res://tests/party_map_mark_helpers.gd")
const PREFIX := "SELECTED_REGION_PANEL "
const VIEWPORT_W := 1152.0
const VIEWPORT_H := 648.0

const REGION_PLAYER := "Gród Własny"
const REGION_NEUTRAL := "Puste Pole"
const REGION_AI := "Twierdza AI"
const SETTLEMENT_PLAYER := "Player Keep"
const SETTLEMENT_AI := "AI Outpost"
const SETTLEMENT_AI_REFRESHED := "AI Keep"

# Fixture strengths: party sizes/hp follow the values measured for task-626
# (new_session(73)); the player garrison is a deliberate 0 edge case, so the
# panel must not drop it as a falsy value. The panel must carry all of these
# through, and the refreshed model must move the AI garrison.
const PLAYER_PARTY_SIZE := 5
const PLAYER_PARTY_HP := 73
const AI_PARTY_SIZE := 1
const AI_PARTY_HP := 25
const SETTLEMENT_PLAYER_GARRISON := 0
const SETTLEMENT_AI_GARRISON := 1
const SETTLEMENT_AI_GARRISON_REFRESHED := 4


func _init() -> void:
	call_deferred("_run")


func _run() -> void:
	root.size = Vector2i(int(VIEWPORT_W), int(VIEWPORT_H))

	var scene: PackedScene = ResourceLoader.load(MAIN_SCENE_PATH) as PackedScene
	if scene == null:
		_fail("cannot load main scene")
		return
	var scene_root: Control = scene.instantiate() as Control
	if scene_root == null:
		_fail("cannot instantiate main scene")
		return

	root.add_child(scene_root)
	scene_root.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	scene_root.size = Vector2(VIEWPORT_W, VIEWPORT_H)
	await process_frame
	await process_frame

	if not scene_root.has_method("apply_model"):
		print(PREFIX, JSON.stringify({"available": false, "reason": "no apply_model"}))
		quit(0)
		return

	var map_view: Node = scene_root.find_child("MapView", true, false)
	var has_map: bool = map_view != null and map_view.has_method("render_model")

	scene_root.apply_model(_model_full())
	await process_frame
	await process_frame

	var empty_before: Dictionary = _panel_snapshot(scene_root)
	if not empty_before.get("found", false):
		print(PREFIX, JSON.stringify({
			"available": true,
			"panel_found": false,
			"has_map_view": has_map,
			"empty_before": empty_before,
		}))
		quit(0)
		return

	var emitted: Array = []
	if has_map and map_view.has_signal("region_selected"):
		map_view.connect(
			"region_selected",
			func(region_name: Variant) -> void:
				emitted.append(str(region_name))
		)

	await _click_region(map_view if has_map else null, REGION_PLAYER)
	await process_frame
	await process_frame
	var after_player: Dictionary = _panel_snapshot(scene_root)
	var emitted_after_player: Array = emitted.duplicate()

	await _click_region(map_view if has_map else null, REGION_NEUTRAL)
	await process_frame
	await process_frame
	var after_neutral: Dictionary = _panel_snapshot(scene_root)
	var emitted_after_neutral: Array = emitted.duplicate()

	await _click_region(map_view if has_map else null, REGION_AI)
	await process_frame
	await process_frame
	var after_ai: Dictionary = _panel_snapshot(scene_root)
	var emitted_after_ai: Array = emitted.duplicate()

	# Same selection name; snapshot fields change (refresh must re-read model).
	scene_root.apply_model(_model_ai_refreshed())
	await process_frame
	await process_frame
	var after_refresh: Dictionary = _panel_snapshot(scene_root)

	# Selected region disappears from snapshot → unambiguous empty state.
	scene_root.apply_model(_model_without_ai())
	await process_frame
	await process_frame
	var after_gone: Dictionary = _panel_snapshot(scene_root)

	print(PREFIX, JSON.stringify({
		"available": true,
		"panel_found": true,
		"has_map_view": has_map,
		"has_region_selected_signal": has_map and map_view.has_signal("region_selected"),
		"empty_before": empty_before,
		"after_player": after_player,
		"after_neutral": after_neutral,
		"after_ai": after_ai,
		"after_refresh": after_refresh,
		"after_gone": after_gone,
		"emitted_after_player": emitted_after_player,
		"emitted_after_neutral": emitted_after_neutral,
		"emitted_after_ai": emitted_after_ai,
		"regions": {
			"player": REGION_PLAYER,
			"neutral": REGION_NEUTRAL,
			"ai": REGION_AI,
			"settlement_player": SETTLEMENT_PLAYER,
			"settlement_ai": SETTLEMENT_AI,
			"settlement_ai_refreshed": SETTLEMENT_AI_REFRESHED,
		},
		"strengths": {
			"player_party_size": PLAYER_PARTY_SIZE,
			"player_party_hp": PLAYER_PARTY_HP,
			"ai_party_size": AI_PARTY_SIZE,
			"ai_party_hp": AI_PARTY_HP,
			"settlement_player_garrison": SETTLEMENT_PLAYER_GARRISON,
			"settlement_ai_garrison": SETTLEMENT_AI_GARRISON,
			"settlement_ai_garrison_refreshed": SETTLEMENT_AI_GARRISON_REFRESHED,
		},
	}))
	quit(0)


func _model_full() -> SnapshotModel:
	return _model([
		_player_region(),
		_neutral_region(),
		{
			"name": REGION_AI,
			"col": 2,
			"row": 0,
			"owner": "ai",
			"settlement": {
				"name": SETTLEMENT_AI,
				"garrison": SETTLEMENT_AI_GARRISON,
			},
			"party": {
				"owner": "ai",
				"size": AI_PARTY_SIZE,
				"hp": AI_PARTY_HP,
			},
		},
	])


func _model_ai_refreshed() -> SnapshotModel:
	# Same selection name, moved numbers: settlement renamed and garrison
	# changed, party gone. Refresh must re-read all of it.
	return _model([
		_player_region(),
		_neutral_region(),
		{
			"name": REGION_AI,
			"col": 2,
			"row": 0,
			"owner": "ai",
			"settlement": {
				"name": SETTLEMENT_AI_REFRESHED,
				"garrison": SETTLEMENT_AI_GARRISON_REFRESHED,
			},
			"party": null,
		},
	])


func _model_without_ai() -> SnapshotModel:
	return _model([_player_region(), _neutral_region()])


func _player_region() -> Dictionary:
	return {
		"name": REGION_PLAYER,
		"col": 0,
		"row": 0,
		"owner": "player",
		"settlement": {
			"name": SETTLEMENT_PLAYER,
			"garrison": SETTLEMENT_PLAYER_GARRISON,
		},
		"party": {
			"owner": "player",
			"size": PLAYER_PARTY_SIZE,
			"hp": PLAYER_PARTY_HP,
		},
	}


func _neutral_region() -> Dictionary:
	return {
		"name": REGION_NEUTRAL,
		"col": 1,
		"row": 0,
		"owner": null,
		"settlement": null,
		"party": null,
	}


func _model(regions: Array) -> SnapshotModel:
	var model := SnapshotModel.new()
	model.year = 1
	model.month = 1
	model.player_result = "ongoing"
	model.regions = regions
	model.player_party_region = REGION_PLAYER
	return model


func _panel_snapshot(scene_root: Node) -> Dictionary:
	# Public carriers: unique SelectedRegionLabel, SelectedRegionPanel (text
	# concat of descendant Labels), or any Label whose text names the panel.
	var label: Label = scene_root.find_child("SelectedRegionLabel", true, false) as Label
	if label != null:
		return {
			"found": true,
			"carrier": "SelectedRegionLabel",
			"text": label.text,
			"visible": label.is_visible_in_tree(),
		}

	var panel: Node = scene_root.find_child("SelectedRegionPanel", true, false)
	if panel != null:
		var joined: String = _join_label_texts(panel)
		var background_path := ""
		if panel is PanelContainer:
			var panel_style: StyleBox = (panel as PanelContainer).get_theme_stylebox("panel")
			if panel_style is StyleBoxTexture:
				var panel_texture: Texture2D = (panel_style as StyleBoxTexture).texture
				if panel_texture != null:
					background_path = panel_texture.resource_path
		return {
			"found": true,
			"carrier": "SelectedRegionPanel",
			"text": joined,
			"label_texts": _label_texts(panel),
			"visible": panel is CanvasItem and (panel as CanvasItem).is_visible_in_tree(),
			"background_path": background_path,
			"visible_visual_paths": _visible_visual_paths(panel),
		}

	var titled: Label = _find_label_containing(scene_root, "Wybrany region")
	if titled != null:
		return {
			"found": true,
			"carrier": str(titled.name),
			"text": titled.text,
			"visible": titled.is_visible_in_tree(),
		}

	return {"found": false, "carrier": "", "text": "", "visible": false}


func _visible_visual_paths(root_node: Node) -> Array[String]:
	# Any visible textured descendant counts, regardless of its node name or
	# exact scene structure.
	var paths: Array[String] = []
	var stack: Array[Node] = [root_node]
	while not stack.is_empty():
		var node: Node = stack.pop_back()
		for child: Node in node.get_children():
			stack.append(child)
		if not node is TextureRect:
			continue
		var visual := node as TextureRect
		if not visual.is_visible_in_tree() or visual.texture == null:
			continue
		var path := str(visual.texture.resource_path)
		if not path.is_empty():
			paths.append(path)
	return paths


func _join_label_texts(root: Node) -> String:
	return "\n".join(_label_texts(root))


func _label_texts(root: Node) -> Array[String]:
	var parts: Array[String] = []
	_collect_label_texts(root, parts)
	return parts


func _collect_label_texts(node: Node, parts: Array[String]) -> void:
	if node is Label:
		var label: Label = node as Label
		var text: String = label.text
		if label.is_visible_in_tree() and not text.is_empty():
			parts.append(text)
	for child: Node in node.get_children():
		_collect_label_texts(child, parts)


func _find_label_containing(root: Node, needle: String) -> Label:
	if root is Label:
		var label: Label = root as Label
		if label.text.findn(needle) >= 0:
			return label
	for child: Node in root.get_children():
		var found: Label = _find_label_containing(child, needle)
		if found != null:
			return found
	return null


func _click_region(map_view: Node, region_name: String) -> void:
	if map_view == null:
		return
	var tile: Control = _find_region_tile(map_view, region_name)
	if tile == null:
		return
	var center: Vector2 = tile.get_global_rect().get_center()
	var press := InputEventMouseButton.new()
	press.button_index = MOUSE_BUTTON_LEFT
	press.pressed = true
	press.position = center
	press.global_position = center
	var release := InputEventMouseButton.new()
	release.button_index = MOUSE_BUTTON_LEFT
	release.pressed = false
	release.position = center
	release.global_position = center
	var vp: Viewport = tile.get_viewport()
	if vp == null:
		return
	vp.push_input(press)
	vp.push_input(release)


func _find_region_tile(map_view: Node, region_name: String) -> Control:
	var label: Label = PartyMapMark.find_label_with_text(map_view, region_name)
	if label == null:
		return null
	return PartyMapMark.tile_control(label, map_view)


func _fail(message: String) -> void:
	printerr("selected_region_panel_probe: ", message)
	quit(1)
