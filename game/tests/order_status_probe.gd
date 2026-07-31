extends SceneTree


const MAIN_SCENE_PATH := "res://scenes/main.tscn"
const PREFIX := "ORDER_STATUS "
const SnapshotModel = preload("res://scripts/snapshot_model.gd")


class StubClient:
	extends RefCounted

	var result: Variant = {"order": "develop", "changed": true}

	func send_order(_order_name: String, _target: String = "") -> SnapshotModel:
		var model := SnapshotModel.new()
		model.year = 1
		model.month = 1
		model.player_result = "ongoing"
		model.regions = []
		return model

	func last_order_result() -> Variant:
		return result


func _init() -> void:
	var scene: PackedScene = ResourceLoader.load(MAIN_SCENE_PATH) as PackedScene
	if scene == null:
		printerr("order_status_probe: cannot load main scene")
		call_deferred("quit", 2)
		return

	var scene_root := scene.instantiate()
	root.add_child(scene_root)
	var status_label := scene_root.find_child("LastOrderStatusLabel", true, false) as Label
	if status_label == null:
		printerr("order_status_probe: missing LastOrderStatusLabel")
		call_deferred("quit", 1)
		return

	var banner := scene_root.find_child("OrderStatusBanner", true, false) as TextureRect
	var slot := scene_root.find_child("OrderStatusSlot", true, false) as Control
	var initial_text: String = status_label.text
	var initial_banner_visible := banner != null and banner.is_visible_in_tree()
	var initial_slot_visible := slot != null and slot.is_visible_in_tree()

	var client := StubClient.new()
	client.result = {
		"kind": "battle",
		"order": "assault",
		"outcome": "nierozstrzygnięta",
		"attacker_losses": 0,
		"defender_losses": 0,
	}
	scene_root.send_order_from_bridge(client, "assault")
	await process_frame
	var populated_text: String = status_label.text
	var populated_banner_visible := banner != null and banner.is_visible_in_tree()
	var populated_slot_visible := slot != null and slot.is_visible_in_tree()
	var banner_path := ""
	var text_width := 0.0
	var drawn_banner_width := 0.0
	var opaque_banner_body_width := 0.0
	var label_content_width := 0.0
	var slot_height := 0.0
	var text_content_height := 0.0
	if banner != null and banner.texture != null:
		banner_path = banner.texture.resource_path
		var font := status_label.get_theme_font("font")
		var font_size := status_label.get_theme_font_size("font_size")
		text_width = font.get_string_size(
			populated_text, HORIZONTAL_ALIGNMENT_LEFT, -1, font_size
		).x
		var texture_size := banner.texture.get_size()
		drawn_banner_width = minf(
			banner.size.x, banner.size.y * texture_size.x / texture_size.y
		)
		var banner_image := banner.texture.get_image()
		var center_y := banner_image.get_height() / 2
		var opaque_left := 0
		var opaque_right := banner_image.get_width() - 1
		while (
			opaque_left < banner_image.get_width()
			and banner_image.get_pixel(opaque_left, center_y).a == 0.0
		):
			opaque_left += 1
		while (
			opaque_right >= 0
			and banner_image.get_pixel(opaque_right, center_y).a == 0.0
		):
			opaque_right -= 1
		opaque_banner_body_width = (
			float(opaque_right - opaque_left + 1)
			* drawn_banner_width
			/ texture_size.x
		)
		label_content_width = status_label.size.x
		slot_height = banner.get_parent_control().size.y
		text_content_height = status_label.get_line_count() * font.get_height(font_size)

	client.result = null
	scene_root.send_order_from_bridge(client, "develop")
	await process_frame

	print(PREFIX, JSON.stringify({
		"text": initial_text,
		"banner_found": banner != null,
		"banner_path": banner_path,
		"initial_banner_visible": initial_banner_visible,
		"initial_slot_visible": initial_slot_visible,
		"populated_text": populated_text,
		"populated_banner_visible": populated_banner_visible,
		"populated_slot_visible": populated_slot_visible,
		"text_width": text_width,
		"drawn_banner_width": drawn_banner_width,
		"opaque_banner_body_width": opaque_banner_body_width,
		"label_content_width": label_content_width,
		"slot_height": slot_height,
		"text_content_height": text_content_height,
		"empty_text": status_label.text,
		"empty_banner_visible": banner != null and banner.is_visible_in_tree(),
		"empty_slot_visible": slot != null and slot.is_visible_in_tree(),
	}))
	call_deferred("quit", 0)
