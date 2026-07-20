"""Tests for the immutable strategic party composition."""

from dataclasses import FrozenInstanceError

import pytest

from tbb import BRUISE, Battlefield, BattleSide, Hex, HexBattle, MAIMED, Party, Unit


def test_party_accepts_hero_with_zero_or_twelve_subordinates():
    hero = Unit(training=3)

    empty_party = Party(hero)
    full_party = Party(hero, [Unit(experience=i) for i in range(12)])

    assert empty_party.hero is hero
    assert empty_party.units == ()
    assert full_party.hero is hero
    assert len(full_party.units) == 12
    assert hero not in full_party.units


def test_party_owner_id_defaults_to_none_and_preserves_explicit_value():
    assert Party(Unit()).owner_id is None
    assert Party(Unit(), owner_id="north").owner_id == "north"


@pytest.mark.parametrize("owner_id", ["", 1, object()])
def test_party_rejects_empty_or_non_text_owner_id(owner_id):
    with pytest.raises((TypeError, ValueError)):
        Party(Unit(), owner_id=owner_id)


@pytest.mark.parametrize("hero", [None, "not a unit"])
def test_party_rejects_missing_or_invalid_hero(hero):
    with pytest.raises((TypeError, ValueError)):
        Party(hero)


def test_party_requires_a_hero_argument():
    with pytest.raises(TypeError):
        Party()


def test_party_rejects_thirteen_or_invalid_subordinates():
    with pytest.raises(ValueError):
        Party(Unit(), [Unit() for _ in range(13)])

    with pytest.raises(TypeError):
        Party(Unit(), [Unit(), object()])


def test_party_copies_units_to_tuple_and_is_immutable():
    hero = Unit()
    subordinate = Unit(training=1)
    source = [subordinate]
    party = Party(hero, source)

    source.append(Unit())

    assert party.units == (subordinate,)
    assert isinstance(party.units, tuple)
    with pytest.raises(FrozenInstanceError):
        party.hero = Unit()
    with pytest.raises(FrozenInstanceError):
        party.units = ()
    with pytest.raises(FrozenInstanceError):
        party.owner_id = "changed"


def test_reconstruct_uses_ordered_survivors_and_preserves_owner():
    original = Party(Unit(), [Unit(), Unit()], owner_id="north")
    hero = Unit(training=2)
    first = Unit(equipment=3)
    second = Unit(experience=4)

    reconstructed = Party.reconstruct(original, [hero, first, second])

    assert reconstructed is not original
    assert reconstructed.hero is hero
    assert reconstructed.units == (first, second)
    assert reconstructed.owner_id == "north"


def test_reconstruct_preserves_survivor_objects_with_wounds_and_experience():
    original = Party(Unit(), owner_id="north")
    wounded_hero = Unit(experience=5, wounds=(MAIMED,))
    wounded_unit = Unit(experience=7, wounds=(MAIMED,))

    reconstructed = Party.reconstruct(original, (wounded_hero, wounded_unit))

    assert reconstructed.hero is wounded_hero
    assert reconstructed.units[0] is wounded_unit
    assert reconstructed.hero.experience == 5
    assert reconstructed.units[0].wounds == (MAIMED,)


def test_reconstruct_clears_stun_without_losing_survivor_state():
    original = Party(Unit(), owner_id="north")
    stunned_hero = Unit(
        training=2, equipment=3, experience=5, wounds=(BRUISE,), stunned=True
    )
    ready_unit = Unit(experience=7, wounds=(MAIMED,))
    stunned_unit = Unit(
        training=1, equipment=4, experience=6, wounds=(BRUISE, MAIMED),
        stunned=True,
    )
    survivors = (stunned_hero, ready_unit, stunned_unit)

    reconstructed = Party.reconstruct(original, survivors)

    assert reconstructed.hero == Unit(
        training=2, equipment=3, experience=5, wounds=(BRUISE,), stunned=False
    )
    assert reconstructed.units == (
        ready_unit,
        Unit(
            training=1,
            equipment=4,
            experience=6,
            wounds=(BRUISE, MAIMED),
            stunned=False,
        ),
    )
    assert reconstructed.units[0] is ready_unit
    assert survivors == (stunned_hero, ready_unit, stunned_unit)
    assert stunned_hero.stunned is True
    assert stunned_unit.stunned is True


def test_reconstruct_removes_units_absent_from_survivors():
    hero = Unit(training=1)
    survivor = Unit(training=2)
    fallen = Unit(training=3)
    original = Party(hero, (survivor, fallen))

    reconstructed = Party.reconstruct(original, (hero, survivor))

    assert reconstructed.units == (survivor,)
    assert fallen not in reconstructed.units


def test_reconstruct_rejects_missing_hero_and_more_than_twelve_subordinates():
    original = Party(Unit())

    with pytest.raises(ValueError):
        Party.reconstruct(original, ())
    with pytest.raises(ValueError):
        Party.reconstruct(original, [Unit() for _ in range(14)])


@pytest.mark.parametrize(
    ("survivors", "message"),
    [
        ((object(),), "party hero must be a Unit"),
        ((Unit(), object()), "party subordinates must be Units"),
    ],
)
def test_reconstruct_rejects_non_unit_survivors_with_constructor_errors(
    survivors, message
):
    with pytest.raises(TypeError, match=message):
        Party.reconstruct(Party(Unit()), survivors)


def test_reconstruct_accepts_side_survivors_in_deployment_order():
    original = Party(Unit(), [Unit()], owner_id="north")
    hero = Unit(training=2)
    subordinate = Unit(equipment=3)
    defender = Unit()
    battle = HexBattle(Battlefield()).deploy(
        hero, Hex(0, 0), BattleSide.ATTACKER
    ).deploy(subordinate, Hex(1, 0), BattleSide.ATTACKER)
    battle = battle.deploy(defender, Hex(2, 0), BattleSide.DEFENDER)

    reconstructed = Party.reconstruct(
        original, battle.side_survivors(BattleSide.ATTACKER)
    )

    assert reconstructed.hero is hero
    assert reconstructed.units == (subordinate,)


def test_reconstruct_does_not_mutate_original_or_survivor_sequence():
    original = Party(Unit(training=1), [Unit(training=2)], owner_id="north")
    survivors = [Unit(training=3), Unit(training=4)]
    original_state = (original.hero, original.units, original.owner_id)
    survivors_before = list(survivors)

    first = Party.reconstruct(original, survivors)
    second = Party.reconstruct(original, survivors)

    assert first == second
    assert (original.hero, original.units, original.owner_id) == original_state
    assert survivors == survivors_before


def test_tick_wounds_heals_bruise_on_hero_and_subordinate_keeps_maimed():
    """Party.tick_wounds advances temporary wounds for every member."""
    hero = Unit(training=2, wounds=(BRUISE, MAIMED))
    subordinate = Unit(equipment=3, experience=1, wounds=(BRUISE,))
    party = Party(hero, (subordinate,), owner_id="north")

    healed = party.tick_wounds(2)

    assert healed is not party
    assert healed.owner_id == "north"
    assert healed.hero.wounds == (MAIMED,)
    assert healed.units == (Unit(equipment=3, experience=1, wounds=()),)
    assert BRUISE not in healed.hero.wounds
    assert BRUISE not in healed.units[0].wounds
    assert MAIMED in healed.hero.wounds
    assert party.hero.wounds == (BRUISE, MAIMED)
    assert party.units[0].wounds == (BRUISE,)


def test_public_api_exports_party():
    from tbb import Party as PublicParty

    assert PublicParty is Party
