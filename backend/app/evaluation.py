from collections import defaultdict
from dataclasses import dataclass

from .nlp_engine import Article, Incident, IncidentNlpEngine
from .schemas import EvaluationClassMetrics, EvaluationReport


@dataclass(frozen=True)
class HoldoutSplit:
    train: list[Incident]
    test: list[Incident]


# Splits incidents into a deterministic stratified train/test partition.
def stratified_holdout(incidents: list[Incident], test_ratio: float = 0.2) -> HoldoutSplit:
    grouped: dict[str, list[Incident]] = defaultdict(list)
    for incident in incidents:
        grouped[incident.category].append(incident)

    train: list[Incident] = []
    test: list[Incident] = []
    for category in sorted(grouped):
        category_items = sorted(grouped[category], key=lambda item: item.ticket_id)
        split_index = max(1, int(round(len(category_items) * (1 - test_ratio))))
        split_index = min(split_index, len(category_items) - 1)
        train.extend(category_items[:split_index])
        test.extend(category_items[split_index:])

    return HoldoutSplit(train=train, test=test)


# Builds a confusion matrix keyed by actual and predicted category.
def build_confusion_matrix(
    labels: list[str], actual: list[str], predicted: list[str]
) -> dict[str, dict[str, int]]:
    matrix = {actual_label: {predicted_label: 0 for predicted_label in labels} for actual_label in labels}
    for actual_label, predicted_label in zip(actual, predicted):
        matrix[actual_label][predicted_label] += 1
    return matrix


# Computes precision, recall, F1, support, and per-category accuracy.
def compute_class_metrics(
    labels: list[str], actual: list[str], predicted: list[str]
) -> list[EvaluationClassMetrics]:
    metrics: list[EvaluationClassMetrics] = []
    for label in labels:
        tp = sum(1 for a, p in zip(actual, predicted) if a == label and p == label)
        fp = sum(1 for a, p in zip(actual, predicted) if a != label and p == label)
        fn = sum(1 for a, p in zip(actual, predicted) if a == label and p != label)
        support = sum(1 for a in actual if a == label)
        precision = tp / (tp + fp) if (tp + fp) else 0.0
        recall = tp / (tp + fn) if (tp + fn) else 0.0
        f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0
        metrics.append(
            EvaluationClassMetrics(
                category=label,
                precision=round(precision, 4),
                recall=round(recall, 4),
                f1=round(f1, 4),
                support=support,
                categorical_accuracy=round(recall, 4),
            )
        )
    return metrics


# Evaluates the incident classifier on a stratified holdout split.
def evaluate_incident_model(
    incidents: list[Incident],
    articles: list[Article],
    test_ratio: float = 0.2,
) -> EvaluationReport:
    split = stratified_holdout(incidents, test_ratio=test_ratio)
    engine = IncidentNlpEngine(incidents_path=None, articles_path=None)
    engine.load_from_records(split.train, articles)

    actual = [incident.category for incident in split.test]
    predicted = [engine.analyze(incident.description).category for incident in split.test]
    labels = sorted({incident.category for incident in incidents})
    total = len(actual)
    correct = sum(1 for a, p in zip(actual, predicted) if a == p)

    confusion_matrix = build_confusion_matrix(labels, actual, predicted)
    class_metrics = compute_class_metrics(labels, actual, predicted)
    return EvaluationReport(
        model_backend=engine.model_backend,
        train_size=len(split.train),
        test_size=len(split.test),
        accuracy=round(correct / total if total else 0.0, 4),
        macro_precision=round(sum(item.precision for item in class_metrics) / len(class_metrics), 4) if class_metrics else 0.0,
        macro_recall=round(sum(item.recall for item in class_metrics) / len(class_metrics), 4) if class_metrics else 0.0,
        macro_f1=round(sum(item.f1 for item in class_metrics) / len(class_metrics), 4) if class_metrics else 0.0,
        confusion_matrix=confusion_matrix,
        class_metrics=class_metrics,
        category_labels=labels,
        categorical_accuracy={item.category: item.categorical_accuracy for item in class_metrics},
        holdout_strategy=f"deterministic stratified holdout ({int(test_ratio * 100)}% test)",
    )
