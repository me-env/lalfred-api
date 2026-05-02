import logging
from typing import override

from fastapi import FastAPI
from opentelemetry import trace
from opentelemetry._logs import set_logger_provider
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.logging import LoggingInstrumentor
from opentelemetry.instrumentation.logging.handler import LoggingHandler
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.sdk._logs import LoggerProvider
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from app.config import settings
from app.database import engine


def _parse_otel_headers(headers: str) -> dict[str, str]:
    parsed_headers: dict[str, str] = {}
    if not headers:
        return parsed_headers

    for header in headers.split(","):
        key, sep, value = header.partition("=")
        if sep and key and value:
            parsed_headers[key.strip()] = value.strip()

    return parsed_headers


class _ExcludeOtelInternalLogsFilter(logging.Filter):
    @override
    def filter(self, record: logging.LogRecord) -> bool:
        return not record.name.startswith("opentelemetry")


def setup_telemetry(app: FastAPI):
    resource = Resource.create({"service.name": settings.otel_service_name})
    provider = TracerProvider(resource=resource)
    logger_provider = LoggerProvider(resource=resource)

    headers = _parse_otel_headers(settings.otel_exporter_otlp_headers)
    protocol = settings.otel_exporter_otlp_protocol.strip().lower()

    if protocol == "http/protobuf":
        from opentelemetry.exporter.otlp.proto.http._log_exporter import \
            OTLPLogExporter
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import \
            OTLPSpanExporter

        exporter = OTLPSpanExporter(
            endpoint=settings.otel_exporter_otlp_endpoint,
            headers=headers or None,
        )
        log_exporter = OTLPLogExporter(
            endpoint=settings.otel_exporter_otlp_endpoint,
            headers=headers or None,
        )
    else:
        from opentelemetry.exporter.otlp.proto.grpc._log_exporter import \
            OTLPLogExporter
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import \
            OTLPSpanExporter

        exporter = OTLPSpanExporter(
            endpoint=settings.otel_exporter_otlp_endpoint,
            headers=headers or None,
            insecure=settings.otel_exporter_otlp_endpoint.startswith("http://"),
        )
        log_exporter = OTLPLogExporter(
            endpoint=settings.otel_exporter_otlp_endpoint,
            headers=headers or None,
            insecure=settings.otel_exporter_otlp_endpoint.startswith("http://"),
        )

    provider.add_span_processor(BatchSpanProcessor(exporter))
    logger_provider.add_log_record_processor(BatchLogRecordProcessor(log_exporter))

    trace.set_tracer_provider(provider)
    set_logger_provider(logger_provider)

    LoggingInstrumentor().instrument(set_logging_format=True, log_level=logging.INFO)
    otel_log_handler = LoggingHandler(level=logging.NOTSET, logger_provider=logger_provider)
    otel_log_handler.addFilter(_ExcludeOtelInternalLogsFilter())
    root_logger = logging.getLogger()
    root_logger.addHandler(otel_log_handler)
    FastAPIInstrumentor.instrument_app(app)
    SQLAlchemyInstrumentor().instrument(engine=engine.sync_engine)
    HTTPXClientInstrumentor().instrument()
