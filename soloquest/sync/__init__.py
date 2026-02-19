"""Sync package — port/adapter abstraction for co-op event sharing.

Single-player uses LocalAdapter (no-op). Co-op campaigns use FileLogAdapter
(per-player JSONL files). Future adapters (WebSocket, etc.) implement SyncPort.
"""

from soloquest.sync.file_log import FileLogAdapter
from soloquest.sync.local import LocalAdapter
from soloquest.sync.models import Event, Proposal, Resolution
from soloquest.sync.port import SyncPort

__all__ = ["Event", "FileLogAdapter", "LocalAdapter", "Proposal", "Resolution", "SyncPort"]
