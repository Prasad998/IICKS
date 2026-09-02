"""Read-only dataset quality report for incidents.csv and kb_articles.csv.

Run this any time you add new tickets or articles - especially before trusting
a change in /api/evaluate's accuracy number. It flags the two problems that
actually hurt this TF-IDF classifier: exact-duplicate text (inflates category
centroids without adding real signal) and category imbalance (skews which
category "wins" ties).

Usage (from backend/):
    python scripts/check_dataset_quality.py
"""

import csv
from collections import Counter
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parents[1] / "data"

# Below this ratio of unique-to-total rows, print a warning rather than just
# a number - this threshold is a judgment call, not a hard system requirement.
DUPLICATION_WARNING_RATIO = 0.5


def report_incidents(path: Path) -> None:
    with path.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    total = len(rows)
    unique_descriptions = len({r["description"] for r in rows})
    categories = Counter(r["category"] for r in rows)
    duplicate_counts = Counter(r["description"] for r in rows)
    top_duplicates = [item for item in duplicate_counts.most_common(5) if item[1] > 1]

    print(f"incidents.csv - {total} rows, {unique_descriptions} unique descriptions "
          f"({unique_descriptions / total:.0%} unique)")
    print(f"  category balance: {dict(categories)}")
    if unique_descriptions / total < DUPLICATION_WARNING_RATIO:
        print("  WARNING: fewer than half the rows are textually unique. The category "
              "centroids and similarity search are effectively trained on far less "
              "real data than the row count suggests.")
    if top_duplicates:
        print("  most-repeated descriptions:")
        for description, count in top_duplicates:
            print(f"    x{count}: {description}")
    print()


def report_articles(path: Path) -> None:
    with path.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    total = len(rows)
    unique_titles = len({r["title"] for r in rows})
    categories = Counter(r["category"] for r in rows)
    duplicate_counts = Counter(r["title"] for r in rows)
    top_duplicates = [item for item in duplicate_counts.most_common(5) if item[1] > 1]

    print(f"kb_articles.csv - {total} rows, {unique_titles} unique titles "
          f"({unique_titles / total:.0%} unique)")
    print(f"  category balance: {dict(categories)}")
    if unique_titles / total < DUPLICATION_WARNING_RATIO:
        print("  WARNING: fewer than half the rows are textually unique.")
    if top_duplicates:
        print("  most-repeated titles:")
        for title, count in top_duplicates:
            print(f"    x{count}: {title}")
    print()


def main() -> None:
    report_incidents(DATA_DIR / "incidents.csv")
    report_articles(DATA_DIR / "kb_articles.csv")


if __name__ == "__main__":
    main()
