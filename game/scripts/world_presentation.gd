class_name WorldPresentation
extends RefCounted

## Single presentation dictionary for world place-names (G100.1a / G99.1b).
## Canonical ids stay on the order/selection contract; only UI labels use these.

const REGION_PL: Dictionary = {
	"player lands": "Ziemie gracza",
	"player outpost": "Posterunek gracza",
	"border": "Pogranicze",
	"ai outpost": "Posterunek wroga",
	"ai lands": "Ziemie wroga",
}

const SETTLEMENT_PL: Dictionary = {
	"Player Keep": "Twierdza gracza",
	"Player Outpost": "Posterunek gracza",
	"AI Keep": "Twierdza wroga",
	"AI Outpost": "Posterunek wroga",
}


static func region_label(canonical: String) -> String:
	return _label_or_canonical(REGION_PL, canonical)


static func settlement_label(canonical: String) -> String:
	return _label_or_canonical(SETTLEMENT_PL, canonical)


static func party_strength_text(party: Variant) -> String:
	var party_text := _party_text(party)
	if party_text == "brak armii":
		return party_text
	if not party is Dictionary:
		return party_text

	var size: Variant = party.get("size")
	var hp: Variant = party.get("hp")
	if not _is_number(size) or not _is_number(hp):
		return party_text
	return "%s, %s %s, %s PŻ" % [
		party_text,
		str(size),
		_unit_word(size),
		str(hp),
	]


static func settlement_strength_text(settlement: Variant) -> String:
	var settlement_text := _settlement_text(settlement)
	if settlement_text == "brak osady":
		return settlement_text
	if not settlement is Dictionary:
		return settlement_text

	var garrison: Variant = settlement.get("garrison")
	if not _is_number(garrison):
		return settlement_text
	return "%s, garnizon: %s" % [settlement_text, str(garrison)]


static func side_text(owner: Variant) -> String:
	match owner:
		"player":
			return "własny (gracz)"
		"ai":
			return "AI (wróg)"
		null, "":
			return "neutralny (brak właściciela)"
		_:
			return str(owner)


static func _settlement_text(settlement: Variant) -> String:
	if settlement is Dictionary:
		var settlement_name: Variant = settlement.get("name")
		if settlement_name is String and not settlement_name.is_empty():
			return settlement_label(settlement_name)
	return "brak osady"


static func _party_text(party: Variant) -> String:
	if party is Dictionary:
		var party_owner: Variant = party.get("owner")
		if party_owner != null and party_owner != "":
			return side_text(party_owner)
	return "brak armii"


static func _is_number(value: Variant) -> bool:
	return value is int or value is float


static func _unit_word(size: Variant) -> String:
	if size == 1:
		return "jednostka"
	if size is int:
		var absolute_size: int = abs(size)
		var last_digit := absolute_size % 10
		var last_two_digits := absolute_size % 100
		if last_digit >= 2 and last_digit <= 4 and not (
			last_two_digits >= 12 and last_two_digits <= 14
		):
			return "jednostki"
	return "jednostek"


static func _label_or_canonical(table: Dictionary, canonical: String) -> String:
	if table.has(canonical):
		return str(table[canonical])
	return canonical
