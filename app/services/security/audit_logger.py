import hashlib
import json
import logging
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler
from pathlib import Path

from app.core.config import LOG_DIR


AUDIT_LOG_FILE = Path(LOG_DIR) / "security_audit.log"


def _build_logger() -> logging.Logger:
    logger = logging.getLogger("security_audit")

    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)
    logger.propagate = False

    handler = RotatingFileHandler(
        AUDIT_LOG_FILE,
        maxBytes=5 * 1024 * 1024,
        backupCount=3,
    )

    handler.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(handler)

    return logger


_logger = _build_logger()


def hash_identifier(value: str) -> str:
    """Create a non-reversible identifier for audit correlation."""
    return hashlib.sha256(
        str(value).encode("utf-8")
    ).hexdigest()[:16]


def log_security_event(
    event: str,
    *,
    endpoint: str = "",
    client_id: str = "",
    decision: str = "",
    risk_score: float | None = None,
    reasons: list[str] | None = None,
) -> None:
    """
    Write a structured security event.

    Never log passwords, API keys, credentials, or raw questions.
    """
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event": event,
        "endpoint": endpoint,
        "client_id": hash_identifier(client_id) if client_id else "",
        "decision": decision,
        "risk_score": risk_score,
        "reasons": reasons or [],
    }

    _logger.info(json.dumps(record))
