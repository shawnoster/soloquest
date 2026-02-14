"""Tests for the dice engine."""

from soloquest.engine.dice import (
    DiceMode,
    Die,
    DigitalDice,
    MixedDice,
    PhysicalDice,
    make_dice_provider,
    roll_action_dice,
    roll_challenge_dice,
    roll_oracle,
)


class TestDigitalDice:
    def test_d6_in_range(self):
        dice = DigitalDice()
        for _ in range(100):
            result = dice.roll(Die.D6)
            assert 1 <= result <= 6

    def test_d10_in_range(self):
        dice = DigitalDice()
        for _ in range(100):
            result = dice.roll(Die.D10)
            assert 1 <= result <= 10

    def test_d100_in_range(self):
        dice = DigitalDice()
        for _ in range(200):
            result = dice.roll(Die.D100)
            assert 1 <= result <= 100


class TestMixedDice:
    def test_defaults_to_digital(self):
        dice = MixedDice()
        # Should not prompt, just roll
        result = dice.roll(Die.D6)
        assert 1 <= result <= 6

    def test_manual_flag_sets_physical(self):
        dice = MixedDice()
        dice.set_manual(True)
        assert dice._force_physical is True
        dice.set_manual(False)
        assert dice._force_physical is False


class TestMakeDiceProvider:
    def test_digital_mode(self):
        provider = make_dice_provider(DiceMode.DIGITAL)
        assert isinstance(provider, DigitalDice)

    def test_physical_mode(self):
        provider = make_dice_provider(DiceMode.PHYSICAL)
        assert isinstance(provider, PhysicalDice)

    def test_mixed_mode(self):
        provider = make_dice_provider(DiceMode.MIXED)
        assert isinstance(provider, MixedDice)


class TestRollHelpers:
    def test_roll_action_dice_returns_three_values(self):
        dice = DigitalDice()
        action, c1, c2 = roll_action_dice(dice)
        assert 1 <= action <= 6
        assert 1 <= c1 <= 10
        assert 1 <= c2 <= 10

    def test_roll_challenge_dice_returns_two_d10s(self):
        dice = DigitalDice()
        c1, c2 = roll_challenge_dice(dice)
        assert 1 <= c1 <= 10
        assert 1 <= c2 <= 10

    def test_roll_oracle_returns_d100(self):
        dice = DigitalDice()
        for _ in range(50):
            result = roll_oracle(dice)
            assert 1 <= result <= 100
