"""Logging setup.

Restriction (docs/SECURITY.md): logs never contain document text, witness
identifiers beyond public codes, or secrets. Log structured metadata only.

Format ``json`` (the container default) writes one JSON object per line so
log shippers can index fields; ``text`` keeps the human-readable line for
local development.
"""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime

_RESERVED = set(logging.LogRecord("", 0, "", 0, "", (), None).__dict__) | {"message", "asctime"}


class JsonFormatter(logging.Formatter):
    """One JSON object per line: timestamp, level, logger, message and any
    structured ``extra`` fields the caller attached."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, object] = {
            "ts": datetime.fromtimestamp(record.created, tz=UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }
        for key, value in record.__dict__.items():
            if key not in _RESERVED and not key.startswith("_"):
                payload[key] = value
        if record.exc_info:
            payload["exc_type"] = getattr(record.exc_info[0], "__name__", str(record.exc_info[0]))
        return json.dumps(payload, default=str, ensure_ascii=False)


def configure_logging(level: str = "INFO", fmt: str = "json") -> None:
    root = logging.getLogger()
    root.setLevel(level.upper())
    for existing in list(root.handlers):
        root.removeHandler(existing)
    handler = logging.StreamHandler()
    if fmt.lower() == "json":
        handler.setFormatter(JsonFormatter())
    else:
        handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s — %(message)s"))
    root.addHandler(handler)
