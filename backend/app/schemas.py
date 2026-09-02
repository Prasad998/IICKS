from pydantic import BaseModel, Field


class AnalyzeRequest(BaseModel):
    description: str = Field(..., min_length=5, max_length=2000)
    top_k: int = Field(default=5, ge=1, le=10)


class SimilarTicket(BaseModel):
    ticket_id: str
    description: str
    category: str
    resolution: str
    similarity: float


class KnowledgeArticle(BaseModel):
    article_id: str
    title: str
    category: str
    excerpt: str
    relevance: float


class AnalyzeResponse(BaseModel):
    category: str
    confidence: float
    similar_tickets: list[SimilarTicket]
    knowledge_articles: list[KnowledgeArticle]
    cached: bool = False
    model_backend: str = "tfidf-local"


class HealthResponse(BaseModel):
    status: str
    incidents_loaded: int
    articles_loaded: int = 0
    model_backend: str = "tfidf-local"
    redis_cache: str = "disabled"
    kafka_events: str = "disabled"


class SubmitResponse(BaseModel):
    request_id: str
    status: str
    kafka_topic: str


class EvaluateRequest(BaseModel):
    test_ratio: float = Field(default=0.2, ge=0.1, le=0.5)


class EvaluationClassMetrics(BaseModel):
    category: str
    precision: float
    recall: float
    f1: float
    support: int
    categorical_accuracy: float


class EvaluationReport(BaseModel):
    model_backend: str
    train_size: int
    test_size: int
    accuracy: float
    macro_precision: float
    macro_recall: float
    macro_f1: float
    confusion_matrix: dict[str, dict[str, int]]
    class_metrics: list[EvaluationClassMetrics]
    category_labels: list[str]
    categorical_accuracy: dict[str, float]
    holdout_strategy: str
