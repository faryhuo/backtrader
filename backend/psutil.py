"""
Minimal psutil compatibility shim for test environments where psutil is absent.
"""

from __future__ import annotations

import os


class _MemoryInfo:
    def __init__(self, rss: int):
        self.rss = rss


class Process:
    def __init__(self, pid: int | None = None):
        self.pid = pid or os.getpid()

    def memory_info(self):
        return _MemoryInfo(0)

