import json
from datetime import datetime, timezone
from uuid import uuid4

from .schemas import AnalyzeResponse
from .settings import Settings


class KafkaEventPublisher:
    # Publishes incident workflow events to Kafka with a no-op fallback.
    def __init__(self, settings: Settings) -> None:
        self.enabled = settings.enable_kafka
        self.input_topic = settings.kafka_input_topic
        self.output_topic = settings.kafka_output_topic
        self.producer = None
        self.error: str | None = None

        if not self.enabled:
            return

        try:
            from kafka import KafkaProducer

            self.producer = KafkaProducer(
                bootstrap_servers=settings.kafka_bootstrap_servers,
                value_serializer=lambda value: json.dumps(value).encode("utf-8"),
                key_serializer=lambda value: value.encode("utf-8"),
                request_timeout_ms=1500,
                api_version_auto_timeout_ms=1500,
            )
        except Exception as exc:  # pragma: no cover - depends on optional Kafka service.
            self.producer = None
            self.error = str(exc)

    # Emits a request event for asynchronous ticket intake pipelines.
    def publish_request(self, description: str, top_k: int) -> str:
        event_id = str(uuid4())
        payload = {
            "event_id": event_id,
            "event_type": "incident.analysis.requested",
            "description": description,
            "top_k": top_k,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        self._send(self.input_topic, event_id, payload)
        return event_id

    # Emits the completed inference result for downstream consumers.
    def publish_result(self, request_id: str, response: AnalyzeResponse) -> None:
        payload = {
            "event_id": str(uuid4()),
            "request_id": request_id,
            "event_type": "incident.analysis.completed",
            "result": response.dict(),
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        self._send(self.output_topic, request_id, payload)

    # Sends a serialized event if Kafka is connected.
    def _send(self, topic: str, key: str, payload: dict) -> None:
        if self.producer is None:
            return
        self.producer.send(topic, key=key, value=payload)
        self.producer.flush(timeout=1)

    # Reports whether Kafka publishing is configured and connected.
    def status(self) -> str:
        if not self.enabled:
            return "disabled"
        if self.producer is None:
            return f"unavailable: {self.error}"
        return "connected"
