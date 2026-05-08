import logging
import os

from fastapi import FastAPI
from opentelemetry import metrics, trace
from opentelemetry._logs import set_logger_provider
from opentelemetry.exporter.otlp.proto.http._log_exporter import OTLPLogExporter
from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.logging import LoggingInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.sdk._logs import LoggerProvider
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from app.config import settings
from app.database import engine


def setup_telemetry(app: FastAPI) -> None:
    if settings.env == "test":
        print("Test environment, skipping telemetry setup.")
        return

    # Endpoint, protocol and headers are read directly from OTEL_* env vars by
    # the SDK (with proper W3C Baggage decoding for headers).
    if not os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT"):
        print("OTEL_EXPORTER_OTLP_ENDPOINT not set, skipping telemetry setup.")
        return

    resource = Resource.create({
        "service.name": settings.otel_service_name,
        "environment": settings.env,
    })

    trace_provider = TracerProvider(resource=resource)
    trace_provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter()))

    logger_provider = LoggerProvider(resource=resource)
    logger_provider.add_log_record_processor(BatchLogRecordProcessor(OTLPLogExporter()))

    meter_provider = MeterProvider(
        resource=resource,
        metric_readers=[PeriodicExportingMetricReader(OTLPMetricExporter(), export_interval_millis=3000)],
    )

    trace.set_tracer_provider(trace_provider)
    set_logger_provider(logger_provider)
    metrics.set_meter_provider(meter_provider)

    # LoggingInstrumentor injects trace context into stdlib LogRecords, sets the
    # root logging format/level via basicConfig, and (since
    # OTEL_PYTHON_LOG_AUTO_INSTRUMENTATION defaults to true) installs a handler
    # on the root logger that ships logs to the global LoggerProvider.
    LoggingInstrumentor().instrument(set_logging_format=False, log_level=logging.INFO)

    FastAPIInstrumentor.instrument_app(app)
    SQLAlchemyInstrumentor().instrument(engine=engine.sync_engine)
    HTTPXClientInstrumentor().instrument()
    print("OTel configured.")
