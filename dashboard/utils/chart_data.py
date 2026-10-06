"""
Centralized Chart Data Pipeline for Phase 3.2.
Handles historical telemetry normalization, timestamp parsing, chronological sorting,
time-range filtering, appliance power attribution, and aggregation for Plotly charts.
"""

from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone
import pandas as pd
import numpy as np

from dashboard.config import APPLIANCE_META


def normalize_history(raw_history: Optional[List[Dict[str, Any]]]) -> pd.DataFrame:
    """
    Transforms a raw list of telemetry dictionaries from GET /history into a clean,
    chronologically sorted pandas DataFrame with verified datatypes and derived fields.
    """
    if not raw_history:
        return pd.DataFrame(columns=[
            "id", "timestamp", "datetime", "power_w", "predicted_power_w",
            "temperature", "humidity", "occupancy", "light_level",
            "energy_kwh", "is_anomaly", "anomaly_score", "wasteful",
            "severity", "occupancy_str", "active_appliances_str"
        ])

    df = pd.DataFrame(raw_history)

    # 1. Parse timestamps
    if "timestamp" in df.columns:
        df["datetime"] = pd.to_datetime(df["timestamp"], errors="coerce", utc=True)
    else:
        df["datetime"] = pd.date_range(end=pd.Timestamp.now(tz="UTC"), periods=len(df), freq="2.5S")

    # Drop invalid timestamps
    df = df.dropna(subset=["datetime"])

    # 2. Chronological sort (oldest first for time-series)
    df = df.sort_values("datetime", ascending=True).reset_index(drop=True)

    # 3. Numeric coercions with safe defaults
    numeric_cols = [
        "power_w", "predicted_power_w", "prediction_error_w",
        "temperature", "humidity", "occupancy", "light_level",
        "energy_wh", "energy_kwh", "anomaly_score"
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)
        else:
            df[col] = 0.0

    # 4. Binary / Flag coercions
    for flag_col in ["is_anomaly", "wasteful", "ac", "fan", "tv", "room_light", "refrigerator", "heater", "microwave"]:
        if flag_col in df.columns:
            df[flag_col] = pd.to_numeric(df[flag_col], errors="coerce").fillna(0).astype(int)
        else:
            df[flag_col] = 0

    # 5. Derived semantic columns
    df["occupancy_str"] = df["occupancy"].apply(lambda v: "Occupied" if v == 1 else "Vacant")

    # Active appliances list string for tooltips
    def get_active_str(row):
        active = []
        for app_k, meta in APPLIANCE_META.items():
            if row.get(app_k, 0) == 1:
                active.append(meta["name"])
        return ", ".join(active) if active else "None (Standby)"

    df["active_appliances_str"] = df.apply(get_active_str, axis=1)

    return df


def filter_by_time_range(df: pd.DataFrame, time_range: str) -> pd.DataFrame:
    """
    Filters historical DataFrame according to the selected time horizon.
    Calculates range dynamically based on the maximum timestamp in the data.
    """
    if df.empty or "datetime" not in df.columns:
        return df

    max_dt = df["datetime"].max()
    if pd.isna(max_dt):
        return df

    range_map = {
        "10 seconds": pd.Timedelta(seconds=10),
        "1 minute": pd.Timedelta(minutes=1),
        "5 minutes": pd.Timedelta(minutes=5),
        "15 minutes": pd.Timedelta(minutes=15),
        "1 hour": pd.Timedelta(hours=1),
    }

    if time_range in range_map:
        cutoff = max_dt - range_map[time_range]
        filtered = df[df["datetime"] >= cutoff]
        return filtered if not filtered.empty else df.tail(1)
    elif time_range == "Today":
        # Records with the same UTC calendar day as max_dt
        filtered = df[df["datetime"].dt.date == max_dt.date()]
        return filtered if not filtered.empty else df
    elif time_range == "All":
        return df
    else:
        # Default fallback: 5 minutes
        cutoff = max_dt - pd.Timedelta(minutes=5)
        filtered = df[df["datetime"] >= cutoff]
        return filtered if not filtered.empty else df


def calculate_appliance_contributions(appliances_dict: Optional[Dict[str, Any]]) -> pd.DataFrame:
    """
    Calculates active power contribution and percentage for each household appliance.
    Based on real current states and rated wattages from APPLIANCE_META.
    """
    states = appliances_dict or {}
    rows = []
    
    for key, meta in APPLIANCE_META.items():
        is_on = int(states.get(key, 0)) == 1
        rated = float(meta["watts"])
        active_w = rated if is_on else 0.0
        rows.append({
            "key": key,
            "name": meta["name"],
            "category": meta["category"],
            "rated_watts": rated,
            "active_watts": active_w,
            "is_on": is_on,
            "state_label": "ON" if is_on else "OFF",
            "color": meta["color"],
        })

    contrib_df = pd.DataFrame(rows)
    total_active = contrib_df["active_watts"].sum()

    if total_active > 0:
        contrib_df["percentage"] = (contrib_df["active_watts"] / total_active) * 100.0
    else:
        contrib_df["percentage"] = 0.0

    # Sort descending by active watts, then by rated watts
    contrib_df = contrib_df.sort_values(by=["active_watts", "rated_watts"], ascending=[False, False]).reset_index(drop=True)
    return contrib_df


def prepare_heatmap_matrix(df: pd.DataFrame) -> Tuple[np.ndarray, List[str], List[int]]:
    """
    Aggregates historical power readings into a 7-day x 24-hour average power matrix.
    Returns: (matrix [7 x 24], days_of_week [Mon-Sun], hours [0-23])
    """
    days_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    hours_order = list(range(24))

    if df.empty or "datetime" not in df.columns or "power_w" not in df.columns:
        return np.zeros((7, 24)), days_order, hours_order

    # Extract day name and hour
    temp_df = df.copy()
    temp_df["day_name"] = temp_df["datetime"].dt.day_name()
    temp_df["hour"] = temp_df["datetime"].dt.hour

    # Pivot table with average power
    pivot = temp_df.pivot_table(
        index="day_name",
        columns="hour",
        values="power_w",
        aggfunc="mean"
    )

    # Reindex to guarantee all days and hours are present
    pivot = pivot.reindex(index=days_order, columns=hours_order)
    
    # Fill NaN cells where no samples exist with 0 (or None for Plotly)
    matrix = pivot.to_numpy()
    return matrix, days_order, hours_order


def prepare_waterfall_decomposition(
    appliances_dict: Optional[Dict[str, Any]],
    current_power_w: Optional[float] = None
) -> List[Dict[str, Any]]:
    """
    Produces a mathematically sound additive waterfall decomposition:
    Baseline Idle -> + Device 1 -> + Device 2 -> ... = Total Power.
    Guarantees no double-counting of loads.
    """
    contrib_df = calculate_appliance_contributions(appliances_dict)
    active_devices = contrib_df[contrib_df["is_on"]].copy()

    total_w = float(current_power_w) if current_power_w is not None else contrib_df["active_watts"].sum()
    sum_appliances = active_devices["active_watts"].sum()

    steps = []

    # Standby / unmetered base load if total power exceeds sum of rated loads
    standby_w = max(0.0, total_w - sum_appliances)
    if standby_w > 0:
        steps.append({
            "name": "Base Standby",
            "type": "relative",
            "value": standby_w,
            "text": f"{int(standby_w)} W"
        })

    # Add each active appliance
    for _, row in active_devices.iterrows():
        steps.append({
            "name": row["name"],
            "type": "relative",
            "value": row["active_watts"],
            "text": f"+{int(row['active_watts'])} W"
        })

    # Final Total step
    steps.append({
        "name": "Total Power",
        "type": "total",
        "value": total_w,
        "text": f"{int(total_w)} W"
    })

    return steps
