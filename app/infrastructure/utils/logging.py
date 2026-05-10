import logging

from app.infrastructure.utils.context import get_trace_id


class ContextTraceFilter(logging.Filter):
    """
    ContextTraceFilter
    ------------------
    A logging filter that injects a `trace_id` into every log record.

    Purpose:
        - Attach a unique trace identifier to all log entries
        - Enable request-level tracing across the entire application
        - Useful for APIs, microservices, async applications, and distributed systems

    How it works:
        The `filter()` method is executed before each log record is processed.
        We retrieve the current request's trace ID from the application context
        (typically stored using `contextvars`) and attach it to the log record.

    Returns:
        bool: True to allow the log record to continue through the pipeline.
    """

    def filter(self, record):
        # Retrieve trace_id from request context (via contextvars or any custom mechanism)
        record.trace_id = get_trace_id()

        # Allow the record to be processed
        return True


def configure_logging() -> None:
    """
    configure_logging
    -----------------
    Configures the application's logging system.

    Responsibilities:
        - Define a consistent log format including timestamp, level, trace_id, and message
        - Create a StreamHandler for console output
        - Set the global log level to INFO
        - Attach the ContextTraceFilter so every log record includes trace_id

    Log format example:
        2026-05-01 12:30:21 | INFO | trace_id=abc123 | User created successfully

    Usage:
        This function must be called once during application startup
        (typically in main.py or the application's bootstrap layer).
    """

    # Standard log format with trace_id included
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | trace_id=%(trace_id)s | %(message)s"
    )

    # Console output handler
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)

    # Root logger for the entire application
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # Attach handler and trace filter
    logger.addHandler(handler)
    logger.addFilter(ContextTraceFilter())
