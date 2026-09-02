from dataclasses import dataclass
from typing import Generic, TypeVar

from .nlp_math import cosine_similarity


T = TypeVar("T")


@dataclass(frozen=True)
class VectorSearchResult(Generic[T]):
    score: float
    item: T


class SparseVectorIndex(Generic[T]):
    # Maintains an in-memory sparse-vector index for cosine similarity search.
    def __init__(self) -> None:
        self._items: dict[str, T] = {}
        self._vectors: dict[str, dict[str, float]] = {}

    # Replaces the index contents with item and vector mappings.
    def build(self, items: dict[str, T], vectors: dict[str, dict[str, float]]) -> None:
        self._items = items
        self._vectors = vectors

    # Returns the highest-scoring items for a query vector.
    def search(self, query_vector: dict[str, float], top_k: int) -> list[VectorSearchResult[T]]:
        scored = [
            VectorSearchResult(
                score=cosine_similarity(query_vector, vector),
                item=self._items[item_id],
            )
            for item_id, vector in self._vectors.items()
        ]
        scored.sort(key=lambda result: result.score, reverse=True)
        return scored[:top_k]
