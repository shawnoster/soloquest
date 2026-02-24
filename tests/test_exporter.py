"""Tests for journal export functionality."""

from __future__ import annotations

from datetime import datetime

import pytest

from wyrd.journal.exporter import export_session
from wyrd.models.character import Character, Stats
from wyrd.models.session import Session


@pytest.fixture
def tmp_sessions(tmp_path, monkeypatch):
    """Redirect sessions directory to temp path."""
    tmp_sessions_dir = tmp_path / "sessions"
    from wyrd.journal import exporter

    monkeypatch.setattr(exporter, "_sessions_dir", lambda: tmp_sessions_dir)
    return tmp_sessions_dir


@pytest.fixture
def sample_character():
    return Character(
        name="Robin Skargard",
        homeworld="Akani Station",
        stats=Stats(edge=2, heart=3, iron=1, shadow=2, wits=2),
    )


@pytest.fixture
def sample_session():
    session = Session(number=1, title="The Derelict")
    session.started_at = datetime(2026, 2, 14, 10, 30, 0)
    session.add_journal("I arrive at the abandoned mining station.")
    session.add_move("Face Danger (wits) → weak hit")
    session.add_oracle("Action: Clash")
    return session


class TestExportSession:
    def test_creates_session_file(self, tmp_sessions, sample_character, sample_session):
        """Session export creates a markdown file."""
        path = export_session(sample_session, sample_character)
        assert path.exists()
        assert path.name == "session_001_the_derelict.md"

    def test_uses_yaml_frontmatter(self, tmp_sessions, sample_character, sample_session):
        """Session export uses YAML frontmatter for metadata."""
        path = export_session(sample_session, sample_character)
        content = path.read_text(encoding="utf-8")

        # Should start with YAML frontmatter
        assert content.startswith("---\n")
        assert "session: 1\n" in content
        assert "character: Robin Skargard\n" in content
        assert "date: 2026-02-14\n" in content
        assert "title: The Derelict\n" in content

        # Should close frontmatter before content
        lines = content.split("\n")
        assert lines[0] == "---"
        assert "---" in lines[1:6]  # Frontmatter closes within first few lines

    def test_session_without_title_uses_number(
        self, tmp_sessions, sample_character, sample_session
    ):
        """Session without title uses 'Session N' as filename."""
        sample_session.title = ""
        path = export_session(sample_session, sample_character)
        assert path.name == "session_001.md"

        content = path.read_text(encoding="utf-8")
        assert "# Session 1\n" in content
        # No title field in frontmatter if empty
        assert "title:" not in content

    def test_includes_session_entries(self, tmp_sessions, sample_character, sample_session):
        """Session export includes all journal entries."""
        path = export_session(sample_session, sample_character)
        content = path.read_text(encoding="utf-8")

        assert "I arrive at the abandoned mining station." in content
        assert "Face Danger (wits) → weak hit" in content
        assert "Action: Clash" in content

    def test_includes_session_stats(self, tmp_sessions, sample_character, sample_session):
        """Session export includes footer with stats."""
        path = export_session(sample_session, sample_character)
        content = path.read_text(encoding="utf-8")

        assert "1 moves" in content
        assert "1 oracles" in content
        assert "1 journal entries" in content

    def test_frontmatter_properly_closed(self, tmp_sessions, sample_character, sample_session):
        """Frontmatter has closing --- before markdown content."""
        path = export_session(sample_session, sample_character)
        content = path.read_text(encoding="utf-8")

        lines = content.split("\n")
        # Find both frontmatter delimiters
        first_delimiter = lines.index("---")
        second_delimiter = lines.index("---", first_delimiter + 1)

        # Content should start after second delimiter
        assert first_delimiter == 0
        assert second_delimiter < 10  # Should be near the top
        assert lines[second_delimiter + 1] == ""  # Blank line after frontmatter
        assert lines[second_delimiter + 2].startswith("# ")  # Then the title
