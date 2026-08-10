extends RefCounted


## Shared battle-pausing resolution for live measurement probes.
## Keep all measurement gates on the same pending-battle detection rule.
static func resolve_pending_battle(client, model: Variant) -> Variant:
	if model != null and model.battle is Dictionary and model.battle.get("result") == null:
		return client.battle_auto()
	return model
