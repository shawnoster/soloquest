"""Sync package — port/adapter abstraction for co-op event sharing.

Single-player uses LocalAdapter (no-op). Co-op campaigns use FileLogAdapter
(per-player JSONL files). Future adapters (WebSocket, etc.) implement SyncPort.
"""

from wyrd.sync.file_log import FileLogAdapter
from wyrd.sync.local import LocalAdapter
from wyrd.sync.models import Event, Proposal, Resolution
from wyrd.sync.port import SyncPort

__all__ = ["Event", "FileLogAdapter", "LocalAdapter", "Proposal", "Resolution", "SyncPort"]
