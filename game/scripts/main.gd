extends Control


const SnapshotModel = preload("res://scripts/snapshot_model.gd")
const BridgeClient = preload("res://scripts/bridge_client.gd")
const BridgeConfig = preload("res://scripts/bridge_config.gd")
const OrderResult = preload("res://scripts/order_result.gd")
const WorldPresentation = preload("res://scripts/world_presentation.gd")
const START_FAILURE_STATUS := "Nie udało się uruchomić mostu ani rozpocząć partii."
const SAVE_SUCCESS_STATUS := "Partia została zapisana."
const SAVE_FAILURE_STATUS := "Nie udało się zapisać partii."
const LOAD_SUCCESS_STATUS := "Partia została wczytana."
const LOAD_FAILURE_STATUS := "Nie udało się wczytać partii."
# OrderBarContent scene offsets: left/right 10 each, top/bottom 8 each.
# Both axes feed OrderControls.custom_minimum_size so the parchment bar does
# not under-report size when MainLayout sizes from content minima.
const ORDER_BAR_CONTENT_PAD := Vector2(20.0, 16.0)
# G100.1d: full-window parchment under MainLayout (see main.tscn).
# Reuses strategic_map_background.png until a dedicated window sheet exists.
const WINDOW_BACKGROUND_NODE := "StrategicWindowBackground"
const WINDOW_BACKGROUND_RES := "res://assets/strategic_map_background.png"
# G101.1c: visible ResultLabel value cells (row key is ResultKeyLabel).
const RESULT_VALUE_BY_CODE := {
	"ongoing": "gra trwa",
	"victory": "zwycięstwo",
	"defeat": "porażka",
	"draw": "remis",
}
const RESULT_FONT_BASE := Color(0.18, 0.11, 0.06, 1)
const RESULT_FONT_VICTORY := Color(0.14, 0.38, 0.16, 1)
const RESULT_FONT_DEFEAT := Color(0.55, 0.14, 0.1, 1)
const RESULT_FONT_DRAW := Color(0.52, 0.36, 0.08, 1)


var _client: Variant = null
var _save_path := ""
var _current_regions: Array = []
var _default_march_label := ""

func _ready() -> void:
	_ensure_strategic_window_background()
	_default_march_label = %MarchButton.text
	_apply_order_button_state_styles()
	_sync_order_controls_minimum_size()
	%MapView.region_selected.connect(_on_region_selected)
	start_session(BridgeConfig.from_environment())


func _ensure_strategic_window_background() -> void:
	## Keep the window parchment as the first full-rect sibling under Main so
	## container gaps never fall back to default grey chrome (G100.1d).
	var bg := get_node_or_null(WINDOW_BACKGROUND_NODE) as TextureRect
	if bg == null:
		return
	if bg.get_index() != 0:
		move_child(bg, 0)
	if bg.texture == null:
		bg.texture = load(WINDOW_BACKGROUND_RES) as Texture2D
	bg.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	bg.mouse_filter = Control.MOUSE_FILTER_IGNORE
	bg.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	bg.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_COVERED


func _order_action_buttons() -> Array[Button]:
	return [
		%NextTurnButton,
		%DevelopButton,
		%RecruitButton,
		%MusterButton,
		%MarchButton,
		%AssaultButton,
		%SaveGameButton,
		%LoadGameButton,
	]


func _sync_order_controls_minimum_size() -> void:
	## OrderControls is a plain Control so the parchment TextureRect can pin
	## full-rect behind the two button rows. Unlike VBoxContainer, Control does
	## not inherit child minimums — without an explicit min width MainLayout
	## collapses to Status+Map minima (848px) and MapView/BattleView stick at
	## custom_minimum_size.x=420. Headless map/battle probes (and any window
	## that sizes from content) then paint legacy 84px tiles and clip hex (2,2).
	var bar := $MainLayout/OrderControls as Control
	var content := $MainLayout/OrderControls/OrderBarContent as Control
	if bar == null or content == null:
		return
	var content_min := content.get_combined_minimum_size()
	var padded := content_min + ORDER_BAR_CONTENT_PAD
	bar.custom_minimum_size = Vector2(
		padded.x,
		maxf(padded.y, bar.custom_minimum_size.y)
	)


func _apply_order_button_state_styles() -> void:
	## G99.1d: explicit StyleBoxFlat per interaction state on every order button.
	## Built once here so main.tscn stays free of eight-fold style duplication while
	## probes still see has_theme_stylebox_override for normal/hover/pressed.
	var style_by_state := {
		"normal": _make_order_button_style(
			Color(0.88, 0.78, 0.58, 1.0), Color(0.42, 0.28, 0.12, 0.9)
		),
		"hover": _make_order_button_style(
			Color(0.95, 0.88, 0.68, 1.0), Color(0.55, 0.38, 0.14, 1.0)
		),
		"pressed": _make_order_button_style(
			Color(0.72, 0.58, 0.38, 1.0), Color(0.32, 0.2, 0.08, 1.0)
		),
	}
	var font_theme_key := {
		"normal": "font_color",
		"hover": "font_hover_color",
		"pressed": "font_pressed_color",
	}
	var font_by_state := {
		"normal": Color(0.18, 0.11, 0.06, 1.0),
		"hover": Color(0.14, 0.08, 0.04, 1.0),
		"pressed": Color(0.1, 0.05, 0.02, 1.0),
	}
	for button: Button in _order_action_buttons():
		for state_name: String in ["normal", "hover", "pressed"]:
			button.add_theme_stylebox_override(
				state_name, style_by_state[state_name].duplicate()
			)
			button.add_theme_color_override(
				font_theme_key[state_name], font_by_state[state_name]
			)


func _make_order_button_style(bg: Color, border: Color) -> StyleBoxFlat:
	var style := StyleBoxFlat.new()
	style.bg_color = bg
	style.border_color = border
	style.set_border_width_all(1)
	style.set_corner_radius_all(4)
	style.content_margin_left = 8.0
	style.content_margin_right = 8.0
	style.content_margin_top = 4.0
	style.content_margin_bottom = 4.0
	return style


func start_session(config) -> bool:
	if not BridgeConfig.is_valid_session_config(config):
		_apply_start_failure_status(false)
		return false

	var command: String = config["command"]
	var state_path: String = config["state_path"]
	_save_path = config["save_path"]
	var seed: int = config["seed"]
	var client := BridgeClient.create_persistent(command, state_path, seed)
	bind_client(client)
	var started := _persist_start_snapshot(client)
	_apply_start_failure_status(started)
	return started


func _persist_start_snapshot(client) -> bool:
	if not client.has_method("persist_snapshot"):
		return refresh_from_bridge(client)
	var model: SnapshotModel = client.persist_snapshot()
	return _apply_model_if_present(model)


func _apply_start_failure_status(started: bool) -> void:
	%StartStatusLabel.text = "" if started else START_FAILURE_STATUS


func bind_client(client) -> void:
	_client = client
	_connect_pressed_once(%NextTurnButton, _on_next_turn_button_pressed)
	_connect_pressed_once(%DevelopButton, _on_develop_button_pressed)
	_connect_pressed_once(%RecruitButton, _on_recruit_button_pressed)
	_connect_pressed_once(%MusterButton, _on_muster_button_pressed)
	_connect_pressed_once(%MarchButton, _on_march_button_pressed)
	_connect_pressed_once(%AssaultButton, _on_assault_button_pressed)
	_connect_pressed_once(%SaveGameButton, _on_save_game_button_pressed)
	_connect_pressed_once(%LoadGameButton, _on_load_game_button_pressed)
	_refresh_bound_client()


func _refresh_bound_client() -> void:
	if _has_bound_client() and _client.has_method("snapshot_model"):
		refresh_from_bridge(_client)


func _has_bound_client() -> bool:
	return _client != null


func _connect_pressed_once(button: Button, handler: Callable) -> void:
	if not button.pressed.is_connected(handler):
		button.pressed.connect(handler)


func _on_next_turn_button_pressed() -> void:
	if _has_bound_client():
		advance_turn_from_bridge(_client)


func _on_develop_button_pressed() -> void:
	_send_bound_order("develop")


func _on_recruit_button_pressed() -> void:
	_send_bound_order("recruit")


func _on_muster_button_pressed() -> void:
	_send_bound_order("muster")


func _on_march_button_pressed() -> void:
	var selected_region_name: String = %MapView.selected_region_name
	var order_name := "march" if selected_region_name.is_empty() else "move"
	_send_bound_order(order_name, selected_region_name)


func _on_assault_button_pressed() -> void:
	_send_bound_order("assault")


func _on_save_game_button_pressed() -> void:
	if _has_bound_client():
		_apply_save_load_result(
			_client.save_party(_save_path), SAVE_SUCCESS_STATUS, SAVE_FAILURE_STATUS
		)


func _on_load_game_button_pressed() -> void:
	if _has_bound_client():
		_apply_save_load_result(
			_client.load_party(_save_path), LOAD_SUCCESS_STATUS, LOAD_FAILURE_STATUS
		)


func _send_bound_order(order_name: String, target: String = "") -> void:
	if _has_bound_client():
		send_order_from_bridge(_client, order_name, target)


func refresh_from_bridge(client) -> bool:
	var model: SnapshotModel = client.snapshot_model()
	return _apply_model_if_present(model)


func advance_turn_from_bridge(client) -> bool:
	var model: SnapshotModel = client.advance_turn()
	return _apply_model_if_present(model)


func develop_from_bridge(client) -> bool:
	return send_order_from_bridge(client, "develop")


func send_order_from_bridge(client, order_name: String, target: String = "") -> bool:
	var model: SnapshotModel = client.send_order(order_name, target)
	if _apply_model_if_present(model):
		_set_last_order_status(OrderResult.status_text(_last_order_result(client)))
		return true
	_set_last_order_status(OrderResult.failure_status_text())
	return false


func _last_order_result(client) -> Variant:
	if not client.has_method("last_order_result"):
		return null
	return client.last_order_result()


func _apply_model_if_present(model: SnapshotModel) -> bool:
	if model == null:
		return false
	apply_model(model)
	return true


func _apply_save_load_result(
	model: SnapshotModel, success_status: String, failure_status: String
) -> bool:
	if _apply_model_if_present(model):
		_set_last_order_status(success_status)
		return true
	_set_last_order_status(failure_status)
	return false


func _set_last_order_status(status: String) -> void:
	%LastOrderStatusLabel.text = status


func apply_model(model: SnapshotModel) -> void:
	_current_regions = model.regions
	# Status card hierarchy (G101.1c): label+value rows with separators, not a
	# text wall. Visible ResultLabel / PlayerPartyPositionLabel hold value cells
	# only; ResultContractLabel / PartyPositionContractLabel / PlayerDuchyStatusLabel
	# keep historical full probe strings as hidden mirrors.
	_apply_status_card(model)
	_update_selected_region_panel(model.regions)
	# RegionList stays in the scene for probe/find_child compatibility but is
	# hidden on the status card (map is the sole region picker on screen).
	_render_region_list(model.regions)
	_render_world_views(model)


func _apply_status_card(model: SnapshotModel) -> void:
	%DateLabel.text = "Rok %d, miesiąc %d" % [model.year, model.month]
	var result_value: String = _get_result_value_text(model.player_result)
	_set_status_value_with_contract_mirror(
		%ResultLabel,
		%ResultContractLabel,
		result_value,
		_result_contract_text(result_value),
	)
	_apply_result_visual_style(model.player_result)
	_apply_player_duchy_status(model.player_duchy_status)
	var party_value: String = _player_party_position_value(model.player_party_region)
	_set_status_value_with_contract_mirror(
		%PlayerPartyPositionLabel,
		%PartyPositionContractLabel,
		party_value,
		_party_position_contract_text(party_value),
	)


func _set_status_value_with_contract_mirror(
	value_label: Label, mirror: Label, value: String, contract_text: String
) -> void:
	# Visible cell = bare value; hidden mirror keeps historical probe strings
	# (e.g. "Wynik: …") without duplicating prefixes on the status card.
	value_label.text = value
	_set_hidden_contract_mirror(mirror, contract_text)


func _set_hidden_contract_mirror(mirror: Label, contract_text: String) -> void:
	mirror.text = contract_text
	mirror.visible = false


func _render_world_views(model: SnapshotModel) -> void:
	%MapView.render_model(model)
	%BattleView.render_model(model)


func _apply_player_duchy_status(player_duchy_status: Variant) -> void:
	var metrics: Dictionary = _player_duchy_metrics(player_duchy_status)
	%MoraleValueLabel.text = metrics["morale"]
	%SettlementsValueLabel.text = metrics["settlements"]
	%PartiesValueLabel.text = metrics["parties"]
	_set_hidden_contract_mirror(
		%PlayerDuchyStatusLabel, _player_duchy_status_text(metrics)
	)


func _player_duchy_metrics(player_duchy_status: Variant) -> Dictionary:
	if not player_duchy_status is Dictionary:
		return {"morale": "", "settlements": "", "parties": ""}
	var status: Dictionary = player_duchy_status
	return {
		"morale": str(status.get("morale", "")),
		"settlements": str(status.get("settlements", "")),
		"parties": str(status.get("parties", "")),
	}


func _player_duchy_status_text(metrics: Dictionary) -> String:
	if metrics["morale"] == "" and metrics["settlements"] == "" and metrics["parties"] == "":
		return ""
	return "Morale: %s, osady: %s, oddziały: %s" % [
		metrics["morale"],
		metrics["settlements"],
		metrics["parties"],
	]


func _render_region_list(regions: Array) -> void:
	var region_list: ItemList = %RegionList
	region_list.clear()
	for region: Variant in regions:
		region_list.add_item(region["name"])


func _on_region_selected(region_name: String) -> void:
	_update_selected_region_panel(_current_regions)
	_update_march_button_label(region_name)


func _update_march_button_label(region_name: String) -> void:
	if region_name.is_empty():
		%MarchButton.text = _default_march_label
		return
	%MarchButton.text = "Wyrusz: %s" % WorldPresentation.region_label(region_name)


func _update_selected_region_panel(regions: Array) -> void:
	# Hierarchical panel rows inside SelectedRegionPanel; hidden
	# SelectedRegionDetailsLabel outside the panel mirrors joined text for
	# older e2e/march probes that still read a single multiline string.
	const EMPTY_PL := "Nie wybrano regionu"
	var selected_region: Dictionary = _find_selected_region(regions)
	var detail_rows: Array[Label] = [
		%SelectedRegionNameLabel,
		%SelectedRegionOwnerLabel,
		%SelectedRegionSettlementLabel,
		%SelectedRegionArmyLabel,
	]
	var details_mirror: Label = %SelectedRegionDetailsLabel
	var empty_label: Label = %SelectedRegionEmptyLabel

	if selected_region.is_empty():
		empty_label.text = EMPTY_PL
		empty_label.visible = true
		_set_selected_region_detail_rows(detail_rows, [])
		details_mirror.text = EMPTY_PL
		return

	var row_texts: Array[String] = _selected_region_detail_row_texts(selected_region)
	empty_label.text = ""
	empty_label.visible = false
	_set_selected_region_detail_rows(detail_rows, row_texts)
	details_mirror.text = "\n".join(row_texts)


func _selected_region_detail_row_texts(selected_region: Dictionary) -> Array[String]:
	return [
		"Nazwa: %s" % WorldPresentation.region_label(
			str(selected_region.get("name", ""))
		),
		"Właściciel: %s" % _side_text(selected_region.get("owner")),
		"Osada: %s" % _settlement_text(selected_region.get("settlement")),
		"Armia: %s" % _party_text(selected_region.get("party")),
	]


func _set_selected_region_detail_rows(
	rows: Array[Label], texts: Array[String]
) -> void:
	var show_rows: bool = not texts.is_empty()
	for index: int in range(rows.size()):
		var label: Label = rows[index]
		if show_rows and index < texts.size():
			label.text = texts[index]
			label.visible = true
		else:
			label.text = ""
			label.visible = false


func _find_selected_region(regions: Array) -> Dictionary:
	var selected_region_name: String = %MapView.selected_region_name
	if selected_region_name.is_empty():
		return {}
	for region: Variant in regions:
		if region is Dictionary and region.get("name") == selected_region_name:
			return region
	return {}


func _side_text(owner: Variant) -> String:
	match owner:
		"player":
			return "własny (gracz)"
		"ai":
			return "AI (wróg)"
		null, "":
			return "neutralny (brak właściciela)"
		_:
			return str(owner)


func _settlement_text(settlement: Variant) -> String:
	if settlement is Dictionary:
		var settlement_name: Variant = settlement.get("name")
		if settlement_name is String and not settlement_name.is_empty():
			return WorldPresentation.settlement_label(settlement_name)
	return "brak osady"


func _party_text(party: Variant) -> String:
	if party is Dictionary:
		var party_owner: Variant = party.get("owner")
		if party_owner != null and party_owner != "":
			return _side_text(party_owner)
	return "brak armii"


func _player_party_position_value(player_party_region: Variant) -> String:
	if player_party_region is String and not player_party_region.is_empty():
		return WorldPresentation.region_label(player_party_region)
	return "brak"


func _party_position_contract_text(value: String) -> String:
	# Historical single-line probe contract (G89+); key lives on PartyPositionKeyLabel.
	return "Położenie oddziału: %s" % value


func _apply_result_visual_style(player_result: String) -> void:
	# ResultLabel ma ciemnobrązowy font_color na pergaminie. Mnożenie go przez
	# Color.GREEN/RED/YELLOW w modulate gasi kanały → niemal czarny tekst.
	# Styl wyniku idzie wyłącznie przez theme_override font_color; modulate = WHITE.
	var result_label: Label = %ResultLabel
	result_label.modulate = Color.WHITE
	var font_color: Color = RESULT_FONT_BASE
	match player_result:
		"victory":
			font_color = RESULT_FONT_VICTORY
		"defeat":
			font_color = RESULT_FONT_DEFEAT
		"draw":
			font_color = RESULT_FONT_DRAW
	result_label.add_theme_color_override("font_color", font_color)


func _get_result_value_text(player_result: String) -> String:
	if player_result in RESULT_VALUE_BY_CODE:
		return RESULT_VALUE_BY_CODE[player_result]
	return "brak"


func _result_contract_text(value: String) -> String:
	# Historical single-line probe contract (G90.2b); key lives on ResultKeyLabel.
	return "Wynik: %s" % value
