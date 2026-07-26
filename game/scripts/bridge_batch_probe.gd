extends SceneTree


const BridgeClient = preload("res://scripts/bridge_client.gd")
const PREFIX := "BRIDGE_BATCH "
const INVALID_RESPONSE_LINES := ["not json", "[]", "42", "\"text\""]


func _init() -> void:
	var commands: Array = [
		{"type": "next_turn", "turn": 1},
		{"type": "save", "path": "user://slot.json"},
		{"type": "snapshot", "options": {"verbose": true}},
	]
	var request := BridgeClient.request_lines(commands)
	var responses := BridgeClient.all_responses("\n {\"sequence\": 1} \n\t\n{\"sequence\": 2}\n{\"sequence\": 3}\n")

	if "--corrupt" in OS.get_cmdline_user_args():
		responses.pop_back()

	var error := _verify(commands, request, responses)
	if not error.is_empty():
		printerr("bridge_batch_probe: ", error)
		call_deferred("quit", 1)
		return

	print(PREFIX, JSON.stringify({
		"request": request,
		"empty_request": BridgeClient.request_lines([]),
		"responses": responses,
	}))
	call_deferred("quit", 0)


func _verify(commands: Array, request: String, responses: Array) -> String:
	if not request.ends_with("\n"):
		return "batch request is missing its trailing newline"
	if BridgeClient.request_lines([]) != "":
		return "empty batch request is not empty"

	var lines := request.split("\n", false)
	if lines.size() != commands.size():
		return "batch request has the wrong number of non-empty lines"
	for index in lines.size():
		var parsed: Variant = JSON.parse_string(lines[index])
		if not parsed is Dictionary or not _same_json_value(parsed, commands[index]):
			return "batch request is not reversible"

	var expected_responses: Array = [
		{"sequence": 1},
		{"sequence": 2},
		{"sequence": 3},
	]
	if not _same_json_value(responses, expected_responses):
		return "responses are not complete and ordered"
	if BridgeClient.all_responses(" \n\t\n") != []:
		return "blank output did not produce an empty response list"

	for invalid_line in INVALID_RESPONSE_LINES:
		var output: String = "{\"before\": true}\n%s\n{\"after\": true}\n" % invalid_line
		if not _same_json_value(BridgeClient.all_responses(output), [{"before": true}]):
			return "invalid response line did not stop parsing"
	return ""


func _same_json_value(left: Variant, right: Variant) -> bool:
	if left is Dictionary and right is Dictionary:
		if left.size() != right.size():
			return false
		for key in left:
			if not right.has(key) or not _same_json_value(left[key], right[key]):
				return false
		return true
	if left is Array and right is Array:
		if left.size() != right.size():
			return false
		for index in left.size():
			if not _same_json_value(left[index], right[index]):
				return false
		return true
	return left == right
