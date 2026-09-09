"""Reusable CDR parsing and geospatial intelligence helpers."""

from __future__ import annotations

from collections import Counter
from datetime import datetime
from io import BytesIO
from typing import Any

import pandas as pd
from geopy.distance import geodesic

REQUIRED_COLUMNS = (
    "Caller_Number",
    "Receiver_Number",
    "DateTime",
    "Call_Duration_Sec",
    "Cell_Tower_ID",
    "Tower_Lat",
    "Tower_Lon",
)

_COLUMN_ALIASES = {
    "caller_number": "Caller_Number",
    "caller": "Caller_Number",
    "receiver_number": "Receiver_Number",
    "receiver": "Receiver_Number",
    "datetime": "DateTime",
    "timestamp": "DateTime",
    "call_duration_sec": "Call_Duration_Sec",
    "call_duration": "Call_Duration_Sec",
    "duration": "Call_Duration_Sec",
    "cell_tower_id": "Cell_Tower_ID",
    "tower_id": "Cell_Tower_ID",
    "tower_lat": "Tower_Lat",
    "latitude": "Tower_Lat",
    "tower_lon": "Tower_Lon",
    "tower_long": "Tower_Lon",
    "longitude": "Tower_Lon",
}


def _canonical_column_name(column: Any) -> str:
    normalized = "_".join(str(column).strip().lower().split())
    return _COLUMN_ALIASES.get(normalized, str(column).strip())


def load_cdr_csv(file_stream: BytesIO) -> pd.DataFrame:
    """Read and validate a CDR CSV, accepting common header variants."""
    dataframe = pd.read_csv(file_stream)
    dataframe.columns = [_canonical_column_name(column) for column in dataframe.columns]
    missing = [column for column in REQUIRED_COLUMNS if column not in dataframe.columns]
    if missing:
        raise ValueError(f"Missing required CSV columns: {', '.join(missing)}")

    dataframe = dataframe.copy()
    dataframe["Caller_Number"] = dataframe["Caller_Number"].astype(str).str.strip()
    dataframe["Receiver_Number"] = dataframe["Receiver_Number"].astype(str).str.strip()
    dataframe["DateTime"] = pd.to_datetime(dataframe["DateTime"], errors="coerce")
    dataframe["Call_Duration_Sec"] = pd.to_numeric(dataframe["Call_Duration_Sec"], errors="coerce")
    dataframe["Tower_Lat"] = pd.to_numeric(dataframe["Tower_Lat"], errors="coerce")
    dataframe["Tower_Lon"] = pd.to_numeric(dataframe["Tower_Lon"], errors="coerce")

    invalid = dataframe["DateTime"].isna() | dataframe[["Tower_Lat", "Tower_Lon"]].isna().any(axis=1)
    invalid |= ~dataframe["Tower_Lat"].between(-90, 90) | ~dataframe["Tower_Lon"].between(-180, 180)
    dataframe = dataframe.loc[~invalid].copy()
    if dataframe.empty:
        raise ValueError("The CSV contains no rows with valid timestamps and tower coordinates.")
    return dataframe.sort_values("DateTime").reset_index(drop=True)


def _timestamp(value: pd.Timestamp) -> str:
    return value.isoformat()


def analyze_cdr(
    dataframe: pd.DataFrame,
    target_number: str,
    crime_lat: float,
    crime_lon: float,
    radius_km: float = 0.5,
    start_time: str | None = None,
    end_time: str | None = None,
) -> dict[str, Any]:
    """Return target timeline, proximity leads, and contact frequency summary."""
    target = str(target_number).strip()
    if not target:
        raise ValueError("target_number is required.")
    if radius_km <= 0:
        raise ValueError("radius_km must be greater than zero.")
    if not -90 <= crime_lat <= 90 or not -180 <= crime_lon <= 180:
        raise ValueError("Crime scene coordinates are outside valid ranges.")

    windowed = dataframe
    parsed_start = pd.to_datetime(start_time, errors="coerce") if start_time else None
    parsed_end = pd.to_datetime(end_time, errors="coerce") if end_time else None
    if start_time and pd.isna(parsed_start) or end_time and pd.isna(parsed_end):
        raise ValueError("start_time and end_time must be valid timestamps.")
    if parsed_start is not None:
        windowed = windowed.loc[windowed["DateTime"] >= parsed_start]
    if parsed_end is not None:
        windowed = windowed.loc[windowed["DateTime"] <= parsed_end]
    if parsed_start is not None and parsed_end is not None and parsed_start > parsed_end:
        raise ValueError("start_time must be earlier than end_time.")

    target_rows = windowed.loc[
        (windowed["Caller_Number"] == target) | (windowed["Receiver_Number"] == target)
    ]
    contacts = Counter(
        row["Receiver_Number"] if row["Caller_Number"] == target else row["Caller_Number"]
        for _, row in target_rows.iterrows()
        if (row["Receiver_Number"] if row["Caller_Number"] == target else row["Caller_Number"]) != target
    )

    timeline = [
        {
            "latitude": float(row["Tower_Lat"]),
            "longitude": float(row["Tower_Lon"]),
            "timestamp": _timestamp(row["DateTime"]),
            "tower_id": str(row["Cell_Tower_ID"]),
            "caller_number": row["Caller_Number"],
            "receiver_number": row["Receiver_Number"],
            "duration_sec": float(row["Call_Duration_Sec"]) if pd.notna(row["Call_Duration_Sec"]) else None,
        }
        for _, row in target_rows.iterrows()
    ]

    proximity_leads = []
    for _, row in windowed.iterrows():
        distance_km = geodesic(
            (crime_lat, crime_lon), (row["Tower_Lat"], row["Tower_Lon"])
        ).km
        if distance_km <= radius_km:
            proximity_leads.append({
                "caller_number": row["Caller_Number"],
                "receiver_number": row["Receiver_Number"],
                "timestamp": _timestamp(row["DateTime"]),
                "tower_id": str(row["Cell_Tower_ID"]),
                "latitude": float(row["Tower_Lat"]),
                "longitude": float(row["Tower_Lon"]),
                "distance_km": round(distance_km, 4),
                "duration_sec": float(row["Call_Duration_Sec"]) if pd.notna(row["Call_Duration_Sec"]) else None,
                "involves_target": target in (row["Caller_Number"], row["Receiver_Number"]),
            })

    return {
        "status": "success",
        "target_number": target,
        "crime_scene": {"latitude": crime_lat, "longitude": crime_lon},
        "radius_km": radius_km,
        "time_window": {"start": start_time, "end": end_time},
        "target_call_timeline": timeline,
        "proximity_leads": proximity_leads,
        "top_contacts": [
            {"number": number, "call_count": count}
            for number, count in contacts.most_common(5)
        ],
        "records_analyzed": int(len(windowed)),
    }
