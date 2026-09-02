import csv
import math
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path

from .nlp_math import cosine_similarity, normalize
from .preprocessing import clean_text
from .schemas import AnalyzeResponse, KnowledgeArticle, SimilarTicket
from .vector_store import SparseVectorIndex


TOKEN_PATTERN = re.compile(r"[a-z0-9]+")
STOPWORDS = {
    "a",
    "after",
    "an",
    "and",
    "are",
    "as",
    "by",
    "for",
    "from",
    "in",
    "is",
    "of",
    "on",
    "or",
    "the",
    "to",
    "with",
}


@dataclass(frozen=True)
class Incident:
    ticket_id: str
    description: str
    category: str
    resolution: str


@dataclass(frozen=True)
class Article:
    article_id: str
    title: str
    category: str
    content: str


class TfidfVectorizer:
    """Small local TF-IDF vectorizer used as an offline SBERT-style retrieval fallback."""

    # Initializes the vectorizer vocabulary and inverse document frequency store.
    def __init__(self) -> None:
        self.idf: dict[str, float] = {}
        self.vocabulary: set[str] = set()

    # Builds TF-IDF weights from the corpus used for classification and retrieval.
    def fit(self, documents: list[str]) -> None:
        doc_count = len(documents)
        document_frequency: Counter[str] = Counter()
        for document in documents:
            document_frequency.update(set(tokenize(document)))

        self.vocabulary = set(document_frequency)
        self.idf = {
            token: math.log((1 + doc_count) / (1 + frequency)) + 1
            for token, frequency in document_frequency.items()
        }

    # Converts free text into a normalized sparse TF-IDF vector.
    def transform(self, document: str) -> dict[str, float]:
        counts = Counter(tokenize(document))
        if not counts:
            return {}

        max_count = max(counts.values())
        vector = {
            token: (count / max_count) * self.idf.get(token, 1.0)
            for token, count in counts.items()
            if token in self.vocabulary
        }
        return normalize(vector)


class IncidentNlpEngine:
    # Wires data sources and model state for the incident analysis pipeline.
    def __init__(
        self,
        incidents_path: Path | None,
        articles_path: Path | None,
        model_backend: str = "tfidf",
        bert_model_path: str | None = None,
        sbert_model_name: str | None = None,
    ) -> None:
        self.incidents_path = incidents_path
        self.articles_path = articles_path
        self.incidents: list[Incident] = []
        self.articles: list[Article] = []
        self.vectorizer = TfidfVectorizer()
        self.incident_vectors: dict[str, dict[str, float]] = {}
        self.article_vectors: dict[str, dict[str, float]] = {}
        self.category_centroids: dict[str, dict[str, float]] = {}
        self.ticket_index: SparseVectorIndex[Incident] = SparseVectorIndex()
        self.article_index: SparseVectorIndex[Article] = SparseVectorIndex()

        # MODEL_BACKEND selects an optional adapter from transformer_backends.py.
        # If the requested backend can't be loaded (dependency missing, artifacts
        # missing, bad path), this degrades to the always-available TF-IDF path
        # rather than crashing the whole service - so a bad MODEL_BACKEND value
        # in an env file can't take the API down.
        self.model_backend = "tfidf-local"
        self.bert_classifier = None
        self.sbert_embedder = None

        if model_backend == "bert":
            self.bert_classifier = _try_load_bert(bert_model_path)
            if self.bert_classifier is not None:
                self.model_backend = "bert-local"
        elif model_backend == "sbert":
            self.sbert_embedder = _try_load_sbert(sbert_model_name)
            if self.sbert_embedder is not None:
                self.model_backend = "sbert-local"

    # Loads datasets and prepares vectors, article indexes, and category centroids.
    def load(self) -> None:
        if self.incidents_path is None or self.articles_path is None:
            raise ValueError("load() requires incidents_path and articles_path")
        self.load_from_records(
            load_incidents(self.incidents_path),
            load_articles(self.articles_path),
        )

    # Loads pre-read records and rebuilds all derived indexes in memory.
    def load_from_records(self, incidents: list[Incident], articles: list[Article]) -> None:
        self.incidents = incidents
        self.articles = articles

        if self.sbert_embedder is not None:
            # Dense SBERT embeddings, adapted into the same {index: value} shape
            # the sparse TF-IDF vectors use, so centroid averaging and cosine
            # similarity below are identical regardless of which backend produced
            # the vectors - only this loading step differs.
            self.incident_vectors = {
                incident.ticket_id: _dense_to_sparse(
                    self.sbert_embedder.encode(f"{incident.description} {incident.resolution}")
                )
                for incident in self.incidents
            }
            self.article_vectors = {
                article.article_id: _dense_to_sparse(
                    self.sbert_embedder.encode(f"{article.title} {article.content} {article.category}")
                )
                for article in self.articles
            }
        else:
            documents = [i.description for i in self.incidents] + [
                f"{a.title} {a.content}" for a in self.articles
            ]
            self.vectorizer.fit(documents)

            self.incident_vectors = {
                incident.ticket_id: self.vectorizer.transform(
                    f"{incident.description} {incident.resolution}"
                )
                for incident in self.incidents
            }
            self.article_vectors = {
                article.article_id: self.vectorizer.transform(
                    f"{article.title} {article.content} {article.category}"
                )
                for article in self.articles
            }

        self.category_centroids = build_category_centroids(
            self.incidents, self.incident_vectors
        )
        self.ticket_index.build(
            {incident.ticket_id: incident for incident in self.incidents},
            self.incident_vectors,
        )
        self.article_index.build(
            {article.article_id: article for article in self.articles},
            self.article_vectors,
        )

    # Runs the full classification, similar-ticket, and knowledge-article workflow.
    def analyze(self, description: str, top_k: int = 5) -> AnalyzeResponse:
        if not self.incidents:
            self.load()

        query_vector = self._vectorize_query(description)

        if self.bert_classifier is not None:
            category, confidence = self.bert_classifier.predict(clean_text(description))
        else:
            category, confidence = self.predict_category(query_vector)

        similar_tickets = self.find_similar_tickets(query_vector, top_k)
        articles = self.find_articles(query_vector, category, top_k=3)

        return AnalyzeResponse(
            category=category,
            confidence=confidence,
            similar_tickets=similar_tickets,
            knowledge_articles=articles,
            model_backend=self.model_backend,
        )

    # Builds the query vector using whichever backend (TF-IDF or SBERT) is active.
    def _vectorize_query(self, description: str) -> dict[str, float]:
        if self.sbert_embedder is not None:
            return _dense_to_sparse(self.sbert_embedder.encode(description))
        return self.vectorizer.transform(description)

    # Scores the query against category centroids and returns the best label.
    def predict_category(self, query_vector: dict[str, float]) -> tuple[str, float]:
        scores = {
            category: cosine_similarity(query_vector, centroid)
            for category, centroid in self.category_centroids.items()
        }
        if not scores:
            return "Uncategorized", 0.0

        best_category = max(scores, key=scores.get)
        positive_scores = [max(score, 0.0) for score in scores.values()]
        denominator = sum(positive_scores) or 1.0
        confidence = max(scores[best_category], 0.0) / denominator
        return best_category, round(confidence, 4)

    # Ranks historical incidents by cosine similarity to the incoming ticket.
    def find_similar_tickets(
        self, query_vector: dict[str, float], top_k: int
    ) -> list[SimilarTicket]:
        scored = []
        for result in self.ticket_index.search(query_vector, top_k):
            scored.append((result.score, result.item))

        return [
            SimilarTicket(
                ticket_id=incident.ticket_id,
                description=incident.description,
                category=incident.category,
                resolution=incident.resolution,
                similarity=round(score, 4),
            )
            for score, incident in scored[:top_k]
        ]

    # Ranks knowledge articles with a semantic score and category-aware boost.
    def find_articles(
        self, query_vector: dict[str, float], category: str, top_k: int
    ) -> list[KnowledgeArticle]:
        scored = []
        for result in self.article_index.search(query_vector, top_k):
            article = result.item
            semantic_score = result.score
            category_boost = 0.15 if article.category == category else 0.0
            scored.append((semantic_score + category_boost, article))

        scored.sort(key=lambda item: item[0], reverse=True)
        return [
            KnowledgeArticle(
                article_id=article.article_id,
                title=article.title,
                category=article.category,
                excerpt=article.content,
                relevance=round(score, 4),
            )
            for score, article in scored[:top_k]
        ]


# Adapts a dense embedding into the sparse {index: value} shape the existing
# cosine-similarity and centroid-averaging code already knows how to handle,
# so SBERT and TF-IDF vectors can flow through one shared pipeline.
def _dense_to_sparse(vector: list[float]) -> dict[str, float]:
    return {str(index): value for index, value in enumerate(vector)}


# Attempts to load a fine-tuned BERT classifier; returns None on any failure
# (missing dependency, missing artifacts, bad path) so the caller can fall
# back to the always-available TF-IDF path instead of crashing at startup.
def _try_load_bert(model_path: str | None):
    if not model_path:
        print("MODEL_BACKEND=bert requested but BERT_MODEL_PATH is not set; using tfidf-local instead.")
        return None
    try:
        from .transformer_backends import BertCategoryClassifier

        return BertCategoryClassifier(model_path)
    except Exception as exc:  # noqa: BLE001 - any load failure should degrade gracefully
        print(f"Could not load BERT classifier from '{model_path}' ({exc}); using tfidf-local instead.")
        return None


# Attempts to load an SBERT embedder; same fallback contract as _try_load_bert.
def _try_load_sbert(model_name: str | None):
    if not model_name:
        print("MODEL_BACKEND=sbert requested but SBERT_MODEL_NAME is not set; using tfidf-local instead.")
        return None
    try:
        from .transformer_backends import SentenceBertEmbedder

        return SentenceBertEmbedder(model_name)
    except Exception as exc:  # noqa: BLE001
        print(f"Could not load SBERT embedder '{model_name}' ({exc}); using tfidf-local instead.")
        return None


# Normalizes free text into searchable lowercase tokens.
def tokenize(text: str) -> list[str]:
    return [
        token
        for token in TOKEN_PATTERN.findall(clean_text(text))
        if token not in STOPWORDS and len(token) > 1
    ]


# Builds per-category centroid vectors from labeled historical incidents.
def build_category_centroids(
    incidents: list[Incident], vectors: dict[str, dict[str, float]]
) -> dict[str, dict[str, float]]:
    grouped: dict[str, list[dict[str, float]]] = defaultdict(list)
    for incident in incidents:
        grouped[incident.category].append(vectors[incident.ticket_id])

    centroids = {}
    for category, category_vectors in grouped.items():
        combined: Counter[str] = Counter()
        for vector in category_vectors:
            combined.update(vector)
        centroids[category] = normalize(
            {
                token: value / len(category_vectors)
                for token, value in combined.items()
            }
        )
    return centroids


# Reads historical incident records from the CSV data source.
def load_incidents(path: Path) -> list[Incident]:
    with path.open(newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        return [
            Incident(
                ticket_id=row["ticket_id"],
                description=row["description"],
                category=row["category"],
                resolution=row["resolution"],
            )
            for row in reader
        ]


# Reads knowledge-base article records from the CSV data source.
def load_articles(path: Path) -> list[Article]:
    with path.open(newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        return [
            Article(
                article_id=row["article_id"],
                title=row["title"],
                category=row["category"],
                content=row["content"],
            )
            for row in reader
        ]
