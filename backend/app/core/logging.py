import json
import logging
import sys
from datetime import datetime, timezone
from typing import Any, Dict


class JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_obj: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Include custom attributes if present
        for attr in ("request_id", "delivery_id", "event_type", "event", "service", "user_id"):
            if hasattr(record, attr):
                log_obj[attr] = getattr(record, attr)

        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_obj)


def setup_logging(level: str = "INFO") -> logging.Logger:
    logger = logging.getLogger("proofmesh")
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    # Avoid duplicate handlers
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(JSONFormatter())
        logger.addHandler(handler)

    # Also configure root logger handler formatting if needed
    logging.basicConfig(level=getattr(logging, level.upper(), logging.INFO), handlers=[logging.StreamHandler(sys.stdout)])
    for h in logging.root.handlers:
        h.setFormatter(JSONFormatter())

    return logger


logger = setup_logging()
