from dataclasses import dataclass


@dataclass(frozen=True)
class TransformerBackendStatus:
    classifier: str
    embedder: str


class BertCategoryClassifier:
    # Provides a Hugging Face BERT classification adapter for trained local models.
    def __init__(self, model_path: str) -> None:
        try:
            from transformers import BertForSequenceClassification, BertTokenizer
        except ImportError as exc:  # pragma: no cover - optional dependency.
            raise RuntimeError("Install transformers to enable BERT classification") from exc

        self.tokenizer = BertTokenizer.from_pretrained(model_path)
        self.model = BertForSequenceClassification.from_pretrained(model_path)
        self.model.eval()

    # Predicts the highest-confidence category for a cleaned incident description.
    def predict(self, text: str) -> tuple[str, float]:
        import torch

        encoded = self.tokenizer(
            text,
            truncation=True,
            padding=True,
            max_length=256,
            return_tensors="pt",
        )
        with torch.no_grad():
            logits = self.model(**encoded).logits
            probabilities = torch.softmax(logits, dim=-1)[0]
            best_index = int(torch.argmax(probabilities).item())
        label = self.model.config.id2label.get(best_index, str(best_index))
        return label, round(float(probabilities[best_index].item()), 4)


class SentenceBertEmbedder:
    # Provides a Sentence-BERT adapter for dense semantic similarity embeddings.
    def __init__(self, model_name: str) -> None:
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as exc:  # pragma: no cover - optional dependency.
            raise RuntimeError("Install sentence-transformers to enable SBERT retrieval") from exc

        self.model = SentenceTransformer(model_name)

    # Generates a dense vector for a single text input.
    def encode(self, text: str) -> list[float]:
        return self.model.encode(text).tolist()
