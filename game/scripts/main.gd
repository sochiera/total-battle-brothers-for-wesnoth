extends Control


const SnapshotModel = preload("res://scripts/snapshot_model.gd")
const BridgeClient = preload("res://scripts/bridge_client.gd")
const BridgeConfig = preload("res://scripts/bridge_config.gd")
const OrderResult = preload("res://scripts/order_result.gd")
const START_FAILURE_STATUS := "Nie udało się uruchomić mostu ani rozpocząć partii."
const SAVE_SUCCESS_STATUS := "Partia została zapisana."
const SAVE_FAILURE_STATUS := "Nie udało się zapisać partii."
const LOAD_SUCCESS_STATUS := "Partia została wczytana."
const LOAD_FAILURE_STATUS := "Nie udało się wczytać partii."


var _client: Variant = null
var _save_path := ""

func _ready() -> void:
	start_session(BridgeConfig.from_environment())


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
	if _client != null and _client.has_method("snapshot_model"):
		refresh_from_bridge(_client)


func _connect_pressed_once(button: Button, handler: Callable) -> void:
	if not button.pressed.is_connected(handler):
		button.pressed.connect(handler)


func _on_next_turn_button_pressed() -> void:
	if _client != null:
		advance_turn_from_bridge(_client)


func _on_develop_button_pressed() -> void:
	_send_bound_order("develop")


func _on_recruit_button_pressed() -> void:
	_send_bound_order("recruit")


func _on_muster_button_pressed() -> void:
	_send_bound_order("muster")


func _on_march_button_pressed() -> void:
	_send_bound_order("march")


func _on_assault_button_pressed() -> void:
	_send_bound_order("assault")


func _on_save_game_button_pressed() -> void:
	if _client != null:
		_apply_save_load_result(
			_client.save_party(_save_path), SAVE_SUCCESS_STATUS, SAVE_FAILURE_STATUS
		)


func _on_load_game_button_pressed() -> void:
	if _client != null:
		_apply_save_load_result(
			_client.load_party(_save_path), LOAD_SUCCESS_STATUS, LOAD_FAILURE_STATUS
		)


func _send_bound_order(order_name: String) -> void:
	if _client != null:
		send_order_from_bridge(_client, order_name)


func refresh_from_bridge(client) -> bool:
	var model: SnapshotModel = client.snapshot_model()
	return _apply_model_if_present(model)


func advance_turn_from_bridge(client) -> bool:
	var model: SnapshotModel = client.advance_turn()
	return _apply_model_if_present(model)


func develop_from_bridge(client) -> bool:
	return send_order_from_bridge(client, "develop")


func send_order_from_bridge(client, order_name: String) -> bool:
	var model: SnapshotModel = client.send_order(order_name)
	if _apply_model_if_present(model):
		%LastOrderStatusLabel.text = OrderResult.status_text(_last_order_result(client))
		return true
	%LastOrderStatusLabel.text = OrderResult.failure_status_text()
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
		%LastOrderStatusLabel.text = success_status
		return true
	%LastOrderStatusLabel.text = failure_status
	return false


func apply_model(model: SnapshotModel) -> void:
	%DateLabel.text = "Rok %d, miesiąc %d" % [model.year, model.month]
	%ResultLabel.text = _get_result_text(model.player_result)
	_apply_result_visual_style(model.player_result)
	%PlayerPartyPositionLabel.text = _player_party_position_text(model.player_party_region)
	var player_duchy_status_label: Label = %PlayerDuchyStatusLabel
	var player_duchy_status: Variant = model.player_duchy_status
	player_duchy_status_label.text = ""
	if player_duchy_status is Dictionary:
		player_duchy_status_label.text = "Morale: %s, osady: %s, oddziały: %s" % [
			player_duchy_status["morale"],
			player_duchy_status["settlements"],
			player_duchy_status["parties"],
		]
	_render_region_list(model.regions)
	_render_world_views(model)


func _render_world_views(model: SnapshotModel) -> void:
	%MapView.render_model(model)
	%BattleView.render_model(model)


func _render_region_list(regions: Array) -> void:
	var region_list: ItemList = %RegionList
	region_list.clear()
	for region: Variant in regions:
		region_list.add_item(region["name"])


func _player_party_position_text(player_party_region: Variant) -> String:
	if player_party_region is String and not player_party_region.is_empty():
		return "Położenie oddziału: %s" % player_party_region
	return "Położenie oddziału: brak"


func _apply_result_visual_style(player_result: String) -> void:
	var result_label: Label = %ResultLabel
	match player_result:
		"victory":
			result_label.modulate = Color.GREEN
		"defeat":
			result_label.modulate = Color.RED
		"draw":
			result_label.modulate = Color.YELLOW
		_:
			result_label.modulate = Color.WHITE


func _get_result_text(player_result: String) -> String:
	var result_map := {
		"ongoing": "Wynik: gra trwa",
		"victory": "Wynik: zwycięstwo",
		"defeat": "Wynik: porażka",
		"draw": "Wynik: remis",
	}
	if player_result in result_map:
		return result_map[player_result]
	return "Wynik: brak"
