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


class ReinforceClient extends RefCounted:
	var after_model: SnapshotModel
	var changed: bool
	var monthly_action_exhausted: bool
	var game_over: bool
	var orders: Array[String] = []

	func _init(
		next_model: SnapshotModel,
		next_changed: bool = true,
		next_exhausted: bool = false,
		next_game_over: bool = false
	) -> void:
		after_model = next_model
		changed = next_changed
		monthly_action_exhausted = next_exhausted
		game_over = next_game_over

	func send_order(order_name: String, _target: String = "") -> SnapshotModel:
		orders.append(order_name)
		return after_model

	func last_order_result() -> Variant:
		var result := {"order": "reinforce", "changed": changed}
		if monthly_action_exhausted:
			result["monthly_action_exhausted"] = true
		if game_over:
			result["game_over"] = true
		return result


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

	# Exercise the public button → Main.send_order_from_bridge → apply_model path
	# on a selected region whose numbers visibly change after reinforcement.
	scene_root.apply_model(_model_reinforce_before())
	await _click_region(map_view if has_map else null, REGION_PLAYER)
	await process_frame
	await process_frame
	var reinforce_before: Dictionary = _panel_snapshot(scene_root)
	var reinforce_client := ReinforceClient.new(_model_reinforce_after())
	scene_root.bind_client(reinforce_client)
	var reinforce_button := scene_root.find_child("ReinforceButton", true, false) as Button
	var reinforce_pressed := reinforce_button != null
	if reinforce_button != null:
		reinforce_button.emit_signal("pressed")
	await process_frame
	await process_frame
	var reinforce_after: Dictionary = _panel_snapshot(scene_root)

	# A second click after the successful reinforce must preserve the bridge's
	# exhausted-month reason even though the selected party now has garrison 0.
	var exhausted_client := ReinforceClient.new(_model_reinforce_after(), false, true)
	scene_root.bind_client(exhausted_client)
	if reinforce_button != null:
		reinforce_button.emit_signal("pressed")
	await process_frame
	await process_frame
	var exhausted_status_label := scene_root.find_child("LastOrderStatusLabel", true, false) as Label
	var exhausted_status := {
		"text": "" if exhausted_status_label == null else exhausted_status_label.text,
		"visible": exhausted_status_label != null and exhausted_status_label.is_visible_in_tree(),
	}

	# Exercise the real UI on an ineffective reinforce: the selected party is
	# present, but the current snapshot shows no settlement garrison to absorb.
	scene_root.apply_model(_model_reinforce_no_garrison())
	await process_frame
	await process_frame
	var ineffective_client := ReinforceClient.new(_model_reinforce_no_garrison(), false)
	scene_root.bind_client(ineffective_client)
	var ineffective_button := scene_root.find_child("ReinforceButton", true, false) as Button
	var ineffective_pressed := ineffective_button != null
	if ineffective_button != null:
		ineffective_button.emit_signal("pressed")
	await process_frame
	await process_frame
	var ineffective_status_label := scene_root.find_child("LastOrderStatusLabel", true, false) as Label
	var ineffective_status := {
		"text": "" if ineffective_status_label == null else ineffective_status_label.text,
		"visible": ineffective_status_label != null and ineffective_status_label.is_visible_in_tree(),
	}
	var ineffective_after: Dictionary = _panel_snapshot(scene_root)

	# A zero-garrison foreign settlement must not be reported as a missing
	# garrison: the snapshot carries both party and settlement owners.
	scene_root.apply_model(_model_reinforce_foreign_settlement())
	await process_frame
	await process_frame
	var foreign_client := ReinforceClient.new(_model_reinforce_foreign_settlement(), false)
	scene_root.bind_client(foreign_client)
	var foreign_button := scene_root.find_child("ReinforceButton", true, false) as Button
	var foreign_pressed := foreign_button != null
	if foreign_button != null:
		foreign_button.emit_signal("pressed")
	await process_frame
	await process_frame
	var foreign_status_label := scene_root.find_child("LastOrderStatusLabel", true, false) as Label
	var foreign_status := {
		"text": "" if foreign_status_label == null else foreign_status_label.text,
		"visible": foreign_status_label != null and foreign_status_label.is_visible_in_tree(),
	}

	# game_over must win over every contextual changed:false explanation.
	scene_root.apply_model(_model_reinforce_no_garrison())
	await process_frame
	await process_frame
	var game_over_client := ReinforceClient.new(_model_reinforce_no_garrison(), false, false, true)
	scene_root.bind_client(game_over_client)
	var game_over_button := scene_root.find_child("ReinforceButton", true, false) as Button
	if game_over_button != null:
		game_over_button.emit_signal("pressed")
	await process_frame
	await process_frame
	var game_over_status_label := scene_root.find_child("LastOrderStatusLabel", true, false) as Label
	var game_over_status := {
		"text": "" if game_over_status_label == null else game_over_status_label.text,
		"visible": game_over_status_label != null and game_over_status_label.is_visible_in_tree(),
	}

	# The order acts at player_party_region, not at an arbitrary selected region.
	scene_root.apply_model(_model_reinforce_selection_mismatch())
	await _click_region(map_view if has_map else null, REGION_AI)
	await process_frame
	await process_frame
	var mismatch_client := ReinforceClient.new(_model_reinforce_selection_mismatch(), false)
	scene_root.bind_client(mismatch_client)
	var mismatch_button := scene_root.find_child("ReinforceButton", true, false) as Button
	if mismatch_button != null:
		mismatch_button.emit_signal("pressed")
	await process_frame
	await process_frame
	var mismatch_status_label := scene_root.find_child("LastOrderStatusLabel", true, false) as Label
	var mismatch_status := {
		"text": "" if mismatch_status_label == null else mismatch_status_label.text,
		"visible": mismatch_status_label != null and mismatch_status_label.is_visible_in_tree(),
	}

	# Missing party and missing settlement are distinct snapshot reasons for a
	# failed reinforce; neither should fall back to the generic no-op status.
	scene_root.apply_model(_model_reinforce_no_party())
	await process_frame
	await process_frame
	var no_party_client := ReinforceClient.new(_model_reinforce_no_party(), false)
	scene_root.bind_client(no_party_client)
	var no_party_button := scene_root.find_child("ReinforceButton", true, false) as Button
	var no_party_pressed := no_party_button != null
	if no_party_button != null:
		no_party_button.emit_signal("pressed")
	await process_frame
	await process_frame
	var no_party_status_label := scene_root.find_child("LastOrderStatusLabel", true, false) as Label
	var no_party_status := {
		"text": "" if no_party_status_label == null else no_party_status_label.text,
		"visible": no_party_status_label != null and no_party_status_label.is_visible_in_tree(),
	}

	scene_root.apply_model(_model_reinforce_no_settlement())
	await process_frame
	await process_frame
	var no_settlement_client := ReinforceClient.new(_model_reinforce_no_settlement(), false)
	scene_root.bind_client(no_settlement_client)
	var no_settlement_button := scene_root.find_child("ReinforceButton", true, false) as Button
	var no_settlement_pressed := no_settlement_button != null
	if no_settlement_button != null:
		no_settlement_button.emit_signal("pressed")
	await process_frame
	await process_frame
	var no_settlement_status_label := scene_root.find_child("LastOrderStatusLabel", true, false) as Label
	var no_settlement_status := {
		"text": "" if no_settlement_status_label == null else no_settlement_status_label.text,
		"visible": no_settlement_status_label != null and no_settlement_status_label.is_visible_in_tree(),
	}

	# A party of eight cannot absorb a five-unit garrison: the resulting size
	# would exceed the core's limit of twelve. The UI must explain this no-op
	# separately from an empty-garrison no-op.
	scene_root.apply_model(_model_reinforce_capacity_limit())
	await process_frame
	await process_frame
	var capacity_client := ReinforceClient.new(_model_reinforce_capacity_limit(), false)
	scene_root.bind_client(capacity_client)
	var capacity_button := scene_root.find_child("ReinforceButton", true, false) as Button
	var capacity_pressed := capacity_button != null
	if capacity_button != null:
		capacity_button.emit_signal("pressed")
	await process_frame
	await process_frame
	var capacity_status_label := scene_root.find_child("LastOrderStatusLabel", true, false) as Label
	var capacity_status := {
		"text": "" if capacity_status_label == null else capacity_status_label.text,
		"visible": capacity_status_label != null and capacity_status_label.is_visible_in_tree(),
	}

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
		"reinforce": {
			"button_found": reinforce_button != null,
			"pressed": reinforce_pressed,
			"orders": reinforce_client.orders,
			"before": reinforce_before,
			"after": reinforce_after,
		},
		"reinforce_exhausted": {
			"orders": exhausted_client.orders,
			"status": exhausted_status,
		},
		"reinforce_ineffective": {
			"button_found": ineffective_button != null,
			"pressed": ineffective_pressed,
			"orders": ineffective_client.orders,
			"status": ineffective_status,
			"after": ineffective_after,
		},
		"reinforce_foreign_settlement": {
			"button_found": foreign_button != null,
			"pressed": foreign_pressed,
			"orders": foreign_client.orders,
			"status": foreign_status,
		},
		"reinforce_game_over": {
			"orders": game_over_client.orders,
			"status": game_over_status,
		},
		"reinforce_selection_mismatch": {
			"button_found": mismatch_button != null,
			"orders": mismatch_client.orders,
			"actual_party_region": REGION_PLAYER,
			"selected_region": REGION_AI,
			"status": mismatch_status,
		},
		"reinforce_no_party": {
			"button_found": no_party_button != null,
			"pressed": no_party_pressed,
			"orders": no_party_client.orders,
			"status": no_party_status,
		},
		"reinforce_no_settlement": {
			"button_found": no_settlement_button != null,
			"pressed": no_settlement_pressed,
			"orders": no_settlement_client.orders,
			"status": no_settlement_status,
		},
		"reinforce_capacity_limit": {
			"button_found": capacity_button != null,
			"pressed": capacity_pressed,
			"orders": capacity_client.orders,
			"status": capacity_status,
		},
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


func _model_reinforce_before() -> SnapshotModel:
	return _model([_reinforce_player_region(5, 5), _neutral_region()])


func _model_reinforce_after() -> SnapshotModel:
	return _model([_reinforce_player_region(10, 0), _neutral_region()])


func _model_reinforce_no_garrison() -> SnapshotModel:
	return _model([_reinforce_player_region(5, 0), _neutral_region()])


func _model_reinforce_foreign_settlement() -> SnapshotModel:
	var region := _reinforce_player_region(5, 0)
	region["settlement"]["owner"] = "ai"
	return _model([region, _neutral_region()])


func _model_reinforce_selection_mismatch() -> SnapshotModel:
	return _model([_reinforce_player_region(5, 5), _zero_garrison_ai_region()])


func _model_reinforce_no_party() -> SnapshotModel:
	var model := _model([_reinforce_player_region_without_party(), _neutral_region()])
	model.player_party_region = null
	return model


func _model_reinforce_no_settlement() -> SnapshotModel:
	return _model([_reinforce_player_region_without_settlement(), _neutral_region()])


func _model_reinforce_capacity_limit() -> SnapshotModel:
	return _model([_reinforce_player_region(8, 5), _neutral_region()])


func _reinforce_player_region(party_size: int, garrison: int) -> Dictionary:
	return {
		"name": REGION_PLAYER,
		"col": 0,
		"row": 0,
		"owner": "player",
		"settlement": {
			"name": "Player Outpost",
			"garrison": garrison,
		},
		"party": {
			"owner": "player",
			"size": party_size,
			"hp": 73 if party_size == 5 else 98,
		},
	}


func _reinforce_player_region_without_party() -> Dictionary:
	var region := _reinforce_player_region(5, 5)
	region["party"] = null
	return region


func _reinforce_player_region_without_settlement() -> Dictionary:
	var region := _reinforce_player_region(5, 5)
	region["settlement"] = null
	return region


func _zero_garrison_ai_region() -> Dictionary:
	return {
		"name": REGION_AI,
		"col": 2,
		"row": 0,
		"owner": "ai",
		"settlement": {
			"name": "AI Outpost",
			"garrison": 0,
		},
		"party": null,
	}


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
