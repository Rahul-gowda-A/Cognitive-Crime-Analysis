"""
generate_all_cdr_cases.py
─────────────────────────
Generates multiple realistic CDR (Call Detail Record) datasets for testing
various criminal intelligence scenarios across major Indian metropolitan areas.
"""

import os
import random
import pandas as pd
from datetime import datetime, timedelta

def random_dt(start: datetime, end: datetime) -> datetime:
    delta = (end - start).total_seconds()
    return start + timedelta(seconds=random.uniform(0, delta))

CASES = [
    {
        "filename": "cdr_case1_bengaluru_robbery.csv",
        "case_name": "Case 1: Central Bengaluru Commercial Snatching / Robbery",
        "target_number": "9876543210",
        "crime_lat": 12.9716,
        "crime_lon": 77.5946,
        "recommended_radius": 0.5,
        "crime_time": datetime(2026, 9, 1, 1, 30, 0),
        "frequent_contact": "9845012345",
        "towers_near": [
            {"id": "BLR_MG_01", "lat": 12.9720, "lon": 77.5950},
            {"id": "BLR_BRIGADE_02", "lat": 12.9712, "lon": 77.5940},
            {"id": "BLR_CHURCH_03", "lat": 12.9715, "lon": 77.5952},
        ],
        "towers_far": [
            {"id": "BLR_KORAMANGALA", "lat": 12.9352, "lon": 77.6245},
            {"id": "BLR_HEBBAL", "lat": 13.0358, "lon": 77.5970},
            {"id": "BLR_JAYANAGAR", "lat": 12.9250, "lon": 77.5938},
            {"id": "BLR_WHITEFIELD", "lat": 12.9698, "lon": 77.7499},
            {"id": "BLR_ELECTRONIC_CITY", "lat": 12.8399, "lon": 77.6770},
            {"id": "BLR_PEENYA", "lat": 13.0210, "lon": 77.4600},
            {"id": "BLR_INDIRANAGAR", "lat": 12.9784, "lon": 77.6408},
        ],
        "other_numbers": [
            "9845012345", "9123456789", "9234567890", "9345678901",
            "9456789012", "9567890123", "9678901234", "9789012345"
        ]
    },
    {
        "filename": "cdr_case2_mumbai_narcotics.csv",
        "case_name": "Case 2: Mumbai Bandra Narcotics Transit Ring",
        "target_number": "9820011223",
        "crime_lat": 19.0596,
        "crime_lon": 72.8295,
        "recommended_radius": 0.8,
        "crime_time": datetime(2026, 8, 30, 22, 15, 0),
        "frequent_contact": "9920199888",
        "towers_near": [
            {"id": "MUM_BANDRA_W1", "lat": 19.0601, "lon": 72.8302},
            {"id": "MUM_BANDRA_W2", "lat": 19.0589, "lon": 72.8288},
            {"id": "MUM_CARTER_RD", "lat": 19.0615, "lon": 72.8270},
        ],
        "towers_far": [
            {"id": "MUM_ANDHERI_E", "lat": 19.1136, "lon": 72.8697},
            {"id": "MUM_DADAR", "lat": 19.0178, "lon": 72.8478},
            {"id": "MUM_BKC", "lat": 19.0664, "lon": 72.8687},
            {"id": "MUM_COLABA", "lat": 18.9067, "lon": 72.8147},
            {"id": "MUM_BORIVALI", "lat": 19.2307, "lon": 72.8567},
            {"id": "MUM_THANE", "lat": 19.2183, "lon": 72.9781},
        ],
        "other_numbers": [
            "9920199888", "9819922334", "9769933445", "9833344556",
            "9988776655", "9821122334", "9892233445"
        ]
    },
    {
        "filename": "cdr_case3_delhi_cyber_fraud.csv",
        "case_name": "Case 3: New Delhi Connaught Place Syndicate Hub",
        "target_number": "9811099887",
        "crime_lat": 28.6289,
        "crime_lon": 77.2065,
        "recommended_radius": 0.6,
        "crime_time": datetime(2026, 8, 31, 14, 45, 0),
        "frequent_contact": "9810011223",
        "towers_near": [
            {"id": "DEL_CP_INNER", "lat": 28.6315, "lon": 77.2167},
            {"id": "DEL_JANPATH", "lat": 28.6265, "lon": 77.2190},
            {"id": "DEL_BARAKHAMBA", "lat": 28.6300, "lon": 77.2250},
        ],
        "towers_far": [
            {"id": "DEL_NOIDA_SEC18", "lat": 28.5700, "lon": 77.3200},
            {"id": "DEL_GURGAON_CYBER", "lat": 28.4900, "lon": 77.0900},
            {"id": "DEL_DWARKA", "lat": 28.5800, "lon": 77.0500},
            {"id": "DEL_ROHINI", "lat": 28.7100, "lon": 77.1100},
            {"id": "DEL_LAJPAT_NGR", "lat": 28.5700, "lon": 77.2400},
            {"id": "DEL_KAROL_BAGH", "lat": 28.6500, "lon": 77.1900},
        ],
        "other_numbers": [
            "9810011223", "9871122334", "9910022334", "9818833445",
            "9891144556", "9999055667", "9810988776"
        ]
    },
    {
        "filename": "cdr_case4_hyderabad_burglary.csv",
        "case_name": "Case 4: Hyderabad Hitec City Corridor Burglary",
        "target_number": "9849055443",
        "crime_lat": 17.4483,
        "crime_lon": 78.3915,
        "recommended_radius": 0.5,
        "crime_time": datetime(2026, 9, 1, 3, 20, 0),
        "frequent_contact": "9848099887",
        "towers_near": [
            {"id": "HYD_HITEC_01", "lat": 17.4490, "lon": 78.3920},
            {"id": "HYD_MADHAPUR_02", "lat": 17.4475, "lon": 78.3908},
            {"id": "HYD_INORBIT_03", "lat": 17.4460, "lon": 78.3880},
        ],
        "towers_far": [
            {"id": "HYD_GACHIBOWLI", "lat": 17.4400, "lon": 78.3489},
            {"id": "HYD_BANJARA_HILLS", "lat": 17.4156, "lon": 78.4350},
            {"id": "HYD_JUBILEE_HILLS", "lat": 17.4319, "lon": 78.4073},
            {"id": "HYD_SECUNDERABAD", "lat": 17.4399, "lon": 78.4983},
            {"id": "HYD_KUKATPALLY", "lat": 17.4849, "lon": 78.4138},
            {"id": "HYD_CHARMINAR", "lat": 17.3616, "lon": 78.4747},
        ],
        "other_numbers": [
            "9848099887", "9949011223", "9866022334", "9700033445",
            "9989044556", "9849155667", "9866166778"
        ]
    }
]

def generate_case(case: dict, total_records: int = 150):
    target = case["target_number"]
    freq_contact = case["frequent_contact"]
    all_numbers = [target] + case["other_numbers"]
    
    start_time = case["crime_time"] - timedelta(hours=36)
    end_time = case["crime_time"] + timedelta(hours=12)
    
    records = []
    
    # 1. Critical proximity calls around crime time near the scene
    crime_window_start = case["crime_time"] - timedelta(minutes=45)
    for i in range(5):
        ts = crime_window_start + timedelta(minutes=i * 18 + random.randint(1, 5))
        tower = random.choice(case["towers_near"])
        partner = freq_contact if (i % 2 == 0) else random.choice(case["other_numbers"])
        records.append({
            "Caller_Number": target,
            "Receiver_Number": partner,
            "DateTime": ts.strftime("%Y-%m-%d %H:%M:%S"),
            "Call_Duration_Sec": random.randint(25, 240),
            "Cell_Tower_ID": tower["id"],
            "Tower_Lat": tower["lat"],
            "Tower_Lon": tower["lon"]
        })
        
    # 2. General movement of the target number across the city
    for _ in range(25):
        ts = random_dt(start_time, end_time)
        tower = random.choice(case["towers_far"])
        partner = freq_contact if (random.random() < 0.45) else random.choice(case["other_numbers"])
        is_caller = random.random() < 0.6
        records.append({
            "Caller_Number": target if is_caller else partner,
            "Receiver_Number": partner if is_caller else target,
            "DateTime": ts.strftime("%Y-%m-%d %H:%M:%S"),
            "Call_Duration_Sec": random.randint(10, 480),
            "Cell_Tower_ID": tower["id"],
            "Tower_Lat": tower["lat"],
            "Tower_Lon": tower["lon"]
        })
        
    # 3. Background noise / other callers in the cell network
    all_towers = case["towers_near"] + case["towers_far"]
    remaining = total_records - len(records)
    for _ in range(remaining):
        c = random.choice(all_numbers)
        r = random.choice([x for x in all_numbers if x != c])
        t = random.choice(all_towers)
        records.append({
            "Caller_Number": c,
            "Receiver_Number": r,
            "DateTime": random_dt(start_time, end_time).strftime("%Y-%m-%d %H:%M:%S"),
            "Call_Duration_Sec": random.randint(5, 500),
            "Cell_Tower_ID": t["id"],
            "Tower_Lat": t["lat"],
            "Tower_Lon": t["lon"]
        })
        
    random.shuffle(records)
    df = pd.DataFrame(records)
    df.to_csv(case["filename"], index=False)
    print(f"[OK] Generated {case['filename']} ({len(df)} records)")

if __name__ == "__main__":
    random.seed(101)
    for case in CASES:
        generate_case(case)
    print("\nAll 4 CDR case CSV files successfully generated!")
