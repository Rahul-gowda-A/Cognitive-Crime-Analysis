"""Generate a small CDR fixture for local dashboard testing.

Run: python generate_dummy_cdr.py
"""

from pathlib import Path

import pandas as pd

rows = [
    ["9876543210", "9123456780", "2026-08-30 08:15:00", 42, "BLR-101", 12.9719, 77.5937],
    ["9123456780", "9876543210", "2026-08-30 09:10:00", 118, "BLR-102", 12.9750, 77.6000],
    ["9876543210", "9988776655", "2026-08-30 10:45:00", 64, "BLR-103", 12.9698, 77.5946],
    ["9988776655", "9876543210", "2026-08-30 12:20:00", 33, "BLR-103", 12.9698, 77.5946],
    ["9876543210", "9123456780", "2026-08-30 14:05:00", 210, "BLR-104", 12.9725, 77.5910],
    ["9000000001", "9000000002", "2026-08-30 15:30:00", 25, "BLR-103", 12.9698, 77.5946],
    ["9876543210", "9123456780", "2026-08-30 18:15:00", 91, "BLR-105", 12.9850, 77.6100],
    ["9111111111", "9222222222", "2026-08-31 08:00:00", 16, "BLR-999", 13.1000, 77.7000],
]

output = Path(__file__).with_name("dummy_cdr.csv")
pd.DataFrame(rows, columns=[
    "Caller_Number", "Receiver_Number", "DateTime", "Call_Duration_Sec",
    "Cell_Tower_ID", "Tower_Lat", "Tower_Lon",
]).to_csv(output, index=False)
print(f"Wrote {len(rows)} records to {output}")
