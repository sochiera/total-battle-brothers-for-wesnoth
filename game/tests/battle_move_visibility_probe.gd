extends SceneTree


## Visual probe for G121.1e: pending move_targets must change the rendered
## battle board, follow refreshed public snapshots, stay legible next to
## attack_targets, and leave unit status readable.

const MAIN_SCENE_PATH := "res://scenes/main.tscn"
const SnapshotModel = preload("res://scripts/snapshot_model.gd")
const PREFIX := "BATTLE_MOVE_VISIBILITY "
const VIEWPORT_W := 1152.0
const VIEWPORT_H := 648.0
const VISUAL_PROOF_PATH := "res://screenshots/task-689-battle-move-visibility-1152x648.png"


func _init() -> void:
	call_deferred("_run")


func _run() -> void:
	root.size = Vector2i(int(VIEWPORT_W), int(VIEWPORT_H))
	var scene := ResourceLoader.load(MAIN_SCENE_PATH) as PackedScene
	if scene == null:
		_fail("cannot load main scene")
		return
	var scene_root := scene.instantiate() as Control
	if scene_root == null:
		_fail("cannot instantiate main scene")
		return
	root.add_child(scene_root)
	scene_root.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	scene_root.size = Vector2(VIEWPORT_W, VIEWPORT_H)
	await process_frame
	await process_frame

	var battle_view := scene_root.find_child("BattleView", true, false) as Control
	if battle_view == null:
		_fail("missing BattleView")
		return

	# Two active units per side plus free destinations make accidental whole-side
	# highlighting, ghost intents, and destination markers observable.
	var hexes: Array = [
		{"q": 0, "r": 0, "terrain": "Plains", "side": "attacker", "hp": 10, "stunned": false},
		{"q": 1, "r": 0, "terrain": "Forest", "side": "attacker", "hp": 9, "stunned": false},
		{"q": 2, "r": 0, "terrain": "Hills", "side": "defender", "hp": 8, "stunned": false},
		{"q": 3, "r": 0, "terrain": "Plains", "side": "defender", "hp": 7, "stunned": false},
	]
	var first_moves: Array = [{
		"mover": {"q": 0, "r": 0},
		"destination": {"q": 0, "r": 1},
	}]
	var second_moves: Array = [{
		"mover": {"q": 1, "r": 0},
		"destination": {"q": 1, "r": 1},
	}]
	var combined_moves: Array = [{
		"mover": {"q": 0, "r": 0},
		"destination": {"q": 0, "r": 1},
	}]
	var combined_targets: Array = [{
		"attacker": {"q": 1, "r": 0},
		"target": {"q": 3, "r": 0},
	}]

	scene_root.apply_model(_model_with_battle(hexes, [], []))
	await _settle_frame()
	battle_view.call("clear_vertical_budget")
	await _settle_frame()
	var baseline_image := _viewport_image()
	var baseline_tiles := _collect_tiles(battle_view, hexes, baseline_image)

	scene_root.apply_model(_model_with_battle(hexes, [], first_moves))
	await _settle_frame()
	var first_image := _viewport_image()
	var first_tiles := _collect_tiles(battle_view, hexes, first_image)
	var first_pair := _pair_coords(first_moves)
	var first_marker_colors := _changed_color_means(
		baseline_image, first_image, battle_view, first_moves
	)
	# Diff while this phase's free destination tiles still exist.
	var first_diff_by_hex := _diff_by_coords(
		baseline_image, first_image, battle_view, first_pair
	)
	if not _save_image(first_image, VISUAL_PROOF_PATH):
		return

	scene_root.apply_model(_model_with_battle(hexes, [], []))
	await _settle_frame()
	var empty_image := _viewport_image()
	var empty_tiles := _collect_tiles(battle_view, hexes, empty_image)
	# Free destination tiles are gone; reuse first-phase rects (same layout as
	# baseline/empty — no extra destination row shift between those two).
	var empty_diff_by_hex := _diff_by_coords_with_fallback(
		baseline_image, empty_image, battle_view, first_pair, first_diff_by_hex
	)

	scene_root.apply_model(_model_with_battle(hexes, [], second_moves))
	await _settle_frame()
	var second_image := _viewport_image()
	var second_tiles := _collect_tiles(battle_view, hexes, second_image)
	var second_pair := _pair_coords(second_moves)
	var second_diff_by_hex := _diff_by_coords(
		baseline_image, second_image, battle_view, second_pair
	)
	# Free destinations recenter the cluster and can change layout scale, so
	# absolute or cross-phase tile-content diffs are not comparable. Detect a
	# leftover move highlight by the public marker rim colors on the live tile;
	# a removed free destination reports present=false with zero marker pixels.
	var second_old_pair_diff := _move_marker_pixels_for_coords(
		second_image, battle_view, first_pair
	)

	scene_root.apply_model(_model_with_battle(hexes, combined_targets, combined_moves))
	await _settle_frame()
	var combined_image := _viewport_image()
	var combined_move_colors := _changed_color_means(
		baseline_image, combined_image, battle_view, combined_moves
	)
	var combined_attack_coords: Array = [{"q": 1, "r": 0}, {"q": 3, "r": 0}]
	var combined_attack_colors := _changed_color_means_for_hexes(
		baseline_image,
		combined_image,
		battle_view,
		combined_attack_coords,
	)
	var combined_move_diff := _diff_by_coords(
		baseline_image, combined_image, battle_view, _pair_coords(combined_moves)
	)
	var combined_attack_diff := _diff_by_coords(
		baseline_image,
		combined_image,
		battle_view,
		combined_attack_coords,
	)

	var projected_moves := _project_move_targets_from_bridge(hexes, first_moves)

	print(PREFIX, JSON.stringify({
		"battle_result_text": _label_text(scene_root, "BattleResultLabel"),
		"battle_view_visible": battle_view.is_visible_in_tree(),
		"hexes": hexes,
		"first_moves": first_moves,
		"second_moves": second_moves,
		"combined_moves": combined_moves,
		"combined_targets": combined_targets,
		"projected_move_targets": projected_moves,
		"first_marker_colors": first_marker_colors,
		"combined_move_colors": combined_move_colors,
		"combined_attack_colors": combined_attack_colors,
		"polish_ui": _polish_ui(scene_root),
		"visual_proof": {
			"path": VISUAL_PROOF_PATH,
			"width": first_image.get_width(),
			"height": first_image.get_height(),
		},
		"baseline_tiles": baseline_tiles,
		"first_tiles": first_tiles,
		"empty_tiles": empty_tiles,
		"second_tiles": second_tiles,
		"first_diff_by_hex": first_diff_by_hex,
		"empty_diff_by_hex": empty_diff_by_hex,
		"second_diff_by_hex": second_diff_by_hex,
		"second_old_pair_diff": second_old_pair_diff,
		"combined_move_diff": combined_move_diff,
		"combined_attack_diff": combined_attack_diff,
	}))
	quit(0)


func _settle_frame() -> void:
	await process_frame
	await process_frame


func _model_with_battle(hexes: Array, targets: Array, moves: Array) -> SnapshotModel:
	var model := SnapshotModel.new()
	model.year = 1
	model.month = 1
	model.player_result = "ongoing"
	model.regions = []
	model.battle = {"result": null, "hexes": hexes}
	if not targets.is_empty():
		model.battle["attack_targets"] = targets.duplicate(true)
	if not moves.is_empty():
		model.battle["move_targets"] = moves.duplicate(true)
	return model


func _project_move_targets_from_bridge(hexes: Array, moves: Array) -> Array:
	## Live bridge path builds SnapshotModel.from_response; move_targets must
	## survive that adapter or the view never sees the public intent.
	var snapshot := {
		"calendar": {"year": 1, "month": 1},
		"map": {"regions": []},
		"result": {"player_result": "ongoing"},
		"battle": {
			"result": null,
			"hexes": hexes,
			"move_targets": moves,
		},
	}
	var model := SnapshotModel.from_response({"ok": true, "snapshot": snapshot})
	if model == null or not model.battle is Dictionary:
		return []
	return model.battle.get("move_targets", [])


func _pair_coords(moves: Array) -> Array:
	var coords: Array = []
	for pair: Variant in moves:
		if not pair is Dictionary:
			continue
		var mover: Variant = pair.get("mover")
		var destination: Variant = pair.get("destination")
		if mover is Dictionary:
			coords.append({"q": int(mover.get("q", 0)), "r": int(mover.get("r", 0))})
		if destination is Dictionary:
			coords.append({
				"q": int(destination.get("q", 0)),
				"r": int(destination.get("r", 0)),
			})
	return coords


func _viewport_image() -> Image:
	return root.get_viewport().get_texture().get_image()


func _save_image(image: Image, res_path: String) -> bool:
	if image == null:
		printerr("battle_move_visibility_probe: viewport image is null")
		quit(1)
		return false
	if image.get_width() != int(VIEWPORT_W) or image.get_height() != int(VIEWPORT_H):
		printerr(
			"battle_move_visibility_probe: unexpected viewport size %sx%s"
			% [image.get_width(), image.get_height()]
		)
		quit(1)
		return false
	var absolute_path := ProjectSettings.globalize_path(res_path)
	if image.save_png(absolute_path) != OK:
		printerr("battle_move_visibility_probe: cannot save visual proof ", absolute_path)
		quit(1)
		return false
	return true


func _label_text(scene_root: Node, node_name: String) -> String:
	var node := scene_root.find_child(node_name, true, false)
	if node is Label:
		return (node as Label).text.strip_edges()
	if node is Button:
		return (node as Button).text.strip_edges()
	return ""


func _polish_ui(scene_root: Node) -> Dictionary:
	var result := {}
	for node_name in ["BattleHeaderLabel", "BattleAdvanceButton", "BattleAutoButton"]:
		var node := scene_root.find_child(node_name, true, false)
		var control := node as Control
		result[node_name] = {
			"text": _label_text(scene_root, node_name),
			"visible": control != null and control.is_visible_in_tree(),
		}
	return result


func _find_hex_tile(battle_view: Node, q: int, r: int) -> Control:
	var tile := battle_view.find_child("HexTile_%d_%d" % [q, r], true, false)
	return tile as Control


func _collect_tiles(battle_view: Node, hexes: Array, image: Image) -> Array:
	var tiles: Array = []
	for hex: Variant in hexes:
		if not hex is Dictionary:
			continue
		var q := int(hex.get("q", 0))
		var r := int(hex.get("r", 0))
		var tile := _find_hex_tile(battle_view, q, r)
		if tile == null:
			continue
		var rect := tile.get_global_rect()
		var labels := _collect_labels(tile)
		for label: Variant in labels:
			if label is Dictionary:
				label["ink_pixels"] = _dark_pixels(image, label["rect"])
		tiles.append({
			"q": q,
			"r": r,
			"side": str(hex.get("side", "")),
			"rect": _rect_dict(rect),
			"labels": labels,
		})
	return tiles


func _collect_labels(node: Node) -> Array:
	var labels: Array = []
	if node is Label:
		var label := node as Label
		var rect := label.get_global_rect()
		labels.append({
			"text": label.text.strip_edges(),
			"visible": label.is_visible_in_tree(),
			"rect": _rect_dict(rect),
		})
	for child: Node in node.get_children():
		labels.append_array(_collect_labels(child))
	return labels


func _rect_dict(rect: Rect2) -> Dictionary:
	return {
		"x": rect.position.x,
		"y": rect.position.y,
		"w": rect.size.x,
		"h": rect.size.y,
	}


func _dark_pixels(image: Image, rect: Dictionary) -> int:
	var left := maxi(0, floori(float(rect.get("x", 0.0))))
	var top := maxi(0, floori(float(rect.get("y", 0.0))))
	var right := mini(
		image.get_width(),
		ceili(float(rect.get("x", 0.0)) + float(rect.get("w", 0.0))),
	)
	var bottom := mini(
		image.get_height(),
		ceili(float(rect.get("y", 0.0)) + float(rect.get("h", 0.0))),
	)
	var count := 0
	for y in range(top, bottom):
		for x in range(left, right):
			var pixel := image.get_pixel(x, y)
			if pixel.a > 0.5 and pixel.r + pixel.g + pixel.b < 1.35:
				count += 1
	return count


func _diff_by_coords(
	before: Image, after: Image, battle_view: Node, coords: Array
) -> Array:
	var result: Array = []
	for coord: Variant in coords:
		if not coord is Dictionary:
			continue
		var q := int(coord.get("q", 0))
		var r := int(coord.get("r", 0))
		var control := _find_hex_tile(battle_view, q, r)
		if control == null:
			result.append({"q": q, "r": r, "pixels": -1, "present": false})
			continue
		result.append({
			"q": q,
			"r": r,
			"present": true,
			"pixels": _diff_pixels(before, after, control.get_global_rect()),
			"rect": _rect_dict(control.get_global_rect()),
		})
	return result


func _diff_by_coords_with_fallback(
	before: Image,
	after: Image,
	battle_view: Node,
	coords: Array,
	prior_rows: Array,
) -> Array:
	## Free destination tiles only exist while their move intent is current.
	## After a refresh that drops them, sample the remembered rect against the
	## new image so ghost-highlight checks stay pixel-real rather than absent.
	var prior_by_qr := {}
	for row: Variant in prior_rows:
		if row is Dictionary:
			prior_by_qr[_qr_key(int(row.get("q", 0)), int(row.get("r", 0)))] = row
	var result: Array = []
	for coord: Variant in coords:
		if not coord is Dictionary:
			continue
		var q := int(coord.get("q", 0))
		var r := int(coord.get("r", 0))
		var control := _find_hex_tile(battle_view, q, r)
		if control != null:
			result.append({
				"q": q,
				"r": r,
				"present": true,
				"pixels": _diff_pixels(before, after, control.get_global_rect()),
			})
			continue
		var prior: Variant = prior_by_qr.get(_qr_key(q, r), null)
		if prior is Dictionary and prior.get("rect") is Dictionary:
			var rect := _rect_from_dict(prior["rect"])
			result.append({
				"q": q,
				"r": r,
				"present": true,
				"pixels": _diff_pixels(before, after, rect),
			})
			continue
		result.append({"q": q, "r": r, "pixels": -1, "present": false})
	return result


func _move_marker_pixels_for_coords(
	image: Image, battle_view: Node, coords: Array
) -> Array:
	## Count upper-rim pixels matching public move-marker colors. Used for
	## ghost checks after layout may have recentered between snapshots.
	var move_colors: Array = [
		Color(0.18, 0.72, 0.88, 1.0),
		Color(0.22, 0.42, 0.92, 1.0),
		Color(0.35, 0.78, 0.55, 1.0),
	]
	var result: Array = []
	for coord: Variant in coords:
		if not coord is Dictionary:
			continue
		var q := int(coord.get("q", 0))
		var r := int(coord.get("r", 0))
		var control := _find_hex_tile(battle_view, q, r)
		if control == null:
			result.append({"q": q, "r": r, "pixels": 0, "present": false})
			continue
		result.append({
			"q": q,
			"r": r,
			"present": true,
			"pixels": _count_color_matches(
				image, control.get_global_rect(), move_colors
			),
		})
	return result


func _count_color_matches(image: Image, rect: Rect2, colors: Array) -> int:
	var left := maxi(0, floori(rect.position.x + 20.0))
	var top := maxi(0, floori(rect.position.y + 8.0))
	var right := mini(image.get_width(), ceili(rect.end.x - 20.0))
	var bottom := mini(image.get_height(), floori(rect.position.y + 12.0))
	var count := 0
	for y in range(top, bottom):
		for x in range(left, right):
			var pixel := image.get_pixel(x, y)
			for candidate: Variant in colors:
				if not candidate is Color:
					continue
				var color := candidate as Color
				var distance := (
					absf(pixel.r - color.r)
					+ absf(pixel.g - color.g)
					+ absf(pixel.b - color.b)
				)
				if distance <= 0.18:
					count += 1
					break
	return count


func _rect_from_dict(rect_dict: Dictionary) -> Rect2:
	return Rect2(
		float(rect_dict.get("x", 0.0)),
		float(rect_dict.get("y", 0.0)),
		float(rect_dict.get("w", 0.0)),
		float(rect_dict.get("h", 0.0)),
	)


func _qr_key(q: int, r: int) -> String:
	return "%d,%d" % [q, r]


func _changed_color_means(
	before: Image, after: Image, battle_view: Node, moves: Array
) -> Array:
	return _changed_color_means_for_hexes(
		before, after, battle_view, _pair_coords(moves)
	)


func _changed_color_means_for_hexes(
	before: Image, after: Image, battle_view: Node, coords: Array
) -> Array:
	var result: Array = []
	for coord: Variant in coords:
		if not coord is Dictionary:
			continue
		var q := int(coord.get("q", 0))
		var r := int(coord.get("r", 0))
		var control := _find_hex_tile(battle_view, q, r)
		if control == null:
			result.append({"q": q, "r": r, "pixels": 0, "rgb": [], "present": false})
			continue
		var rect := control.get_global_rect()
		# Sample the marker's upper border, away from rounded corners.
		var left := maxi(0, floori(rect.position.x + 20.0))
		var top := maxi(0, floori(rect.position.y + 8.0))
		var right := mini(before.get_width(), ceili(rect.end.x - 20.0))
		var bottom := mini(before.get_height(), floori(rect.position.y + 12.0))
		var count := 0
		var red := 0.0
		var green := 0.0
		var blue := 0.0
		for y in range(top, bottom):
			for x in range(left, right):
				var old_pixel := before.get_pixel(x, y)
				var new_pixel := after.get_pixel(x, y)
				var changed := (
					absf(old_pixel.r - new_pixel.r)
					+ absf(old_pixel.g - new_pixel.g)
					+ absf(old_pixel.b - new_pixel.b)
					+ absf(old_pixel.a - new_pixel.a)
				)
				if changed <= 0.06:
					continue
				count += 1
				red += new_pixel.r
				green += new_pixel.g
				blue += new_pixel.b
		result.append({
			"q": q,
			"r": r,
			"present": true,
			"pixels": count,
			"rgb": [red / count, green / count, blue / count] if count > 0 else [],
		})
	return result


func _diff_pixels(before: Image, after: Image, rect: Rect2) -> int:
	var left := maxi(0, floori(rect.position.x))
	var top := maxi(0, floori(rect.position.y))
	var right := mini(before.get_width(), ceili(rect.end.x))
	var bottom := mini(before.get_height(), ceili(rect.end.y))
	var count := 0
	for y in range(top, bottom):
		for x in range(left, right):
			var a := before.get_pixel(x, y)
			var b := after.get_pixel(x, y)
			if absf(a.r - b.r) + absf(a.g - b.g) + absf(a.b - b.b) + absf(a.a - b.a) > 0.06:
				count += 1
	return count


func _fail(message: String) -> void:
	printerr("battle_move_visibility_probe: ", message)
	quit(1)
