"""Collect current TfL road disruption records."""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


API_URL = "https://api.tfl.gov.uk/Road/all/Disruption"

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = PROJECT_ROOT / "data/raw/tfl"


def collect():
    print("=== TfL ROAD DISRUPTION INGESTION ===")

    request = Request(
        API_URL,
        headers={
            "Accept": "application/json",
            "User-Agent": "UK-RoadPulse/0.1",
        },
    )

    try:
        with urlopen(request, timeout=30) as response:
            status = response.status
            payload = json.load(response)

    except (HTTPError, URLError, TimeoutError) as exc:
        print(f"API request failed: {exc}")
        return 1

    except json.JSONDecodeError as exc:
        print(f"Invalid JSON response: {exc}")
        return 1

    if not isinstance(payload, list):
        print("Unexpected response structure.")
        return 1

    collected_at = datetime.now(timezone.utc)

    RAW_DIR.mkdir(parents=True, exist_ok=True)

    filename = (
        "tfl_disruptions_"
        + collected_at.strftime("%Y%m%dT%H%M%SZ")
        + ".json"
    )

    destination = RAW_DIR / filename

    snapshot = {
        "source": "tfl",
        "endpoint": API_URL,
        "collected_at_utc": collected_at.isoformat(),
        "record_count": len(payload),
        "records": payload,
    }

    with destination.open("w", encoding="utf-8") as file:
        json.dump(snapshot, file, indent=2)

    print(f"HTTP status: {status}")
    print(f"Records retrieved: {len(payload)}")
    print(f"Collected at UTC: {collected_at.isoformat()}")
    print(f"Snapshot saved: {destination}")

    if payload:
        print("\n=== SAMPLE RECORD STRUCTURE ===")
        print("Available fields:")
        print(", ".join(sorted(payload[0].keys())))

        print("\n=== SAMPLE DISRUPTIONS ===")
        for record in payload[:3]:
            print({
                "id": record.get("id"),
                "severity": record.get("severity"),
                "category": record.get("category"),
                "location": record.get("location"),
                "startDate": record.get("startDate"),
            })

    return 0


if __name__ == "__main__":
    sys.exit(collect())
