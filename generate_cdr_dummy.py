"""
generate_cdr_dummy.py
─────────────────────
Generates a realistic synthetic CDR (Call Detail Record) CSV file for
testing the CDR Intelligence Module locally.

Usage:
    python generate_cdr_dummy.py

Output:
    dummy_cdr.csv  (written to the project root directory)

The script plants several calls from a specific target number
(9876543210) near a fixed crime scene coordinate so that the
proximity flagging feature can be immediately verified.
"""

import random
import pandas as pd
from datetime import datetime, timedelta

# ── Configuration ────────────────────────────────────────────────────────────
TOTAL_RECORDS    = 200
OUTPUT_FILE      = "dummy_cdr.csv"

# Target number — use this number in the UI to test timeline analysis
TARGET_NUMBER    = "9876543210"

# Crime scene location (Bengaluru — MG Road area)
CRIME_SCENE_LAT  = 12.9716
CRIME_SCENE_LON  = 77.5946

# Cell towers — mixture of far towers and a cluster NEAR the crime scene
CELL_TOWERS = [
    # Near-crime-scene towers (within 0.5 km) — will be flagged as leads
    {"id": "TOWER_CS_01", "lat": 12.9720, "lon": 77.5950},
    {"id": "TOWER_CS_02", "lat": 12.9712, "lon": 77.5940},
    {"id": "TOWER_CS_03", "lat": 12.9715, "lon": 77.5952},
    # Wider Bengaluru towers
    {"id": "TOWER_BLR_10", "lat": 12.9352, "lon": 77.6245},
    {"id": "TOWER_BLR_11", "lat": 13.0358, "lon": 77.5970},
    {"id": "TOWER_BLR_12", "lat": 12.9063, "lon": 77.5900},
    {"id": "TOWER_BLR_13", "lat": 12.9698, "lon": 77.7499},
    {"id": "TOWER_BLR_14", "lat": 12.8399, "lon": 77.6770},
    {"id": "TOWER_BLR_15", "lat": 13.0210, "lon": 77.4600},
    {"id": "TOWER_BLR_16", "lat": 12.9592, "lon": 77.6974},
    {"id": "TOWER_BLR_17", "lat": 12.9762, "lon": 77.5088},
    {"id": "TOWER_BLR_18", "lat": 12.9987, "lon": 77.6101},
]

# Phone numbers used in the simulation
PHONE_POOL = [
    TARGET_NUMBER,
    "9123456789", "9234567890", "9345678901", "9456789012",
    "9567890123", "9678901234", "9789012345", "9890123456",
    "9012345678", "8123456789", "8234567890",
]

# Time window: 48 hours up to "now"
END_TIME   = datetime(2026, 9, 1, 20, 0, 0)
START_TIME = END_TIME - timedelta(hours=48)


def random_datetime(start: datetime, end: datetime) -> datetime:
    delta = (end - start).total_seconds()
    return start + timedelta(seconds=random.uniform(0, delta))


def build_records(n: int) -> list[dict]:
    records = []

    # ── Planted proximity calls (target number near crime scene) ──────────
    planted_times = [
        datetime(2026, 8, 31, 21, 15, 0),   # evening before
        datetime(2026, 8, 31, 23, 47, 0),   # late night
        datetime(2026, 9,  1,  0, 12, 0),   # just after midnight (crime time)
        datetime(2026, 9,  1,  0, 58, 0),   # ~1 AM
    ]
    for ts in planted_times:
        tower = random.choice(CELL_TOWERS[:3])      # near-crime towers
        other = random.choice([p for p in PHONE_POOL if p != TARGET_NUMBER])
        records.append({
            "Caller_Number":   TARGET_NUMBER,
            "Receiver_Number": other,
            "DateTime":        ts.strftime("%Y-%m-%d %H:%M:%S"),
            "Call_Duration_Sec": random.randint(30, 300),
            "Cell_Tower_ID":   tower["id"],
            "Tower_Lat":       tower["lat"],
            "Tower_Lon":       tower["lon"],
        })

    # ── Target number calls far from crime scene (normal movement) ────────
    for _ in range(20):
        tower = random.choice(CELL_TOWERS[3:])
        other = random.choice([p for p in PHONE_POOL if p != TARGET_NUMBER])
        caller, receiver = (TARGET_NUMBER, other) if random.random() < 0.5 else (other, TARGET_NUMBER)
        records.append({
            "Caller_Number":   caller,
            "Receiver_Number": receiver,
            "DateTime":        random_datetime(START_TIME, END_TIME).strftime("%Y-%m-%d %H:%M:%S"),
            "Call_Duration_Sec": random.randint(5, 600),
            "Cell_Tower_ID":   tower["id"],
            "Tower_Lat":       tower["lat"],
            "Tower_Lon":       tower["lon"],
        })

    # ── Random background CDR noise ───────────────────────────────────────
    remaining = n - len(records)
    for _ in range(remaining):
        caller   = random.choice(PHONE_POOL)
        receiver = random.choice([p for p in PHONE_POOL if p != caller])
        tower    = random.choice(CELL_TOWERS)
        records.append({
            "Caller_Number":   caller,
            "Receiver_Number": receiver,
            "DateTime":        random_datetime(START_TIME, END_TIME).strftime("%Y-%m-%d %H:%M:%S"),
            "Call_Duration_Sec": random.randint(5, 600),
            "Cell_Tower_ID":   tower["id"],
            "Tower_Lat":       tower["lat"],
            "Tower_Lon":       tower["lon"],
        })

    random.shuffle(records)
    return records


if __name__ == "__main__":
    random.seed(42)
    records = build_records(TOTAL_RECORDS)
    df = pd.DataFrame(records, columns=[
        "Caller_Number", "Receiver_Number", "DateTime",
        "Call_Duration_Sec", "Cell_Tower_ID", "Tower_Lat", "Tower_Lon"
    ])
    df.to_csv(OUTPUT_FILE, index=False)

    print(f"[OK]  Generated {len(df)} CDR records -> {OUTPUT_FILE}")
    print()
    print("--- Test Parameters -------------------------------------------")
    print(f"   Target Phone Number : {TARGET_NUMBER}")
    print(f"   Crime Scene Lat     : {CRIME_SCENE_LAT}")
    print(f"   Crime Scene Lon     : {CRIME_SCENE_LON}")
    print(f"   Proximity Radius    : 0.5 km")
    print("---------------------------------------------------------------")
    print(f"   Expected proximity leads: 4 (planted near crime scene towers)")
    print()
    print("Upload dummy_cdr.csv on the /cdr page with the parameters above.")
