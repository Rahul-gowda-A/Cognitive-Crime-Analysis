"""
generate_sample_cdr.py
Generate a realistic Call Detail Record (CDR) sample CSV dataset matching standard telecom schemas.

Schema Columns:
  - Caller_Number
  - Receiver_Number
  - DateTime
  - Call_Duration_Sec
  - Cell_Tower_ID
  - Tower_Lat
  - Tower_Lon

Test Parameters:
  - Target Number: 9876543210
  - Crime Scene: Lat 12.9716, Lon 77.5946 (Bengaluru Central)
  - Proximity Radius: 0.5 km
"""

from pathlib import Path
import pandas as pd

def generate_cdr_csv(output_path="sample_cdr.csv"):
    records = [
        # Target movements and calls
        # 1. Morning call in Indiranagar (~4.5km away)
        {
            "Caller_Number": "9876543210",
            "Receiver_Number": "9123456780",
            "DateTime": "2026-09-02 08:30:15",
            "Call_Duration_Sec": 85,
            "Cell_Tower_ID": "BLR-TOW-101",
            "Tower_Lat": 12.9784,
            "Tower_Lon": 77.6408,
        },
        # 2. Call on MG Road moving toward Central (~1.8km away)
        {
            "Caller_Number": "9988776655",
            "Receiver_Number": "9876543210",
            "DateTime": "2026-09-02 09:45:20",
            "Call_Duration_Sec": 140,
            "Cell_Tower_ID": "BLR-TOW-104",
            "Tower_Lat": 12.9740,
            "Tower_Lon": 77.6080,
        },
        # 3. Call right near Crime Scene (Cubbon Park / Central - ~0.15 km from (12.9716, 77.5946)) -> PROXIMITY HIT
        {
            "Caller_Number": "9876543210",
            "Receiver_Number": "9123456780",
            "DateTime": "2026-09-02 11:15:00",
            "Call_Duration_Sec": 45,
            "Cell_Tower_ID": "BLR-TOW-202",
            "Tower_Lat": 12.9720,
            "Tower_Lon": 77.5940,
        },
        # 4. Another call at the Crime Scene perimeter (~0.22 km) -> PROXIMITY HIT
        {
            "Caller_Number": "9876543210",
            "Receiver_Number": "9811223344",
            "DateTime": "2026-09-02 12:05:30",
            "Call_Duration_Sec": 210,
            "Cell_Tower_ID": "BLR-TOW-203",
            "Tower_Lat": 12.9705,
            "Tower_Lon": 77.5932,
        },
        # 5. Non-target suspicious call right in Crime Scene cell tower (~0.15 km) -> PROXIMITY HIT
        {
            "Caller_Number": "9444332211",
            "Receiver_Number": "9555667788",
            "DateTime": "2026-09-02 12:10:12",
            "Call_Duration_Sec": 30,
            "Cell_Tower_ID": "BLR-TOW-202",
            "Tower_Lat": 12.9720,
            "Tower_Lon": 77.5940,
        },
        # 6. Target moving to Richmond Town (~1.2 km away)
        {
            "Caller_Number": "9123456780",
            "Receiver_Number": "9876543210",
            "DateTime": "2026-09-02 13:40:00",
            "Call_Duration_Sec": 95,
            "Cell_Tower_ID": "BLR-TOW-305",
            "Tower_Lat": 12.9610,
            "Tower_Lon": 77.6010,
        },
        # 7. Target calling top contact 1 again
        {
            "Caller_Number": "9876543210",
            "Receiver_Number": "9123456780",
            "DateTime": "2026-09-02 14:15:22",
            "Call_Duration_Sec": 160,
            "Cell_Tower_ID": "BLR-TOW-305",
            "Tower_Lat": 12.9610,
            "Tower_Lon": 77.6010,
        },
        # 8. Target calling contact 2
        {
            "Caller_Number": "9876543210",
            "Receiver_Number": "9988776655",
            "DateTime": "2026-09-02 15:30:10",
            "Call_Duration_Sec": 50,
            "Cell_Tower_ID": "BLR-TOW-410",
            "Tower_Lat": 12.9520,
            "Tower_Lon": 77.6150,
        },
        # 9. Target calling contact 3
        {
            "Caller_Number": "9876543210",
            "Receiver_Number": "9811223344",
            "DateTime": "2026-09-02 16:20:00",
            "Call_Duration_Sec": 75,
            "Cell_Tower_ID": "BLR-TOW-412",
            "Tower_Lat": 12.9480,
            "Tower_Lon": 77.6200,
        },
        # 10. Target calling contact 4
        {
            "Caller_Number": "9765432109",
            "Receiver_Number": "9876543210",
            "DateTime": "2026-09-02 17:05:40",
            "Call_Duration_Sec": 115,
            "Cell_Tower_ID": "BLR-TOW-501",
            "Tower_Lat": 12.9350,
            "Tower_Lon": 77.6250,
        },
        # 11. Target calling contact 5
        {
            "Caller_Number": "9876543210",
            "Receiver_Number": "9654321098",
            "DateTime": "2026-09-02 18:00:15",
            "Call_Duration_Sec": 60,
            "Cell_Tower_ID": "BLR-TOW-508",
            "Tower_Lat": 12.9280,
            "Tower_Lon": 77.6320,
        },
        # 12. Additional target calls to solidify frequency matrix
        {
            "Caller_Number": "9876543210",
            "Receiver_Number": "9123456780",
            "DateTime": "2026-09-02 19:10:00",
            "Call_Duration_Sec": 180,
            "Cell_Tower_ID": "BLR-TOW-508",
            "Tower_Lat": 12.9280,
            "Tower_Lon": 77.6320,
        },
        {
            "Caller_Number": "9988776655",
            "Receiver_Number": "9876543210",
            "DateTime": "2026-09-02 20:30:45",
            "Call_Duration_Sec": 40,
            "Cell_Tower_ID": "BLR-TOW-601",
            "Tower_Lat": 12.9180,
            "Tower_Lon": 77.6450,
        },
        # 13. Other unrelated background calls in telecom network
        {
            "Caller_Number": "9111111111",
            "Receiver_Number": "9222222222",
            "DateTime": "2026-09-02 11:30:00",
            "Call_Duration_Sec": 120,
            "Cell_Tower_ID": "BLR-TOW-900",
            "Tower_Lat": 13.0358,
            "Tower_Lon": 77.5970,
        },
        {
            "Caller_Number": "9333333333",
            "Receiver_Number": "9444444444",
            "DateTime": "2026-09-02 12:45:00",
            "Call_Duration_Sec": 90,
            "Cell_Tower_ID": "BLR-TOW-901",
            "Tower_Lat": 13.0100,
            "Tower_Lon": 77.5500,
        }
    ]

    df = pd.DataFrame(records)
    out_file = Path(output_path)
    df.to_csv(out_file, index=False)
    print(f" Successfully generated CDR dataset: {out_file.resolve()}")
    print(f"   Total Records: {len(df)}")
    print("   Standard Telecom Columns:", list(df.columns))
    print("\n Recommended Test Parameters for CDR Intelligence Module:")
    print("   • Target Phone Number: 9876543210")
    print("   • Crime Scene Latitude: 12.9716")
    print("   • Crime Scene Longitude: 77.5946")
    print("   • Proximity Radius: 0.5 km")
    return out_file

if __name__ == "__main__":
    generate_cdr_csv("sample_cdr.csv")
    generate_cdr_csv("dummy_cdr.csv")
