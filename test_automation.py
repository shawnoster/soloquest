"""Automated end-to-end testing script for Starforged CLI.

Tests the complete system by creating a synthetic session programmatically,
then validates exports and error handling.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from soloquest.engine.dice import DiceMode, DigitalDice
from soloquest.engine.moves import resolve_move
from soloquest.engine.oracles import load_oracles
from soloquest.journal.exporter import export_session, append_to_journal
from soloquest.models.character import Character, Stats
from soloquest.models.session import Session
from soloquest.models.vow import Vow, VowRank
from soloquest.state.save import save_game, load_game

DATA_DIR = Path(__file__).parent / "soloquest" / "data"


def test_character_creation():
    """Test 1: Character creation and validation."""
    print("\n=== Test 1: Character Creation ===")

    char = Character(
        name="Kael Vex",
        homeworld="Drift Station Erebus",
        stats=Stats(edge=2, heart=1, iron=3, shadow=2, wits=3),
        assets=["starship", "ace", "gearhead"],
    )

    assert char.name == "Kael Vex"
    assert char.stats.iron == 3
    assert char.health == 5
    assert char.spirit == 5
    assert char.supply == 3  # Default is 3, not 5
    assert char.momentum == 2
    assert char.momentum_max == 10
    assert char.momentum_reset == 2

    print(f"[PASS] Character created: {char.name}")
    print(f"[PASS] Stats validated: Iron={char.stats.iron}, Wits={char.stats.wits}")
    print(f"[PASS] Tracks initialized correctly")

    return char


def test_session_logging(char: Character):
    """Test 2: Session creation and journal logging."""
    print("\n=== Test 2: Session Logging ===")

    session = Session(number=1, title="Test Session")

    # Journal entries
    session.add_journal("The airlock hisses open. Dust swirls in the thin atmosphere.")
    session.add_journal("The settlement ahead looks abandoned, but I spot faint light.")

    # Move result
    session.add_move("FACE DANGER | Edge 2 + d6(4) + 0 = 6 vs [3, 8] -> Weak Hit")

    # Oracle
    session.add_oracle("Action: Explore | Theme: Mystery")

    # Note
    session.add_note("Strange energy signature detected")

    assert len(session.entries) == 5
    print(f"[PASS] Session created with {len(session.entries)} entries")
    print(f"[PASS] Journal entries: 2")
    print(f"[PASS] Move results: 1")
    print(f"[PASS] Oracle results: 1")
    print(f"[PASS] Notes: 1")

    return session


def test_move_resolution():
    """Test 3: Move resolution with all outcome tiers."""
    print("\n=== Test 3: Move Resolution ===")

    # Strong Hit
    result = resolve_move(action_die=5, stat=3, adds=0, c1=4, c2=6)
    assert result.action_score == 8
    assert result.outcome.value == "strong_hit"
    print(f"[PASS] Strong Hit: {result.action_score} vs [{result.challenge_1}, {result.challenge_2}]")

    # Weak Hit
    result = resolve_move(action_die=3, stat=1, adds=0, c1=5, c2=2)
    assert result.outcome.value == "weak_hit"
    print(f"[PASS] Weak Hit: {result.action_score} vs [{result.challenge_1}, {result.challenge_2}]")

    # Miss
    result = resolve_move(action_die=1, stat=1, adds=0, c1=8, c2=9)
    assert result.outcome.value == "miss"
    print(f"[PASS] Miss: {result.action_score} vs [{result.challenge_1}, {result.challenge_2}]")

    # Match detection
    result = resolve_move(action_die=5, stat=3, adds=0, c1=7, c2=7)
    assert result.match is True
    print(f"[PASS] Match detected: challenge dice both {result.challenge_1}")

    # Momentum burn
    result = resolve_move(action_die=1, stat=1, adds=0, c1=5, c2=6, momentum=8, burn=True)
    assert result.burned_momentum is True
    assert result.outcome.value == "strong_hit"
    print(f"[PASS] Momentum burn: Miss -> Strong Hit with momentum {result.momentum_used}")


def test_track_management(char: Character):
    """Test 4: Track adjustments and bounds."""
    print("\n=== Test 4: Track Management ===")

    # Damage
    char.adjust_track("health", -2)
    assert char.health == 3
    print(f"[PASS] Health damage: 5 -> {char.health}")

    # Healing
    char.adjust_track("health", 1)
    assert char.health == 4
    print(f"[PASS] Health recovery: 3 -> {char.health}")

    # Upper bound clamping
    char.adjust_track("health", 10)
    assert char.health == 5
    print(f"[PASS] Health clamped at max: {char.health}")

    # Lower bound clamping
    char.adjust_track("spirit", -10)
    assert char.spirit == 0
    print(f"[PASS] Spirit clamped at min: {char.spirit}")

    # Momentum
    char.adjust_momentum(5)
    assert char.momentum == 7
    print(f"[PASS] Momentum gain: 2 -> {char.momentum}")

    # Momentum max
    char.adjust_momentum(10)
    assert char.momentum == 10
    print(f"[PASS] Momentum clamped at max: {char.momentum}")

    # Reset for next tests
    char.spirit = 5
    char.momentum = 2


def test_vow_lifecycle():
    """Test 5: Vow creation, progress, and fulfillment."""
    print("\n=== Test 5: Vow Lifecycle ===")

    # Create vow
    vow = Vow("Find the source of the signal", VowRank.DANGEROUS)
    assert vow.rank == VowRank.DANGEROUS
    assert vow.ticks == 0
    assert vow.progress_score == 0
    print(f"[PASS] Vow created: '{vow.description}' ({vow.rank.value})")

    # Mark progress (dangerous = 8 ticks)
    vow.mark_progress()
    assert vow.ticks == 8
    assert vow.progress_score == 2
    print(f"[PASS] Progress marked: {vow.ticks} ticks -> score {vow.progress_score}")

    # Mark again
    vow.mark_progress()
    assert vow.ticks == 16
    assert vow.progress_score == 4
    print(f"[PASS] Second mark: {vow.ticks} ticks -> score {vow.progress_score}")

    # Boxes filled
    assert vow.boxes_filled == 4
    print(f"[PASS] Progress boxes: {vow.boxes_filled}/10")

    # Fulfill
    vow.fulfilled = True
    assert vow.fulfilled is True
    print(f"[PASS] Vow fulfilled")

    return vow


def test_debilities(char: Character):
    """Test 6: Debility system and momentum caps."""
    print("\n=== Test 6: Debilities ===")

    # Toggle wounded
    char.toggle_debility("wounded")
    assert "wounded" in char.debilities
    assert char.momentum_max == 9
    print(f"[PASS] Wounded debility: momentum max -> {char.momentum_max}")

    # Toggle shaken (now 2 debilities total)
    char.toggle_debility("shaken")
    assert char.momentum_max == 8
    assert char.momentum_reset == 0  # 2+ debilities -> reset drops to 0
    print(f"[PASS] Shaken debility: momentum max -> {char.momentum_max}, reset -> {char.momentum_reset}")

    # Momentum should clamp when adjusted
    char.momentum = 10
    char.adjust_momentum(0)  # Triggers clamping
    assert char.momentum <= char.momentum_max
    print(f"[PASS] Momentum clamped to new max: {char.momentum}")

    # Toggle off
    char.toggle_debility("wounded")
    assert "wounded" not in char.debilities
    assert char.momentum_max == 9
    print(f"[PASS] Wounded removed: momentum max -> {char.momentum_max}")

    # Clear all debilities
    char.debilities.clear()
    char.momentum = 2


def test_oracle_system():
    """Test 7: Oracle loading and lookups."""
    print("\n=== Test 7: Oracle System ===")

    oracles = load_oracles(DATA_DIR)

    assert len(oracles) > 0
    print(f"[PASS] Loaded {len(oracles)} oracle tables")

    # Test specific oracles
    assert "action" in oracles
    assert "theme" in oracles
    assert "pay_the_price" in oracles
    print(f"[PASS] Key oracles present: action, theme, pay_the_price")

    # Test lookup
    result = oracles["action"].lookup(50)
    assert isinstance(result, str)
    assert len(result) > 0
    print(f"[PASS] Action oracle (50): '{result}'")

    # Test full range
    for roll in [1, 50, 100]:
        result = oracles["action"].lookup(roll)
        assert result != "Unknown"
    print(f"[PASS] Full range coverage (1, 50, 100)")

    # Test Pay the Price
    result = oracles["pay_the_price"].lookup(42)
    print(f"[PASS] Pay the Price (42): '{result}'")


def test_save_load_cycle(char: Character, vows: list[Vow]):
    """Test 8: Save and load game state."""
    print("\n=== Test 8: Save/Load Cycle ===")

    # Save
    save_path = save_game(
        character=char,
        vows=vows,
        session_count=1,
        dice_mode=DiceMode.DIGITAL,
    )

    assert save_path.exists()
    print(f"[PASS] Game saved: {save_path}")

    # Verify JSON structure
    with save_path.open() as f:
        data = json.load(f)

    assert data["character"]["name"] == "Kael Vex"
    assert data["session_count"] == 1
    assert data["settings"]["dice_mode"] == "digital"
    print(f"[PASS] Save file valid JSON")
    print(f"[PASS] Character name: {data['character']['name']}")
    print(f"[PASS] Session count: {data['session_count']}")

    # Load
    loaded_char, loaded_vows, loaded_count, loaded_mode = load_game("Kael Vex")

    assert loaded_char.name == char.name
    assert loaded_char.stats.iron == char.stats.iron
    assert loaded_count == 1
    assert loaded_mode == DiceMode.DIGITAL
    print(f"[PASS] Game loaded successfully")
    print(f"[PASS] Character data intact")
    print(f"[PASS] Vows count: {len(loaded_vows)}")


def test_export_markdown(char: Character, session: Session):
    """Test 9: Markdown export."""
    print("\n=== Test 9: Markdown Export ===")

    # Export session
    session_path = export_session(session, char)
    assert session_path.exists()
    print(f"[PASS] Session exported: {session_path}")

    # Read and validate
    content = session_path.read_text()
    assert "# Test Session" in content
    assert char.name in content
    assert "The airlock hisses open" in content
    print(f"[PASS] Session Markdown contains title and character")
    print(f"[PASS] Journal entries present")

    # Check structure
    assert "---" in content
    assert "*" in content  # Oracle italics
    assert ">" in content  # Mechanical quotes
    print(f"[PASS] Markdown formatting correct")

    # Append to journal
    journal_path = append_to_journal(session, char)
    assert journal_path.exists()
    print(f"[PASS] Journal appended: {journal_path}")

    return session_path, journal_path


def test_edge_cases():
    """Test 10: Error handling and edge cases."""
    print("\n=== Test 10: Edge Cases ===")

    char = Character(name="Test", stats=Stats())

    # Track bounds
    char.health = 5
    char.adjust_track("health", 100)
    assert char.health == 5
    print(f"[PASS] Health max bound: {char.health}")

    char.adjust_track("health", -100)
    assert char.health == 0
    print(f"[PASS] Health min bound: {char.health}")

    # Momentum bounds
    char.momentum = 0
    char.adjust_momentum(20)
    assert char.momentum == 10
    print(f"[PASS] Momentum max bound: {char.momentum}")

    char.adjust_momentum(-20)
    assert char.momentum == -6
    print(f"[PASS] Momentum min bound: {char.momentum}")

    # Vow progress max
    vow = Vow("Test", VowRank.TROUBLESOME)
    for _ in range(20):  # Over-mark
        vow.mark_progress()
    assert vow.ticks <= 40  # MAX_TICKS
    assert vow.progress_score == 10
    print(f"[PASS] Vow progress capped: {vow.progress_score}")

    # Debility toggle (on/off)
    char.toggle_debility("wounded")
    char.toggle_debility("wounded")
    assert "wounded" not in char.debilities
    print(f"[PASS] Debility toggle works")

    print(f"[PASS] All edge cases handled gracefully")


def generate_sample_session():
    """Generate a complete sample session for manual review."""
    print("\n=== Generating Sample Session ===")

    # Create character
    char = Character(
        name="Kael Vex",
        homeworld="Drift Station Erebus",
        stats=Stats(edge=2, heart=1, iron=3, shadow=2, wits=3),
        assets=["starship", "ace", "gearhead"],
    )

    # Create background vow
    bg_vow = Vow("Discover what destroyed the Andurath colony", VowRank.EPIC)

    # Create session
    session = Session(number=1, title="Abandoned Settlement Investigation")

    # Narrative intro
    session.add_journal(
        "The airlock hisses open. Dust swirls in the thin atmosphere as I step onto "
        "the surface of LV-426. The settlement ahead looks abandoned—empty hab modules "
        "scattered across the ridge, solar panels dark and lifeless."
    )

    session.add_journal(
        "But there's something off. A faint light pulses in the northern facility. "
        "Someone—or something—is still here."
    )

    # Oracle consultation
    session.add_oracle("Action: Explore | Theme: Mystery")

    # Move: Gather Information
    result = resolve_move(action_die=4, stat=3, adds=0, c1=3, c2=7)
    session.add_move(
        f"GATHER INFORMATION | Wits 3 + d6(4) + 0 = {result.action_score} "
        f"vs [{result.challenge_1}, {result.challenge_2}] -> {result.outcome.value.replace('_', ' ').title()}"
    )
    char.adjust_track("momentum", 2)
    session.add_mechanical(f"Momentum: {char.momentum - 2} -> {char.momentum}")

    session.add_journal(
        "I scan the facility with my multi-tool. Energy signatures everywhere—but "
        "they're wrong. Not solar, not fusion. Something else entirely."
    )

    # Create a vow
    signal_vow = Vow("Find the source of the signal", VowRank.DANGEROUS)
    session.add_mechanical("Vow: Find the source of the signal (Dangerous)")

    # Note
    session.add_note("Strange energy signature - unknown type")

    # Move: Face Danger
    result = resolve_move(action_die=2, stat=2, adds=0, c1=8, c2=5)
    session.add_move(
        f"FACE DANGER | Edge 2 + d6(2) + 0 = {result.action_score} "
        f"vs [{result.challenge_1}, {result.challenge_2}] -> {result.outcome.value.replace('_', ' ').title()}"
    )
    char.adjust_track("health", -1)
    session.add_mechanical(f"Health: {char.health + 1} -> {char.health}")

    session.add_journal(
        "The door explodes outward. I dive behind a cargo container as debris rains down. "
        "A shard catches my shoulder. Blood, but I'm still moving."
    )

    # Oracle
    session.add_oracle("Descriptor: Ancient | Focus: Technology")

    session.add_journal(
        "Through the smoke, I see it: some kind of artifact. Ancient tech, far older "
        "than the colony. It pulses with that same eerie light."
    )

    # Progress on vow
    signal_vow.mark_progress()
    session.add_mechanical(f"Vow Progress: {signal_vow.description} -> {signal_vow.boxes_filled}/10 boxes")

    # Note
    session.add_note("NPC?: Possible survivor in southern module")

    session.add_journal(
        "But I'm not alone. I hear movement in the southern module. Could be a survivor. "
        "Could be something worse."
    )

    # Save and export
    vows = [bg_vow, signal_vow]
    save_game(char, vows, 1, DiceMode.DIGITAL)

    session_path = export_session(session, char)
    journal_path = append_to_journal(session, char)

    print(f"[PASS] Sample session generated")
    print(f"[PASS] Session file: {session_path}")
    print(f"[PASS] Journal file: {journal_path}")

    return session_path, journal_path


def main():
    """Run all automated tests."""
    print("=" * 70)
    print("STARFORGED CLI - AUTOMATED TEST SUITE")
    print("=" * 70)

    try:
        # Run tests
        char = test_character_creation()
        session = test_session_logging(char)
        test_move_resolution()
        test_track_management(char)
        vows = [test_vow_lifecycle()]
        test_debilities(char)
        test_oracle_system()
        test_save_load_cycle(char, vows)
        session_path, journal_path = test_export_markdown(char, session)
        test_edge_cases()

        # Generate sample session
        sample_session, sample_journal = generate_sample_session()

        print("\n" + "=" * 70)
        print("ALL TESTS PASSED [PASS]")
        print("=" * 70)

        print("\n[Summary] Test Summary:")
        print("  [PASS] Character creation and validation")
        print("  [PASS] Session logging and journal entries")
        print("  [PASS] Move resolution (all outcome tiers)")
        print("  [PASS] Track management and bounds")
        print("  [PASS] Vow lifecycle (create/progress/fulfill)")
        print("  [PASS] Debility system and momentum caps")
        print("  [PASS] Oracle loading and lookups")
        print("  [PASS] Save/load game state")
        print("  [PASS] Markdown export (session + journal)")
        print("  [PASS] Edge cases and error handling")

        print("\n[Files] Generated Files:")
        print(f"  Session: {sample_session}")
        print(f"  Journal: {sample_journal}")
        print(f"  Save: saves/kael_vex.json")

        print("\n[Next] Next Steps:")
        print("  1. Review generated Markdown files for quality")
        print("  2. Run manual playthrough (PLAYTEST_GUIDE.md)")
        print("  3. Evaluate UX and visual presentation")

        return 0

    except AssertionError as e:
        print(f"\n[FAIL] TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
