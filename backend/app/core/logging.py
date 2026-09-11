
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone

from app.core.config import settings


class JsonFormatter(logging.Formatter):
    """Emit one JSON object per log event."""

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        for key in ("request_id", "method", "path", "status_code", "duration_ms"):
            if hasattr(record, key):
                payload[key] = getattr(record, key)

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(payload, default=str)


def configure_logging() -> None:
    """Configure application logging from environment settings."""
    root = logging.getLogger()
    root.setLevel(settings.LOG_LEVEL.upper())

    if not root.handlers:
        root.addHandler(logging.StreamHandler())

    formatter: logging.Formatter
    if settings.JSON_LOGS:
        formatter = JsonFormatter()
    else:
        formatter = logging.Formatter(
            "%(asctime)s %(levelname)s %(name)s %(message)s"
        )

    for handler in root.handlers:
        handler.setFormatter(formatter)
