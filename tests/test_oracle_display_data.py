from pathlib import Path

from soloquest.engine.oracles import load_oracle_display

DATA_DIR = Path(__file__).parent.parent / "soloquest" / "data"


def test_loads_categories():
    cats, _ = load_oracle_display(DATA_DIR)
    assert len(cats) > 0


def test_categories_have_name_and_keys():
    cats, _ = load_oracle_display(DATA_DIR)
    for cat in cats:
        assert cat.name
        assert len(cat.keys) > 0


def test_loads_inspirations():
    _, insps = load_oracle_display(DATA_DIR)
    assert len(insps) > 0


def test_inspirations_have_label_and_cmd():
    _, insps = load_oracle_display(DATA_DIR)
    for insp in insps:
        assert insp.label
        assert insp.cmd.startswith("/oracle")


def test_category_names_are_unique():
    cats, _ = load_oracle_display(DATA_DIR)
    names = [c.name for c in cats]
    assert len(names) == len(set(names))


def test_returns_empty_for_missing_file(tmp_path):
    cats, insps = load_oracle_display(tmp_path)
    assert cats == []
    assert insps == []


def test_core_category_present():
    cats, _ = load_oracle_display(DATA_DIR)
    assert any(c.name == "Core" for c in cats)


def test_core_category_includes_action():
    cats, _ = load_oracle_display(DATA_DIR)
    core = next(c for c in cats if c.name == "Core")
    assert "action" in core.keys
