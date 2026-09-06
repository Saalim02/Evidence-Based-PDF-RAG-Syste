import json

from app.services.security.audit_logger import (
    AUDIT_LOG_FILE,
    hash_identifier,
    log_security_event,
)


def test_hash_identifier_is_stable_and_non_reversible():
    value = "127.0.0.1"

    assert hash_identifier(value) == hash_identifier(value)
    assert value not in hash_identifier(value)


def test_audit_log_does_not_contain_secret(tmp_path, monkeypatch):
    log_file = tmp_path / "security_audit.log"

    import app.services.security.audit_logger as audit

    handler = audit._logger.handlers[0]
    handler.close()
    audit._logger.removeHandler(handler)

    from logging.handlers import RotatingFileHandler

    new_handler = RotatingFileHandler(
        log_file,
        maxBytes=1024 * 1024,
        backupCount=1,
    )
    new_handler.setFormatter(audit.logging.Formatter("%(message)s"))
    audit._logger.addHandler(new_handler)

    secret = "sk-test-secret-never-log-this"

    log_security_event(
        "authentication_failure",
        endpoint="/api/ask",
        client_id="127.0.0.1",
        reasons=["Invalid access credentials"],
    )

    content = log_file.read_text()

    assert secret not in content

    record = json.loads(content.strip())

    assert record["event"] == "authentication_failure"
    assert record["endpoint"] == "/api/ask"
    assert "127.0.0.1" not in content

    new_handler.close()
    audit._logger.removeHandler(new_handler)
