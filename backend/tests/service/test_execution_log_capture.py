import logging
import warnings

from src.service.execution_log_capture import capture_execution_logs


def test_capture_execution_logs_collects_logging_stdout_and_warnings():
    logger = logging.getLogger("tests.execution_log_capture")
    original_level = logger.level
    logger.setLevel(logging.INFO)

    try:
        with capture_execution_logs() as collector:
            logger.info("logger message")
            print("printed message")
            warnings.warn("warning message", RuntimeWarning)
    finally:
        logger.setLevel(original_level)

    logs = collector.as_list()
    messages = [entry["message"] for entry in logs]
    levels = [entry["level"] for entry in logs]

    assert any("logger message" in message for message in messages)
    assert any("printed message" in message for message in messages)
    assert any("warning message" in message for message in messages)
    assert "info" in levels
    assert "warning" in levels
