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


static func _label_or_canonical(table: Dictionary, canonical: String) -> String:
	if table.has(canonical):
		return str(table[canonical])
	return canonical
