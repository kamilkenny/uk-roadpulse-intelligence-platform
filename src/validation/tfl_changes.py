"""Compare TfL snapshots and validate map coordinates."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data/raw/tfl"


def coordinates_valid(value):
    if not value:
        return False

    try:
        obj = json.loads(value) if isinstance(value, str) else value

        if obj.get("type") != "Point":
            return False

        coords = obj.get("coordinates", [])

        return (
            len(coords) >= 2
            and -180 <= float(coords[0]) <= 180
            and -90 <= float(coords[1]) <= 90
        )
    except (ValueError, TypeError, AttributeError):
        return False


def main():
    files = sorted(RAW.glob("tfl_disruptions_*.json"))

    if len(files) < 2:
        raise SystemExit("At least two snapshots are required.")

    with files[-2].open(encoding="utf-8") as f:
        previous = json.load(f)

    with files[-1].open(encoding="utf-8") as f:
        current = json.load(f)

    old = {
        r["id"]: r
        for r in previous["records"]
        if r.get("id")
    }

    new = {
        r["id"]: r
        for r in current["records"]
        if r.get("id")
    }

    added = new.keys() - old.keys()
    disappeared = old.keys() - new.keys()

    updated = {
        key
        for key in old.keys() & new.keys()
        if old[key].get("lastModifiedTime")
        != new[key].get("lastModifiedTime")
        or old[key] != new[key]
    }

    valid_coordinates = sum(
        coordinates_valid(r.get("point"))
        for r in current["records"]
    )

    print("\n=== ROADPULSE CHANGE DETECTION ===")
    print("Previous:", previous["collected_at_utc"])
    print("Current:", current["collected_at_utc"])
    print("Previous records:", len(old))
    print("Current records:", len(new))
    print("New incidents:", len(added))
    print("Updated incidents:", len(updated))
    print("Disappeared incidents:", len(disappeared))
    print("Valid map coordinates:", valid_coordinates)

    print("\nSample new IDs:", sorted(added)[:5])
    print("Sample updated IDs:", sorted(updated)[:5])
    print("Sample disappeared IDs:", sorted(disappeared)[:5])

    print("\nNOTE: Disappeared does not necessarily mean resolved.")
    print("A source may remove or filter an incident.")

    report = {
        "previous_collection": previous["collected_at_utc"],
        "current_collection": current["collected_at_utc"],
        "new_count": len(added),
        "updated_count": len(updated),
        "disappeared_count": len(disappeared),
        "valid_coordinate_count": valid_coordinates,
        "new_ids": sorted(added),
        "updated_ids": sorted(updated),
        "disappeared_ids": sorted(disappeared),
    }

    output = RAW / "latest_change_report.json"
    output.write_text(json.dumps(report, indent=2))

    print("\nChange report saved:", output)


if __name__ == "__main__":
    main()
