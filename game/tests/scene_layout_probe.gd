extends SceneTree


## Headless probe: after main.tscn is in the tree and has had a chance to lay out,
## report global rects of the public status/order controls (found by name under root).
##
## G94.1d also reports composition at the review resolution 1152×648: BattleView
## layout contribution with/without battle, MapView panel + background texture path.
##
## Dependency: add_child runs Main._ready → start_session(BridgeConfig.from_environment()),
## so this probe exercises a full bridge autostart even though it only asserts geometry.
## The layout pytest gate (timeout=30s) therefore needs a working default bridge/env;
## it is not a pure geometry-only fixture that skips the session.

const MAIN_SCENE_PATH := "res://scenes/main.tscn"
const SnapshotModel = preload("res://scripts/snapshot_model.gd")
const PREFIX := "SCENE_LAYOUT "
const VIEWPORT_W := 1152.0
const VIEWPORT_H := 648.0
const BACKGROUND_RES := "res://assets/strategic_map_background.png"
const STATUS_BACKGROUND_RES := "res://assets/strategic_status_background.png"
const ORDER_BAR_BACKGROUND_RES := "res://assets/order_bar_background.png"
const WINDOW_BACKGROUND_RESOURCES: Array[String] = [
	"res://assets/strategic_window_background.png",
	BACKGROUND_RES,
	STATUS_BACKGROUND_RES,
	ORDER_BAR_BACKGROUND_RES,
]

const CONTROL_NAMES: Array[String] = [
	"DateLabel",
	"StartStatusLabel",
	"RegionList",
	"ResultLabel",
	"ResultContractLabel",
	"PlayerDuchyStatusLabel",
	"PartyPositionContractLabel",
	"MoraleValueLabel",
	"SettlementsValueLabel",
	"PartiesValueLabel",
	"LastOrderStatusLabel",
	"PlayerPartyPositionLabel",
	"SelectedRegionPanel",
	"NextTurnButton",
	"DevelopButton",
	"RecruitButton",
	"MusterButton",
	"MarchButton",
	"AssaultButton",
	"SaveGameButton",
	"LoadGameButton",
]


func _init() -> void:
	call_deferred("_run")


func _run() -> void:
	# Review resolution from G94.1d / PROJECT.md (fresh party composition).
	root.size = Vector2i(int(VIEWPORT_W), int(VIEWPORT_H))

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
	if scene_root is Control:
		var main_ctrl: Control = scene_root as Control
		main_ctrl.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
		main_ctrl.size = Vector2(VIEWPORT_W, VIEWPORT_H)
	# Containers and content min-sizes settle after idle frames.
	await process_frame
	await process_frame

	# Composition gates require Main.apply_model. Do not alias with-battle
	# fields onto no-battle data — that would green-pass if apply_model vanished.
	var apply_model_ok: bool = scene_root.has_method("apply_model")
	var controls_no_battle: Dictionary = {}
	var battle_no_battle: Dictionary = {"found": false}
	var map_state: Dictionary = _map_view_state(scene_root)
	var map_with_battle: Dictionary = {"found": false}
	# OwnerLegend vs region tiles under with-battle fit (G106.1c readability).
	var map_readability_with_battle: Dictionary = {"found": false}
	var controls_with_battle: Variant = null
	var battle_with_battle: Dictionary = {"found": false}
	var battle_result_text: String = ""

	if apply_model_ok:
		# Fresh party / no battle: force public path independent of bridge residue.
		scene_root.call("apply_model", _model_without_battle())
		await process_frame
		await process_frame
		controls_no_battle = _collect_controls(scene_root)
		battle_no_battle = _battle_view_state(scene_root)
		map_state = _map_view_state(scene_root)

		scene_root.call("apply_model", _model_with_battle())
		await process_frame
		await process_frame
		controls_with_battle = _collect_controls(scene_root)
		battle_with_battle = _battle_view_state(scene_root)
		# Map may shrink under multi-hex battle fit; capture separately so the
		# composition gate does not mistake the no-battle map height for chrome+bitwa.
		map_with_battle = _map_view_state(scene_root)
		map_readability_with_battle = _map_view_readability(scene_root)
		battle_result_text = _battle_result_text(scene_root)
	else:
		# Still report live control rects for the disjoint-layout gate, but mark
		# with-battle / forced no-battle as unavailable (found:false / null).
		controls_no_battle = _collect_controls(scene_root)
		battle_no_battle = {"found": false}
		controls_with_battle = null
		battle_with_battle = {"found": false}
		map_with_battle = {"found": false}
		map_readability_with_battle = {"found": false}

	# Single no-battle key "controls" (disjoint gate + composition); with-battle
	# is separate so assertions cannot silently drift across two aliases.
	print(PREFIX, JSON.stringify({
		"viewport": {"w": VIEWPORT_W, "h": VIEWPORT_H},
		"apply_model": apply_model_ok,
		"controls": controls_no_battle,
		"controls_with_battle": controls_with_battle,
		"battle_view_no_battle": battle_no_battle,
		"battle_view_with_battle": battle_with_battle,
		"battle_result_text_with_battle": battle_result_text,
		"map_view": map_state,
		"map_view_with_battle": map_with_battle,
		"map_readability_with_battle": map_readability_with_battle,
		"status_card": _status_card_state(scene_root),
		"order_bar": _order_bar_state(scene_root),
		"window_background": _window_background_state(scene_root),
		"background_res": BACKGROUND_RES,
	}))
	quit(0)


func _collect_controls(scene_root: Node) -> Dictionary:
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
			"visible": node.visible,
		}
	return controls


func _battle_view_state(scene_root: Node) -> Dictionary:
	var battle_view: Control = scene_root.find_child("BattleView", true, false) as Control
	if battle_view == null:
		return {"found": false}
	var rect: Rect2 = battle_view.get_global_rect()
	return {
		"found": true,
		"x": rect.position.x,
		"y": rect.position.y,
		"w": rect.size.x,
		"h": rect.size.y,
		"visible": battle_view.visible,
	}


func _map_view_state(scene_root: Node) -> Dictionary:
	var map_view: Control = scene_root.find_child("MapView", true, false) as Control
	if map_view == null:
		return {
			"found": false,
			"background_path": "",
			"background_covers_panel": false,
		}
	var rect: Rect2 = map_view.get_global_rect()
	# Observable: some textured control covers the map panel with the strategic
	# background asset. Do not require a fixed node name or parent (refactor-
	# friendly); only path + coverage of the MapView rect.
	var bg: Dictionary = _strategic_background_over(map_view, rect)
	return {
		"found": true,
		"x": rect.position.x,
		"y": rect.position.y,
		"w": rect.size.x,
		"h": rect.size.y,
		"visible": map_view.visible,
		"background_path": str(bg.get("path", "")),
		"background_covers_panel": bool(bg.get("covers", false)),
	}


func _map_view_readability(scene_root: Node) -> Dictionary:
	## Public MapView readability after with-battle fit: OwnerLegend AABB must
	## not cover region tiles, and RegionTile heights (tile.h) are exposed so
	## pytest can assert ≥ ¾·BASE_TILE — map_h>1 alone is not enough.

	var map_view: Control = scene_root.find_child("MapView", true, false) as Control
	if map_view == null:
		return {"found": false}
	var legend_node: Control = map_view.find_child("OwnerLegend", true, false) as Control
	var legend_rect: Variant = null
	if legend_node != null:
		var lr: Rect2 = legend_node.get_global_rect()
		legend_rect = {
			"x": lr.position.x,
			"y": lr.position.y,
			"w": lr.size.x,
			"h": lr.size.y,
		}
	var tiles: Array = []
	for child: Node in map_view.get_children():
		if not str(child.name).begins_with("RegionTile_"):
			continue
		if not child is Control:
			continue
		var tr: Rect2 = (child as Control).get_global_rect()
		tiles.append({
			"name": str(child.name),
			"x": tr.position.x,
			"y": tr.position.y,
			"w": tr.size.x,
			"h": tr.size.y,
		})
	return {
		"found": true,
		"map_h": map_view.get_global_rect().size.y,
		"legend": legend_rect,
		"region_tiles": tiles,
	}


func _status_card_state(scene_root: Node) -> Dictionary:
	var card: Control = scene_root.find_child("StatusControls", true, false) as Control
	if card == null:
		return {"found": false}
	var rect: Rect2 = card.get_global_rect()
	var bg: Dictionary = _background_over(scene_root, rect, STATUS_BACKGROUND_RES)
	return {
		"found": true,
		"background_path": str(bg.get("path", "")),
		"background_covers_panel": bool(bg.get("covers", false)),
	}


func _order_bar_state(scene_root: Node) -> Dictionary:
	var bar: Control = scene_root.find_child("OrderControls", true, false) as Control
	if bar == null:
		return {"found": false}
	var rect: Rect2 = bar.get_global_rect()
	var bg: Dictionary = _background_over(scene_root, rect, ORDER_BAR_BACKGROUND_RES)
	return {
		"found": true,
		"background_path": str(bg.get("path", "")),
		"background_covers_panel": bool(bg.get("covers", false)),
		"button_states": _order_button_states(scene_root),
	}


func _window_background_state(scene_root: Node) -> Dictionary:
	var window_rect := Rect2(Vector2.ZERO, Vector2(VIEWPORT_W, VIEWPORT_H))
	var main_layout: Node = scene_root.find_child("MainLayout", false, false)
	var stack: Array[Node] = [scene_root]
	var best_state := {
		"found": false,
		"background_path": "",
		"background_covers_window": false,
		"visible": false,
		"covered_stretch": false,
		"below_main_layout": false,
	}
	var best_score := -1
	while not stack.is_empty():
		var node: Node = stack.pop_back()
		for child: Node in node.get_children():
			stack.append(child)
		if not node is TextureRect:
			continue
		var texture_rect := node as TextureRect
		if texture_rect.texture == null:
			continue
		var path := str(texture_rect.texture.resource_path)
		if path not in WINDOW_BACKGROUND_RESOURCES:
			continue
		var below_content := (
			main_layout != null
			and texture_rect.get_parent() == main_layout.get_parent()
			and texture_rect.get_index() < main_layout.get_index()
		)
		var covered_stretch := (
			texture_rect.stretch_mode == TextureRect.STRETCH_KEEP_ASPECT_COVERED
		)
		var covers_window := _rect_covers(
			texture_rect.get_global_rect(), window_rect, 1.0
		)
		var candidate := {
			"found": true,
			"background_path": path,
			"background_covers_window": covers_window,
			"visible": texture_rect.visible,
			"covered_stretch": covered_stretch,
			"below_main_layout": below_content,
		}
		var score := (
			int(covers_window)
			+ int(texture_rect.visible)
			+ int(covered_stretch)
			+ int(below_content)
		)
		if score > best_score:
			best_state = candidate
			best_score = score
		if score == 4:
			return candidate
	return best_state


func _order_button_states(scene_root: Node) -> Dictionary:
	var states: Dictionary = {}
	for button_name: String in [
		"NextTurnButton",
		"DevelopButton",
		"RecruitButton",
		"MusterButton",
		"MarchButton",
		"AssaultButton",
		"SaveGameButton",
		"LoadGameButton",
	]:
		var button: Button = scene_root.find_child(button_name, true, false) as Button
		if button == null:
			states[button_name] = {"found": false}
			continue
		var button_state: Dictionary = {"found": true}
		for state_name: String in ["normal", "hover", "pressed"]:
			var style: StyleBox = button.get_theme_stylebox(state_name)
			var carrier := ""
			var texture_path := ""
			var modulate_rgba: Variant = null
			if style is StyleBoxFlat:
				carrier = "StyleBoxFlat"
			elif style is StyleBoxTexture:
				var textured: StyleBoxTexture = style as StyleBoxTexture
				carrier = "StyleBoxTexture"
				if textured.texture != null:
					texture_path = textured.texture.resource_path
				modulate_rgba = [
					textured.modulate_color.r,
					textured.modulate_color.g,
					textured.modulate_color.b,
					textured.modulate_color.a,
				]
			button_state[state_name] = {
				"explicit": button.has_theme_stylebox_override(state_name),
				"carrier": carrier,
				"texture_path": texture_path,
				"modulate_rgba": modulate_rgba,
			}
		button_state["icon_modulate_rgba"] = [
			button.get_theme_color("icon_normal_color").r,
			button.get_theme_color("icon_normal_color").g,
			button.get_theme_color("icon_normal_color").b,
			button.get_theme_color("icon_normal_color").a,
		]
		states[button_name] = button_state
	return states


func _strategic_background_over(map_view: Node, map_rect: Rect2) -> Dictionary:
	# Search only the map panel subtree. A full-window sibling using the same
	# texture must not satisfy the independent MapView background contract.
	return _background_over(map_view, map_rect, BACKGROUND_RES)


func _background_over(scene_root: Node, panel_rect: Rect2, resource_path: String) -> Dictionary:
	# Walk the tree for TextureRect (Control) using BACKGROUND_RES whose global
	# rect covers the map panel (edges may match; 1px snap tolerance). Contract
	# is a UI panel background, not a Node2D Sprite2D.
	var best_path := ""
	var covers := false
	var stack: Array[Node] = [scene_root]
	while not stack.is_empty():
		var node: Node = stack.pop_back()
		for child: Node in node.get_children():
			stack.append(child)
		if not node is TextureRect:
			continue
		var tr: TextureRect = node as TextureRect
		if tr.texture == null:
			continue
		var path: String = str(tr.texture.resource_path)
		if path != resource_path:
			continue
		best_path = path
		var bg_rect: Rect2 = tr.get_global_rect()
		if bg_rect.size.x <= 0.0 or bg_rect.size.y <= 0.0:
			continue
		if _rect_covers(bg_rect, panel_rect, 1.0):
			covers = true
			break
	return {"path": best_path, "covers": covers}


func _rect_covers(outer: Rect2, inner: Rect2, tol: float) -> bool:
	return (
		outer.position.x <= inner.position.x + tol
		and outer.position.y <= inner.position.y + tol
		and outer.position.x + outer.size.x >= inner.position.x + inner.size.x - tol
		and outer.position.y + outer.size.y >= inner.position.y + inner.size.y - tol
	)


func _battle_result_text(scene_root: Node) -> String:
	var label: Label = scene_root.find_child("BattleResultLabel", true, false) as Label
	if label == null:
		return ""
	return label.text


func _model_without_battle() -> SnapshotModel:
	var model := SnapshotModel.new()
	model.year = 1
	model.month = 1
	model.player_result = "ongoing"
	model.regions = [
		{
			"name": "player lands",
			"col": 0,
			"row": 0,
			"owner": "player",
			"settlement": {"name": "Player Keep"},
		},
		{
			"name": "player outpost",
			"col": 1,
			"row": 0,
			"owner": "player",
			"settlement": {"name": "Player Outpost"},
		},
		{"name": "border", "col": 2, "row": 0, "owner": null, "settlement": null},
		{
			"name": "ai outpost",
			"col": 3,
			"row": 0,
			"owner": "ai",
			"settlement": {"name": "AI Outpost"},
		},
		{
			"name": "ai lands",
			"col": 4,
			"row": 0,
			"owner": "ai",
			"settlement": {"name": "AI Keep"},
		},
	]
	model.player_duchy_status = {"morale": 1, "settlements": 2, "parties": 1}
	model.player_party_region = "player lands"
	model.battle = null
	return model


func _model_with_battle() -> SnapshotModel:
	## Same multi-hex field as battle_view_probe / G104–G106 battle captures
	## (r∈{0,1,2}, both sides, terrain decor). A 2-hex strip under-represents
	## BattleView height after K105.1c cluster scale and lets chrome overflow
	## stay green on a toy payload.
	var model := _model_without_battle()
	model.battle = {
		"result": "attacker_win",
		"hexes": [
			{"q": 0, "r": 0, "terrain": "Plains", "side": "attacker", "hp": 10},
			{"q": 2, "r": 0, "terrain": "Plains", "side": "defender", "hp": 8},
			{"q": 0, "r": 1, "terrain": "Forest", "side": "attacker", "hp": 5},
			{"q": 0, "r": 2, "terrain": "Hills", "side": "attacker", "hp": 7},
			{"q": 2, "r": 2, "terrain": "Forest", "side": "defender", "hp": 6},
			{"q": 1, "r": 0, "terrain": "Plains", "side": "unknown", "hp": 1},
			{"q": 1, "r": 1, "terrain": "Hills", "side": "", "hp": 1},
		],
	}
	return model
