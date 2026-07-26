extends RefCounted


static func request_line(command: Dictionary) -> String:
	return JSON.stringify(command)


static func first_response(output: String) -> Variant:
	for line in output.split("\n"):
		var trimmed: String = line.strip_edges()
		if trimmed.is_empty():
			continue

		var parsed: Variant = JSON.parse_string(trimmed)
		return parsed if parsed is Dictionary else null
	return null
