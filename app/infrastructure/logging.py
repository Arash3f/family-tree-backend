import logging

from .context import get_trace_id


class ContextTraceFilter(logging.Filter):
    def filter(self, record):
        record.trace_id = get_trace_id()
        return True


def configure_logging() -> None:
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | trace_id=%(trace_id)s | %(message)s"
    )

    handler = logging.StreamHandler()
    handler.setFormatter(formatter)

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)
    logger.addFilter(ContextTraceFilter())
