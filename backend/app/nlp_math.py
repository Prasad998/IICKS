import math


# Scales a sparse vector to unit length for cosine-based scoring.
def normalize(vector: dict[str, float]) -> dict[str, float]:
    magnitude = math.sqrt(sum(value * value for value in vector.values()))
    if magnitude == 0:
        return vector
    return {token: value / magnitude for token, value in vector.items()}


# Computes cosine similarity between two sparse vectors.
def cosine_similarity(left: dict[str, float], right: dict[str, float]) -> float:
    if not left or not right:
        return 0.0
    smaller, larger = (left, right) if len(left) < len(right) else (right, left)
    return sum(value * larger.get(token, 0.0) for token, value in smaller.items())
