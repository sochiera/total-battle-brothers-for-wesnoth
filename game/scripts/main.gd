extends Control


const SnapshotModel = preload("res://scripts/snapshot_model.gd")


func _ready() -> void:
	pass


func apply_model(model: SnapshotModel) -> void:
	$DateLabel.text = "Rok %d, miesiąc %d" % [model.year, model.month]
