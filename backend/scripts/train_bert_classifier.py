"""Fine-tunes a BERT classifier on incidents.csv and saves it for MODEL_BACKEND=bert.

IMPORTANT: this script needs internet access (to download the base
bert-base-uncased checkpoint from Hugging Face on first run) and the ML
dependencies in requirements-ml.txt. It is not run automatically - you run it
yourself, once you're happy with the size/diversity of incidents.csv.

What it does:
  1. Loads incidents.csv and reuses the exact same stratified 80/20 holdout
     split that /api/evaluate uses, so you can compare BERT's held-out
     accuracy against the TF-IDF baseline on an identical test set.
  2. Fine-tunes bert-base-uncased as a 5-way sequence classifier on the
     training split.
  3. Evaluates on the held-out test split and prints accuracy.
  4. Saves the fine-tuned model + tokenizer to backend/models/bert-category-classifier/
     with the category label mapping baked in, so BertCategoryClassifier
     (transformer_backends.py) can load it directly.

After it finishes, point the running API at it:
    export MODEL_BACKEND=bert
    export BERT_MODEL_PATH=./models/bert-category-classifier
    python -m uvicorn app.main:app --reload --port 8000

Usage (from backend/, with requirements-ml.txt installed):
    python scripts/train_bert_classifier.py
"""

import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

from app.evaluation import stratified_holdout  # noqa: E402
from app.nlp_engine import load_incidents  # noqa: E402
from app.preprocessing import clean_text  # noqa: E402

DATA_PATH = BACKEND_DIR / "data" / "incidents.csv"
OUTPUT_DIR = BACKEND_DIR / "models" / "bert-category-classifier"
EPOCHS = 4
BATCH_SIZE = 16
LEARNING_RATE = 2e-5
MAX_LENGTH = 128


def main() -> None:
    try:
        import torch
        from torch.utils.data import DataLoader, Dataset
        from transformers import BertForSequenceClassification, BertTokenizer
    except ImportError as exc:
        raise SystemExit(
            "This script needs the ML dependencies. Run:\n"
            "  pip install -r requirements-ml.txt\n"
            f"Missing: {exc}"
        )

    incidents = load_incidents(DATA_PATH)
    split = stratified_holdout(incidents, test_ratio=0.2)
    labels = sorted({incident.category for incident in incidents})
    label2id = {label: index for index, label in enumerate(labels)}
    id2label = {index: label for label, index in label2id.items()}

    print(f"Training on {len(split.train)} incidents, evaluating on {len(split.test)} "
          f"held-out incidents, across {len(labels)} categories: {labels}")

    tokenizer = BertTokenizer.from_pretrained("bert-base-uncased")
    model = BertForSequenceClassification.from_pretrained(
        "bert-base-uncased",
        num_labels=len(labels),
        id2label=id2label,
        label2id=label2id,
    )

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model.to(device)
    print(f"Using device: {device}")

    class IncidentDataset(Dataset):
        def __init__(self, records):
            self.records = records

        def __len__(self):
            return len(self.records)

        def __getitem__(self, index):
            incident = self.records[index]
            text = clean_text(f"{incident.description} {incident.resolution}")
            encoded = tokenizer(
                text,
                truncation=True,
                padding="max_length",
                max_length=MAX_LENGTH,
                return_tensors="pt",
            )
            return {
                "input_ids": encoded["input_ids"].squeeze(0),
                "attention_mask": encoded["attention_mask"].squeeze(0),
                "labels": torch.tensor(label2id[incident.category], dtype=torch.long),
            }

    train_loader = DataLoader(IncidentDataset(split.train), batch_size=BATCH_SIZE, shuffle=True)
    test_loader = DataLoader(IncidentDataset(split.test), batch_size=BATCH_SIZE)

    optimizer = torch.optim.AdamW(model.parameters(), lr=LEARNING_RATE)

    model.train()
    for epoch in range(1, EPOCHS + 1):
        total_loss = 0.0
        for batch in train_loader:
            batch = {key: value.to(device) for key, value in batch.items()}
            optimizer.zero_grad()
            outputs = model(**batch)
            outputs.loss.backward()
            optimizer.step()
            total_loss += outputs.loss.item()
        print(f"epoch {epoch}/{EPOCHS} - avg training loss: {total_loss / len(train_loader):.4f}")

    model.eval()
    correct = 0
    total = 0
    with torch.no_grad():
        for batch in test_loader:
            labels_batch = batch["labels"].to(device)
            inputs = {key: value.to(device) for key, value in batch.items() if key != "labels"}
            logits = model(**inputs).logits
            predictions = torch.argmax(logits, dim=-1)
            correct += int((predictions == labels_batch).sum().item())
            total += labels_batch.size(0)

    accuracy = correct / total if total else 0.0
    print(f"Held-out test accuracy: {accuracy:.4f} ({correct}/{total})")
    print("Compare this against the TF-IDF baseline from POST /api/evaluate on the same data.")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    model.save_pretrained(OUTPUT_DIR)
    tokenizer.save_pretrained(OUTPUT_DIR)
    print(f"Saved fine-tuned model to {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
