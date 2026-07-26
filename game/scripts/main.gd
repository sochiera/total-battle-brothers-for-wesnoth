extends Control


const SnapshotModel = preload("res://scripts/snapshot_model.gd")
const BridgeClient = preload("res://scripts/bridge_client.gd")
const BridgeConfig = preload("res://scripts/bridge_config.gd")


var _client: Variant = null


func _ready() -> void:
	var config: Variant = BridgeConfig.from_environment()
	if config != null:
		start_session(config)


func start_session(config) -> bool:
	if not BridgeConfig.is_valid_session_config(config):
		return false

	var command: String = config["command"]
	var state_path: String = config["state_path"]
	var seed: int = config["seed"]
	var client := BridgeClient.create_persistent(command, state_path, seed)
	bind_client(client)
	return refresh_from_bridge(client)


func bind_client(client) -> void:
	_client = client
	var next_turn_button: Button = $NextTurnButton
	var next_turn_handler := _on_next_turn_button_pressed
	if not next_turn_button.pressed.is_connected(next_turn_handler):
		next_turn_button.pressed.connect(next_turn_handler)
	var develop_button: Button = $DevelopButton
	var develop_handler := _on_develop_button_pressed
	if not develop_button.pressed.is_connected(develop_handler):
		develop_button.pressed.connect(develop_handler)


func _on_next_turn_button_pressed() -> void:
	if _client != null:
		advance_turn_from_bridge(_client)


func _on_develop_button_pressed() -> void:
	if _client != null:
		develop_from_bridge(_client)


func refresh_from_bridge(client) -> bool:
	var model: SnapshotModel = client.snapshot_model()
	return _apply_model_if_present(model)


func advance_turn_from_bridge(client) -> bool:
	var model: SnapshotModel = client.advance_turn()
	return _apply_model_if_present(model)


func develop_from_bridge(client) -> bool:
	return _apply_model_if_present(client.send_order("develop"))


func _apply_model_if_present(model: SnapshotModel) -> bool:
	if model == null:
		return false
	apply_model(model)
	return true


func apply_model(model: SnapshotModel) -> void:
	$DateLabel.text = "Rok %d, miesiąc %d" % [model.year, model.month]
	$ResultLabel.text = "Wynik: %s" % model.player_result
	var player_duchy_status_label: Label = $PlayerDuchyStatusLabel
	var player_duchy_status: Variant = model.player_duchy_status
	if player_duchy_status is Dictionary:
		player_duchy_status_label.text = "Morale: %s, osady: %s, oddziały: %s" % [
			player_duchy_status["morale"],
			player_duchy_status["settlements"],
			player_duchy_status["parties"],
		]
	else:
		player_duchy_status_label.text = ""
	var region_list: ItemList = $RegionList
	region_list.clear()
	for region: Variant in model.regions:
		if region is Dictionary and region.get("name") is String:
			region_list.add_item(region["name"])
