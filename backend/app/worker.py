import json
from pathlib import Path

from .events import KafkaEventPublisher
from .nlp_engine import IncidentNlpEngine
from .settings import settings


BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"


# Runs a Kafka consumer loop for asynchronous incident analysis requests.
def main() -> None:
    try:
        from kafka import KafkaConsumer
    except ImportError as exc:
        raise SystemExit("Install kafka-python to run the Kafka worker") from exc

    engine = IncidentNlpEngine(
        incidents_path=DATA_DIR / "incidents.csv",
        articles_path=DATA_DIR / "kb_articles.csv",
    )
    engine.load()
    publisher = KafkaEventPublisher(settings)
    consumer = KafkaConsumer(
        settings.kafka_input_topic,
        bootstrap_servers=settings.kafka_bootstrap_servers,
        value_deserializer=lambda value: json.loads(value.decode("utf-8")),
        auto_offset_reset="earliest",
        enable_auto_commit=True,
        group_id="incident-nlp-workers",
    )

    for message in consumer:
        payload = message.value
        response = engine.analyze(
            payload["description"],
            top_k=payload.get("top_k", 5),
        )
        publisher.publish_result(payload["event_id"], response)


if __name__ == "__main__":
    main()
