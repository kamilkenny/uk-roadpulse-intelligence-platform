"""Profile TfL road disruption snapshot quality."""

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data/raw/tfl"


def parse_date(value):
    if not value:
        return None
    try:
        return datetime.fromisoformat(
            value.replace("Z", "+00:00")
        )
    except (ValueError, TypeError, AttributeError):
        return None


def main():
    snapshots = sorted(RAW.glob("tfl_disruptions_*.json"))

    if not snapshots:
        raise SystemExit("No TfL snapshots found.")

    latest = snapshots[-1]

    with latest.open(encoding="utf-8") as file:
        snapshot = json.load(file)

    records = snapshot["records"]
    ids = [r.get("id") for r in records]
    valid_ids = [x for x in ids if x]

    severities = Counter(
        r.get("severity") or "Unknown"
        for r in records
    )

    categories = Counter(
        r.get("category") or "Unknown"
        for r in records
    )

    start_dates = [
        parse_date(r.get("startDateTime"))
        for r in records
    ]

    modified_dates = [
        parse_date(r.get("lastModifiedTime"))
        for r in records
    ]

    update_dates = [
        parse_date(r.get("currentUpdateDateTime"))
        for r in records
    ]

    def count_dates(values):
        return sum(x is not None for x in values)

    def newest(values):
        valid = [x for x in values if x]
        return max(valid) if valid else None

    with_geography = sum(
        bool(r.get("geography") or r.get("point"))
        for r in records
    )

    print("\n=== ROADPULSE DATA QUALITY REPORT ===")
    print("Snapshot:", latest.name)
    print("Collected:", snapshot["collected_at_utc"])
    print("Records:", len(records))
    print("Unique IDs:", len(set(valid_ids)))
    print("Missing IDs:", len(ids) - len(valid_ids))
    print("Duplicate IDs:", len(valid_ids) - len(set(valid_ids)))

    print("\n=== SEVERITY DISTRIBUTION ===")
    for name, count in severities.most_common():
        print(f"{name}: {count}")

    print("\n=== INCIDENT CATEGORIES ===")
    for name, count in categories.most_common():
        print(f"{name}: {count}")

    print("\n=== FIELD COMPLETENESS ===")
    print("Valid start dates:", count_dates(start_dates))
    print("Valid modified dates:", count_dates(modified_dates))
    print("Valid update dates:", count_dates(update_dates))
    print("Geography populated:", with_geography)

    print("\n=== SOURCE TIMESTAMPS ===")
    print("Latest modified:", newest(modified_dates))
    print("Latest current update:", newest(update_dates))

    collected = parse_date(snapshot["collected_at_utc"])
    modified = newest(modified_dates)

    if collected and modified:
        lag = (collected - modified).total_seconds() / 60
        print(f"Newest incident modification age: {lag:.1f} minutes")

    print("\nNOTE: Incident modification age is not")
    print("the same as API publication latency.")

    print("\n=== QUALITY CHECK COMPLETE ===")


if __name__ == "__main__":
    main()
