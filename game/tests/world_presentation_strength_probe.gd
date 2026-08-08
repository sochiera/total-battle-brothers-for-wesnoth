extends SceneTree

const WorldPresentation = preload("res://scripts/world_presentation.gd")


func _init() -> void:
	var party_cases: Dictionary = {
		"player_full": {"owner": "player", "size": 5, "hp": 73},
		"ai_singular": {"owner": "ai", "size": 1, "hp": 25},
		"missing": null,
		"non_dict": "oops",
		"empty_owner": {"owner": "", "size": 3, "hp": 10},
		"missing_size": {"owner": "player", "hp": 50},
		"non_numeric_size": {"owner": "player", "size": "abc", "hp": 50},
	}
	var settlement_cases: Dictionary = {
		"keep_garrison_zero": {"name": "Player Keep", "garrison": 0},
		"outpost_garrison_five": {"name": "Player Outpost", "garrison": 5},
		"missing": null,
		"missing_garrison": {"name": "AI Keep"},
		"non_numeric_garrison": {"name": "AI Outpost", "garrison": "x"},
		# G114.1c (task-637) AC3: snapshot niesie ``free`` (snapshot.py) — wiersz
		# osady dokłada wolną ludność obok garnizonu. Zero jest realną wartością
		# (jak garnizon: 0), więc go nie trać. AC4: brakujące/nieliczbowe ``free``
		# → dotychczasowy tekst BEZ fabrykowanego „0" (symetrycznie do garnizonu).
		"keep_garrison_zero_free_zero": {"name": "Player Keep", "garrison": 0, "free": 0},
		"outpost_garrison_five_free_three": {"name": "Player Outpost", "garrison": 5, "free": 3},
		"keep_garrison_two_missing_free": {"name": "AI Keep", "garrison": 2},
		"keep_garrison_two_non_numeric_free": {"name": "AI Outpost", "garrison": 2, "free": "x"},
	}

	var party_text: Dictionary = {}
	for case_name: String in party_cases:
		party_text[case_name] = WorldPresentation.party_strength_text(party_cases[case_name])

	var settlement_text: Dictionary = {}
	for case_name: String in settlement_cases:
		settlement_text[case_name] = WorldPresentation.settlement_strength_text(
			settlement_cases[case_name]
		)

	print("WORLD_PRESENTATION_STRENGTH ", JSON.stringify({
		"party": party_text,
		"settlement": settlement_text,
	}))
	call_deferred("quit", 0)
