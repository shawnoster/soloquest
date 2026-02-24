"""Configuration management for wyrd CLI."""

from __future__ import annotations

from pathlib import Path

CONFIG_DIR = Path.home() / ".config" / "wyrd"
CONFIG_FILE = CONFIG_DIR / "config.toml"


class Config:
    """Shared configuration object.

    Priority order for adventures_dir:
    1. CLI argument (set via set_adventures_dir())
    2. Config file setting (future)
    3. Default: ~/wyrd-adventures
    """

    _instance: Config | None = None
    _adventures_dir: Path | None = None

    def __new__(cls) -> Config:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @property
    def adventures_dir(self) -> Path:
        """Get the adventures directory path."""
        if self._adventures_dir is not None:
            return self._adventures_dir

        return Path.home() / "wyrd-adventures"

    def set_adventures_dir(self, path: Path | str | None) -> None:
        """Set the adventures directory from CLI argument."""
        self._adventures_dir = None if path is None else Path(path).expanduser().resolve()

    def saves_dir(self) -> Path:
        """Get the saves directory path."""
        return self.adventures_dir / "saves"

    def sessions_dir(self) -> Path:
        """Get the sessions directory path."""
        return self.adventures_dir / "sessions"

    def journal_dir(self) -> Path:
        """Get the journal directory path."""
        return self.adventures_dir / "journal"

    def reset(self) -> None:
        """Reset config to defaults (useful for testing)."""
        self._adventures_dir = None


config = Config()
