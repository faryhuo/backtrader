"""
Utilities for capturing detailed execution logs during strategy runs.

Captures:
- Python logging records
- stdout prints
- stderr writes
- Python warnings
"""

from __future__ import annotations

import io
import logging
import sys
import warnings
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Iterator, List


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class ExecutionLogEntry:
    timestamp: str
    level: str
    message: str
    source: str

    def to_dict(self) -> dict[str, str]:
        return {
            "timestamp": self.timestamp,
            "level": self.level,
            "message": self.message,
            "source": self.source,
        }


class ExecutionLogCollector:
    """Bounded in-memory collector for execution log entries."""

    def __init__(self, max_entries: int = 2000):
        self.max_entries = max_entries
        self._entries: List[ExecutionLogEntry] = []

    def add(
        self,
        level: str,
        message: Any,
        *,
        source: str,
        timestamp: str | None = None,
    ) -> None:
        text = str(message).strip()
        if not text:
            return

        self._entries.append(
            ExecutionLogEntry(
                timestamp=timestamp or _utc_now_iso(),
                level=str(level).lower(),
                message=text,
                source=source,
            )
        )

        if len(self._entries) > self.max_entries:
            overflow = len(self._entries) - self.max_entries
            del self._entries[:overflow]

    def as_list(self) -> list[dict[str, str]]:
        return [entry.to_dict() for entry in self._entries]


class _CollectorLogHandler(logging.Handler):
    def __init__(self, collector: ExecutionLogCollector):
        super().__init__(level=logging.NOTSET)
        self.collector = collector

    def emit(self, record: logging.LogRecord) -> None:
        try:
            self.collector.add(
                record.levelname.lower(),
                record.getMessage(),
                source=f"logger:{record.name}",
                timestamp=datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            )
        except Exception:
            self.handleError(record)


class _CollectorStream(io.TextIOBase):
    def __init__(self, collector: ExecutionLogCollector, *, level: str, source: str):
        self.collector = collector
        self.level = level
        self.source = source
        self._buffer = ""

    @property
    def encoding(self) -> str:
        return "utf-8"

    def writable(self) -> bool:
        return True

    def write(self, data: str) -> int:
        if not data:
            return 0

        self._buffer += data
        lines = self._buffer.splitlines(keepends=True)
        self._buffer = ""

        for line in lines:
            if line.endswith("\n") or line.endswith("\r"):
                self.collector.add(self.level, line.rstrip("\r\n"), source=self.source)
            else:
                self._buffer = line

        return len(data)

    def flush(self) -> None:
        if self._buffer:
            self.collector.add(self.level, self._buffer, source=self.source)
            self._buffer = ""


@contextmanager
def capture_execution_logs(max_entries: int = 2000) -> Iterator[ExecutionLogCollector]:
    """Capture logging, stdout, stderr, and warnings for a scoped execution block."""

    collector = ExecutionLogCollector(max_entries=max_entries)
    handler = _CollectorLogHandler(collector)
    root_logger = logging.getLogger()
    original_stdout = sys.stdout
    original_stderr = sys.stderr
    original_showwarning = warnings.showwarning

    stdout_stream = _CollectorStream(collector, level="info", source="stdout")
    stderr_stream = _CollectorStream(collector, level="error", source="stderr")

    def _showwarning(message, category, filename, lineno, file=None, line=None):
        formatted = warnings.formatwarning(message, category, filename, lineno, line).rstrip()
        collector.add("warning", formatted, source="warning")

    root_logger.addHandler(handler)
    sys.stdout = stdout_stream
    sys.stderr = stderr_stream
    warnings.showwarning = _showwarning

    try:
        yield collector
    finally:
        stdout_stream.flush()
        stderr_stream.flush()
        warnings.showwarning = original_showwarning
        sys.stdout = original_stdout
        sys.stderr = original_stderr
        root_logger.removeHandler(handler)
