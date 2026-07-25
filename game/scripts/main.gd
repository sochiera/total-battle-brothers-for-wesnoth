extends Control


const SnapshotModel = preload("res://scripts/snapshot_model.gd")


func _ready() -> void:
	pass


func apply_model(model: SnapshotModel) -> void:
	$DateLabel.text = "Rok %d, miesiąc %d" % [model.year, model.month]
	var region_list: ItemList = $RegionList
	for region: Variant in model.regions:
		if region is Dictionary and region.get("name") is String:
			region_list.add_item(region["name"])
