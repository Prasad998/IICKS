import os
from dataclasses import dataclass


def _enabled(value: str | None, default: bool = False) -> bool:
    # Parses boolean environment flags in a shell-friendly way.
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    kafka_bootstrap_servers: str = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
    kafka_input_topic: str = os.getenv("KAFKA_INPUT_TOPIC", "incident.requests")
    kafka_output_topic: str = os.getenv("KAFKA_OUTPUT_TOPIC", "incident.analysis")
    cache_ttl_seconds: int = int(os.getenv("CACHE_TTL_SECONDS", "900"))
    enable_redis: bool = _enabled(os.getenv("ENABLE_REDIS"))
    enable_kafka: bool = _enabled(os.getenv("ENABLE_KAFKA"))
    model_backend: str = os.getenv("MODEL_BACKEND", "tfidf")
    bert_model_path: str | None = os.getenv("BERT_MODEL_PATH")
    sbert_model_name: str | None = os.getenv("SBERT_MODEL_NAME")


# Shared runtime settings for cache, Kafka, and model backend selection.
settings = Settings()
