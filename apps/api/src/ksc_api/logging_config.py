"""Logging setup.

Restriction (docs/SECURITY.md): logs never contain document text, witness
identifiers beyond public codes, or secrets. Log structured metadata only.
"""

from __future__ import annotations

import logging


def configure_logging(level: str = "INFO") -> None:
    logging.basicConfig(
        level=level.upper(),
        format="%(asctime)s %(levelname)s %(name)s — %(message)s",
    )
