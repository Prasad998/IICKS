import hashlib

from .schemas import AnalyzeResponse
from .settings import Settings


class AnalysisCache:
    # Wraps Redis response caching with a no-op fallback when Redis is unavailable.
    def __init__(self, settings: Settings) -> None:
        self.enabled = settings.enable_redis
        self.ttl_seconds = settings.cache_ttl_seconds
        self.client = None
        self.error: str | None = None

        if not self.enabled:
            return

        try:
            import redis

            self.client = redis.Redis.from_url(
                settings.redis_url,
                socket_connect_timeout=1,
                socket_timeout=1,
                decode_responses=True,
            )
            self.client.ping()
        except Exception as exc:  # pragma: no cover - depends on optional Redis service.
            self.client = None
            self.error = str(exc)

    # Creates a stable cache key for an analysis request.
    def key_for(self, description: str, top_k: int) -> str:
        digest = hashlib.sha256(f"{description}|{top_k}".encode("utf-8")).hexdigest()
        return f"incident-analysis:{digest}"

    # Returns a cached analysis response if Redis contains one.
    def get(self, description: str, top_k: int) -> AnalyzeResponse | None:
        if self.client is None:
            return None

        cached = self.client.get(self.key_for(description, top_k))
        if cached is None:
            return None
        response = AnalyzeResponse.parse_raw(cached)
        response.cached = True
        return response

    # Stores an analysis response in Redis for repeated-ticket acceleration.
    def set(self, description: str, top_k: int, response: AnalyzeResponse) -> None:
        if self.client is None:
            return

        self.client.setex(
            self.key_for(description, top_k),
            self.ttl_seconds,
            response.json(),
        )

    # Reports whether Redis caching is configured and connected.
    def status(self) -> str:
        if not self.enabled:
            return "disabled"
        if self.client is None:
            return f"unavailable: {self.error}"
        return "connected"
