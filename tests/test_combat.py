from tbb import HILLS, PLAINS, Terrain, Unit, melee_hit_chance


def test_base_recruit_against_base_recruit_on_plains_has_fifty_percent_chance():
    assert melee_hit_chance(Unit(), Unit(), PLAINS, PLAINS, morale=0) == 50


def test_pillars_terrain_and_morale_follow_the_exact_formula():
    attacker = Unit(training=4, equipment=2, experience=3)
    defender = Unit(training=1, equipment=5, experience=2)
    exposed_ground = Terrain("Exposed", move_cost=1, defense_mod=-2, accuracy_mod=-3)

    assert melee_hit_chance(attacker, defender, HILLS, exposed_ground, morale=6) == 59
    assert melee_hit_chance(attacker, defender, HILLS, exposed_ground, morale=-6) == 47


def test_hit_chance_is_clamped_to_five_and_ninety_five_percent():
    strong = Unit(training=100, experience=100)
    defended = Unit(equipment=100, experience=100)

    assert melee_hit_chance(strong, Unit(), HILLS, PLAINS, morale=100) == 95
    assert melee_hit_chance(Unit(), defended, PLAINS, HILLS, morale=-100) == 5


def test_hit_chance_is_deterministic_and_does_not_change_inputs():
    attacker = Unit(training=2, equipment=3, experience=4)
    defender = Unit(training=5, equipment=6, experience=7)
    attacker_terrain = Terrain("Rise", move_cost=2, defense_mod=1, accuracy_mod=3)
    defender_terrain = Terrain("Cover", move_cost=2, defense_mod=4, accuracy_mod=-2)
    inputs_before = (attacker, defender, attacker_terrain, defender_terrain)

    first = melee_hit_chance(attacker, defender, attacker_terrain, defender_terrain, morale=2)
    second = melee_hit_chance(attacker, defender, attacker_terrain, defender_terrain, morale=2)

    assert first == second == 44
    assert (attacker, defender, attacker_terrain, defender_terrain) == inputs_before
