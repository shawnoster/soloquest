"""Tests for character_md serialisation / deserialisation."""

from __future__ import annotations

from wyrd.models.asset import Asset, AssetAbility, CharacterAsset
from wyrd.models.character import Character, Stats
from wyrd.state.character_md import character_from_markdown, character_to_markdown


def _make_character(**kwargs) -> Character:
    defaults = dict(
        name="Kira Vex",
        pronouns="she/her",
        callsign="Reaper",
        look="Scarred face",
        act="Moves cautiously",
        wear="Worn leather duster",
        backstory="Lost her crew to the void.",
        gear=["Plasma cutter", "Medkit"],
        stats=Stats(edge=2, heart=1, iron=3, shadow=2, wits=3),
    )
    defaults.update(kwargs)
    return Character(**defaults)


def _asset_registry() -> dict:
    return {
        "glowcat": Asset(
            key="glowcat",
            name="Glowcat",
            category="companion",
            abilities=[
                AssetAbility(text="When you make your cat do tricks, +1."),
                AssetAbility(text="When you cuddle, add +heart."),
                AssetAbility(text="Once per session, reroll one die."),
            ],
        )
    }


class TestDescriptionBullets:
    def test_serialises_wear_look_act_as_bullets(self):
        char = _make_character()
        md = character_to_markdown(char)
        assert "- Wear: Worn leather duster" in md
        assert "- Look: Scarred face" in md
        assert "- Act: Moves cautiously" in md

    def test_bullet_order_is_wear_look_act(self):
        char = _make_character()
        md = character_to_markdown(char)
        wear_pos = md.index("- Wear:")
        look_pos = md.index("- Look:")
        act_pos = md.index("- Act:")
        assert wear_pos < look_pos < act_pos

    def test_no_subheadings_for_description_fields(self):
        char = _make_character()
        md = character_to_markdown(char)
        assert "### Look" not in md
        assert "### Act" not in md
        assert "### Wear" not in md

    def test_round_trip_description_fields(self):
        char = _make_character()
        md = character_to_markdown(char)
        result = character_from_markdown(md)
        assert result is not None
        narrative, _ = result
        assert narrative.look == "Scarred face"
        assert narrative.act == "Moves cautiously"
        assert narrative.wear == "Worn leather duster"

    def test_parses_legacy_subheading_format(self):
        legacy_md = """\
# Character Sheet — Old Character

## Description

### Look

Sharp eyes

### Act

Quietly

### Wear

Dark cloak

### Backstory

Once a soldier.

### Gear

- Knife
"""
        result = character_from_markdown(legacy_md)
        assert result is not None
        narrative, _ = result
        assert narrative.look == "Sharp eyes"
        assert narrative.act == "Quietly"
        assert narrative.wear == "Dark cloak"


class TestAssetAbilities:
    def test_serialises_abilities_with_text(self):
        char = _make_character()
        char.assets = [
            CharacterAsset(
                asset_key="glowcat",
                abilities_unlocked=[True, False, False],
            )
        ]
        registry = _asset_registry()
        md = character_to_markdown(char, registry)
        assert "- [x] When you make your cat do tricks, +1." in md
        assert "- [ ] When you cuddle, add +heart." in md
        assert "- [ ] Once per session, reroll one die." in md

    def test_serialises_abilities_without_registry(self):
        char = _make_character()
        char.assets = [
            CharacterAsset(
                asset_key="glowcat",
                abilities_unlocked=[True, False, True],
            )
        ]
        md = character_to_markdown(char)
        assert "- [x]" in md
        assert "- [ ]" in md

    def test_round_trip_ability_bullets(self):
        char = _make_character()
        char.assets = [
            CharacterAsset(
                asset_key="glowcat",
                abilities_unlocked=[True, False, True],
            )
        ]
        registry = _asset_registry()
        md = character_to_markdown(char, registry)
        result = character_from_markdown(md)
        assert result is not None
        _, assets = result
        assert len(assets) == 1
        assert assets[0].abilities_unlocked == [True, False, True]

    def test_parses_legacy_abilities_line(self):
        md = """\
# Character Sheet — Test

## Assets

### Glowcat

Abilities: [x] [ ] [x]

---
"""
        result = character_from_markdown(md)
        assert result is not None
        _, assets = result
        assert assets[0].abilities_unlocked == [True, False, True]
