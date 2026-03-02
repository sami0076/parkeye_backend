"""
Parkeye Mock Data Seeder

Generates synthetic occupancy data and loads all mock files into Supabase.
Idempotent — safe to re-run without creating duplicates.

Usage:
    python mock/seed.py
"""

import csv
import json
import math
import os
import random
import sys
from pathlib import Path

from dotenv import load_dotenv
from supabase import create_client

MOCK_DIR = Path(__file__).parent
PROJECT_ROOT = MOCK_DIR.parent

load_dotenv(PROJECT_ROOT / ".env")

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_KEY"]

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


# ---------------------------------------------------------------------------
# Occupancy CSV generation
# ---------------------------------------------------------------------------

def sin_curve(hour: int, peak: int = 10, trough: int = 3) -> float:
    """Sinusoidal base occupancy: peaks at `peak` hour, troughs at `trough` hour."""
    period = 24
    phase = (2 * math.pi / period) * (hour - peak)
    return 0.5 * (1 + math.cos(phase))


def clamp(value: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, value))


def occupancy_color(pct: float) -> str:
    if pct < 0.6:
        return "green"
    if pct < 0.85:
        return "yellow"
    return "red"


def generate_occupancy_csv(lots: list[dict]) -> list[dict]:
    """
    Generate 24h x 7-day occupancy for every lot and write to CSV.
    Returns the rows so they can be inserted into the DB in the same run.
    """
    random.seed(42)
    rows: list[dict] = []

    for lot in lots:
        lot_id = lot["id"]
        capacity = lot["capacity"]
        # Larger lots tend to fill slightly less
        capacity_factor = 1.0 - (capacity / 20_000)

        for day in range(7):
            weekend = day >= 5
            weekend_factor = 0.4 if weekend else 1.0

            for hour in range(24):
                base = sin_curve(hour)
                noise = random.gauss(0, 0.05)
                pct = clamp(base * weekend_factor * capacity_factor + noise)
                color = occupancy_color(pct)
                rows.append({
                    "lot_id": lot_id,
                    "hour_of_day": hour,
                    "day_of_week": day,
                    "occupancy_pct": round(pct, 4),
                    "color": color,
                })

    csv_path = MOCK_DIR / "occupancy_history.csv"
    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(
            f, fieldnames=["lot_id", "hour_of_day", "day_of_week", "occupancy_pct", "color"]
        )
        writer.writeheader()
        writer.writerows(rows)

    print(f"  Generated {len(rows)} rows -> {csv_path}")
    return rows


# ---------------------------------------------------------------------------
# Supabase seeding helpers
# ---------------------------------------------------------------------------

def seed_lots(lots: list[dict]) -> None:
    existing = supabase.table("lots").select("name").execute()
    existing_names = {row["name"] for row in existing.data}

    to_insert = []
    for lot in lots:
        if lot["name"] not in existing_names:
            to_insert.append({
                "id": lot["id"],
                "name": lot["name"],
                "capacity": lot["capacity"],
                "permit_types": lot["permit_types"],
                "lat": lot["lat"],
                "lon": lot["lon"],
                "is_deck": lot["is_deck"],
                "floors": lot["floors"],
                "status": "open",
            })

    if to_insert:
        supabase.table("lots").insert(to_insert).execute()
        print(f"  Inserted {len(to_insert)} lots")
    else:
        print("  Lots already seeded — skipped")


def seed_occupancy(rows: list[dict]) -> None:
    existing = supabase.table("occupancy_snapshots").select("lot_id, hour_of_day, day_of_week").execute()
    existing_keys = {
        (r["lot_id"], r["hour_of_day"], r["day_of_week"]) for r in existing.data
    }

    to_insert = [
        r for r in rows
        if (r["lot_id"], r["hour_of_day"], r["day_of_week"]) not in existing_keys
    ]

    if not to_insert:
        print("  Occupancy snapshots already seeded — skipped")
        return

    # Insert in batches of 500 to avoid request-size limits
    batch_size = 500
    for i in range(0, len(to_insert), batch_size):
        batch = to_insert[i : i + batch_size]
        supabase.table("occupancy_snapshots").insert(batch).execute()

    print(f"  Inserted {len(to_insert)} occupancy snapshots")


def seed_events(events: list[dict]) -> None:
    existing = supabase.table("campus_events").select("title").execute()
    existing_titles = {row["title"] for row in existing.data}

    to_insert = [
        e for e in events if e["title"] not in existing_titles
    ]

    if to_insert:
        supabase.table("campus_events").insert(to_insert).execute()
        print(f"  Inserted {len(to_insert)} campus events")
    else:
        print("  Campus events already seeded — skipped")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    print("=== Parkeye Seed Script ===\n")

    with open(MOCK_DIR / "lots.json") as f:
        lots = json.load(f)

    with open(MOCK_DIR / "events.json") as f:
        events = json.load(f)

    print("[1/4] Generating occupancy CSV...")
    occupancy_rows = generate_occupancy_csv(lots)

    print("[2/4] Seeding lots...")
    seed_lots(lots)

    print("[3/4] Seeding occupancy snapshots...")
    seed_occupancy(occupancy_rows)

    print("[4/4] Seeding campus events...")
    seed_events(events)

    print("\nDone. All mock data loaded into Supabase.")


if __name__ == "__main__":
    try:
        main()
    except KeyError as exc:
        print(f"\nError: Missing environment variable {exc}")
        print("Make sure .env exists at the project root with SUPABASE_URL and SUPABASE_KEY")
        sys.exit(1)
    except Exception as exc:
        print(f"\nError: {exc}")
        sys.exit(1)
