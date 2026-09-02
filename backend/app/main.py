from pathlib import Path
from time import perf_counter

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware

try:
    from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest
except ImportError:  # pragma: no cover - fallback keeps the app runnable without optional metrics deps.
    CONTENT_TYPE_LATEST = "text/plain; version=0.0.4"

    class _NoOpMetric:
        def __init__(self, *args, **kwargs) -> None:
            pass

        def labels(self, *args, **kwargs):
            return self

        def inc(self, *args, **kwargs):
            return None

        def observe(self, *args, **kwargs):
            return None

    Counter = Histogram = _NoOpMetric

    def generate_latest() -> bytes:
        return (
            b"# HELP incident_api_requests_total Total HTTP requests handled by the incident API\n"
            b"# TYPE incident_api_requests_total counter\n"
            b"incident_api_requests_total 0\n"
            b"# HELP incident_api_request_duration_seconds Request latency for incident API endpoints\n"
            b"# TYPE incident_api_request_duration_seconds histogram\n"
            b"incident_api_request_duration_seconds_bucket{le=\"0.5\"} 0\n"
        )

from .cache import AnalysisCache
from .events import KafkaEventPublisher
from .evaluation import evaluate_incident_model
from .nlp_engine import IncidentNlpEngine
from .schemas import AnalyzeRequest, AnalyzeResponse, EvaluateRequest, EvaluationReport, HealthResponse, SubmitResponse
from .settings import settings


BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"

app = FastAPI(
    title="IBM Intelligent Incident Categorization & Knowledge Search",
    version="1.0.0",
    description="Enterprise-style incident classification and semantic knowledge search API.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


REQUEST_COUNT = Counter(
    "incident_api_requests_total",
    "Total HTTP requests handled by the incident API",
    ["method", "path", "status"],
)
REQUEST_LATENCY = Histogram(
    "incident_api_request_duration_seconds",
    "Request latency for incident API endpoints",
    ["method", "path"],
)
ANALYZE_CACHE_HIT = Counter(
    "incident_api_analyze_cache_hits_total",
    "Total cached analyze responses returned",
)
ANALYZE_CACHE_MISS = Counter(
    "incident_api_analyze_cache_misses_total",
    "Total analyze requests that required model inference",
)
EVALUATE_REQUESTS = Counter(
    "incident_api_evaluate_requests_total",
    "Total evaluation requests served",
)

engine = IncidentNlpEngine(
    incidents_path=DATA_DIR / "incidents.csv",
    articles_path=DATA_DIR / "kb_articles.csv",
    model_backend=settings.model_backend,
    bert_model_path=settings.bert_model_path,
    sbert_model_name=settings.sbert_model_name,
)
analysis_cache = AnalysisCache(settings)
event_publisher = KafkaEventPublisher(settings)


@app.middleware("http")
# Records request counts and latency for Prometheus scraping.
async def prometheus_metrics(request: Request, call_next):
    start = perf_counter()
    response = await call_next(request)
    duration = perf_counter() - start
    REQUEST_COUNT.labels(request.method, request.url.path, str(response.status_code)).inc()
    REQUEST_LATENCY.labels(request.method, request.url.path).observe(duration)
    return response


@app.on_event("startup")
# Loads the in-memory NLP index before serving API traffic.
def startup() -> None:
    engine.load()


@app.get("/health", response_model=HealthResponse)
# Reports service readiness and the current incident index size.
def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        incidents_loaded=len(engine.incidents),
        articles_loaded=len(engine.articles),
        model_backend=engine.model_backend,
        redis_cache=analysis_cache.status(),
        kafka_events=event_publisher.status(),
    )


@app.post("/api/analyze", response_model=AnalyzeResponse)
# Classifies an incident and returns ranked ticket and article matches.
def analyze_ticket(payload: AnalyzeRequest) -> AnalyzeResponse:
    cached = analysis_cache.get(payload.description, payload.top_k)
    if cached is not None:
        ANALYZE_CACHE_HIT.inc()
        return cached

    ANALYZE_CACHE_MISS.inc()
    request_id = event_publisher.publish_request(payload.description, payload.top_k)
    response = engine.analyze(payload.description, top_k=payload.top_k)
    analysis_cache.set(payload.description, payload.top_k, response)
    event_publisher.publish_result(request_id, response)
    return response


@app.post("/api/submit", response_model=SubmitResponse)
# Publishes an incident analysis request for asynchronous Kafka processing.
def submit_ticket(payload: AnalyzeRequest) -> SubmitResponse:
    request_id = event_publisher.publish_request(payload.description, payload.top_k)
    return SubmitResponse(
        request_id=request_id,
        status="queued" if event_publisher.producer is not None else "accepted-local",
        kafka_topic=event_publisher.input_topic,
    )


@app.post("/api/evaluate", response_model=EvaluationReport)
# Evaluates classifier correctness on a deterministic stratified holdout split.
def evaluate_model(payload: EvaluateRequest) -> EvaluationReport:
    EVALUATE_REQUESTS.inc()
    return evaluate_incident_model(
        engine.incidents,
        engine.articles,
        test_ratio=payload.test_ratio,
    )


@app.get("/api/examples")
# Provides curated sample tickets for frontend demonstrations.
def examples() -> list[dict[str, str]]:
    return [
        {
            "description": "Unable to login to SAP after password reset",
            "expected_category": "Authentication",
        },
        {
            "description": "VPN disconnects every 10 minutes on Cisco AnyConnect",
            "expected_category": "Network",
        },
        {
            "description": "Payroll batch job failed overnight with DB timeout",
            "expected_category": "Application",
        },
    ]


@app.get("/metrics")
# Exposes Prometheus metrics for Grafana or Prometheus scraping.
def metrics() -> Response:
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
