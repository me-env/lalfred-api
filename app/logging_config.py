import logging
import sys

from app.config import settings

_configured = False


def configure_logging() -> None:
    """Ensure application loggers emit INFO+ to stderr when OTLP is not wired.

    Uvicorn configures its own loggers; ``app.*`` loggers propagate to the root logger,
    which defaults to WARNING, so INFO lines were invisible unless OpenTelemetry added a
    root handler (only when ``otel_exporter_otlp_endpoint`` is set).
    """
    global _configured
    if settings.env == "test" or _configured:
        return
    _configured = True

    app_logger = logging.getLogger("app")
    app_logger.setLevel(logging.INFO)

    handler = logging.StreamHandler(sys.stderr)
    handler.setLevel(logging.INFO)
    handler.setFormatter(logging.Formatter("%(levelname)s [%(name)s] %(message)s"))
    app_logger.addHandler(handler)
