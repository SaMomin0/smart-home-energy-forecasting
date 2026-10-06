"""
Feature Engineering Layer for Linear Regression and Isolation Forest Models.
Transforms environmental sensor readings, appliance binary states, and temporal
metadata into structured feature matrices.
"""

from datetime import datetime, timezone
from typing import Dict, Any, List, Union, Tuple
import pandas as pd
import numpy as np

from backend.config import APPLIANCE_RATINGS, HIGH_POWER_APPLIANCES, DAYLIGHT_LUX_THRESHOLD

# Exactly ordered feature columns for Linear Regression expected power estimation
# (Note: total_appliance_power is excluded from regression inputs to avoid target leakage,
# allowing the linear model to learn the true physical wattage coefficients: 1500W, 75W, etc.)
REGRESSION_FEATURES: List[str] = [
    # 1. Environmental Sensors
    "temperature",
    "humidity",
    "occupancy",
    "light_level",
    # 2. Discrete Appliance Binary States
    "ac",
    "fan",
    "tv",
    "room_light",
    "refrigerator",
    "heater",
    "microwave",
    # 3. Aggregation & Load Characteristics
    "appliance_count",
    "high_power_count",
    # 4. Temporal Features
    "hour",
    "minute",
    "day_of_week",
    # 5. Domain Interaction Features
    "occupied_ac",
    "occupied_fan",
    "occupied_light",
    "occupied_heater",
    "daylight_light",
]

# Ordered features for Isolation Forest Unsupervised Anomaly Detection
ISOLATION_FEATURES: List[str] = [
    "power_w",
    "temperature",
    "humidity",
    "occupancy",
    "appliance_count",
    "high_power_count",
    "hour",
    "total_appliance_power",
]

# Ordered features for Short-Term Energy Forecasting (Model 2)
# Strictly uses historical lags and contextual metadata.
# The current target power is NEVER included as an input.
FORECAST_FEATURES: List[str] = [
    "power_lag_1",          # Power at t-1 (2.5 seconds ago)
    "power_lag_2",          # Power at t-2 (5.0 seconds ago)
    "power_lag_3",          # Power at t-3 (7.5 seconds ago)
    "power_rolling_mean_3", # Moving average across previous 3 time steps
    "power_trend_1_2",      # Delta / gradient between t-1 and t-2
    "temperature",          # Exogenous environmental temperature
    "humidity",             # Exogenous environmental humidity
    "occupancy",            # Room occupancy state
    "hour",                 # Diurnal time factor
    "minute",               # Sub-hourly factor
]


def extract_features_single(record: Dict[str, Any]) -> Dict[str, Any]:
    """
    Computes all engineered and interaction features from a single telemetry dictionary.
    Returns an augmented dictionary containing all regression and isolation features.
    """
    # Extract timestamp or default to now
    ts_val = record.get("timestamp")
    if isinstance(ts_val, str):
        try:
            dt = datetime.fromisoformat(ts_val.replace("Z", "+00:00"))
        except Exception:
            dt = datetime.now(timezone.utc)
    elif isinstance(ts_val, datetime):
        dt = ts_val
    else:
        dt = datetime.now(timezone.utc)

    hour = dt.hour
    minute = dt.minute
    day_of_week = dt.weekday()

    # Sensor values
    temp = float(record.get("temperature", 24.0))
    hum = float(record.get("humidity", 50.0))
    occ = int(record.get("occupancy", 0))
    light = int(record.get("light_level", 400))

    # Appliance states
    ac = int(record.get("ac", 0))
    fan = int(record.get("fan", 0))
    tv = int(record.get("tv", 0))
    room_light = int(record.get("room_light", 0))
    refrigerator = int(record.get("refrigerator", 1))
    heater = int(record.get("heater", 0))
    microwave = int(record.get("microwave", 0))

    # Aggregations
    appliance_count = ac + fan + tv + room_light + refrigerator + heater + microwave
    high_power_count = ac + heater + microwave

    # Deterministic power summation from individual ratings
    total_appliance_power = (
        ac * APPLIANCE_RATINGS["ac"]
        + fan * APPLIANCE_RATINGS["fan"]
        + tv * APPLIANCE_RATINGS["tv"]
        + room_light * APPLIANCE_RATINGS["room_light"]
        + refrigerator * APPLIANCE_RATINGS["refrigerator"]
        + heater * APPLIANCE_RATINGS["heater"]
        + microwave * APPLIANCE_RATINGS["microwave"]
    )

    # Useful domain interactions
    occupied_ac = occ * ac
    occupied_fan = occ * fan
    occupied_light = occ * room_light
    occupied_heater = occ * heater
    daylight_light = 1 if (light > DAYLIGHT_LUX_THRESHOLD and room_light == 1) else 0

    power_w = int(record.get("power_w", total_appliance_power))

    features = {
        "temperature": temp,
        "humidity": hum,
        "occupancy": occ,
        "light_level": light,
        "ac": ac,
        "fan": fan,
        "tv": tv,
        "room_light": room_light,
        "refrigerator": refrigerator,
        "heater": heater,
        "microwave": microwave,
        "appliance_count": appliance_count,
        "high_power_count": high_power_count,
        "total_appliance_power": total_appliance_power,
        "hour": hour,
        "minute": minute,
        "day_of_week": day_of_week,
        "occupied_ac": occupied_ac,
        "occupied_fan": occupied_fan,
        "occupied_light": occupied_light,
        "occupied_heater": occupied_heater,
        "daylight_light": daylight_light,
        "power_w": power_w,
    }

    return features


def extract_features_df(data: Union[pd.DataFrame, List[Dict[str, Any]]]) -> pd.DataFrame:
    """
    Transforms a DataFrame or list of telemetry dictionaries into a fully engineered DataFrame.
    """
    if isinstance(data, list):
        records = [extract_features_single(r) for r in data]
        return pd.DataFrame(records)
    elif isinstance(data, pd.DataFrame):
        records = [extract_features_single(row.to_dict()) for _, row in data.iterrows()]
        return pd.DataFrame(records)
    else:
        raise TypeError("Input must be a pandas DataFrame or a list of dictionaries.")


def build_lag_features_df(df_raw: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series]:
    """
    Constructs short-term time series lag features for chronological forecasting.
    
    Target:
      y = power_w at time t
      
    Inputs:
      power_lag_1 = power at t-1 (previous telemetry step)
      power_lag_2 = power at t-2 (2 steps ago)
      power_lag_3 = power at t-3 (3 steps ago)
      power_rolling_mean_3 = average of lags 1, 2, 3
      power_trend_1_2 = rate of change between t-1 and t-2
      environmental context (temperature, humidity, occupancy, hour, minute)
      
    DATA LEAKAGE PREVENTION:
      power_w at time t is strictly the target 'y' and is NEVER included in feature matrix 'X'.
    """
    df = df_raw.copy()
    if "timestamp" in df.columns:
        df["dt"] = pd.to_datetime(df["timestamp"])
        df = df.sort_values("dt").reset_index(drop=True)
        df["hour"] = df["dt"].dt.hour
        df["minute"] = df["dt"].dt.minute
    else:
        if "hour" not in df.columns:
            df["hour"] = 12
        if "minute" not in df.columns:
            df["minute"] = 0

    # Lags shifted chronologically backwards
    df["power_lag_1"] = df["power_w"].shift(1)
    df["power_lag_2"] = df["power_w"].shift(2)
    df["power_lag_3"] = df["power_w"].shift(3)

    # Rolling statistics over past values
    df["power_rolling_mean_3"] = (df["power_lag_1"] + df["power_lag_2"] + df["power_lag_3"]) / 3.0
    df["power_trend_1_2"] = df["power_lag_1"] - df["power_lag_2"]

    # Drop the first 3 rows which contain NaN due to shifting
    df_clean = df.dropna(subset=["power_lag_1", "power_lag_2", "power_lag_3"]).copy()

    X = df_clean[FORECAST_FEATURES]
    y = df_clean["power_w"].astype(float)

    return X, y


def build_live_forecast_feature_row(
    recent_power_history: List[float],
    current_record: Dict[str, Any]
) -> pd.DataFrame:
    """
    Constructs the feature vector to forecast power for the NEXT telemetry interval (t+1),
    using the most recently observed power readings.
    
    recent_power_history: [P_(t-2), P_(t-1), P_t] where last element is current power.
    """
    # Fallback padding if fewer than 3 historical values are available
    current_p = float(current_record.get("power_w", 0.0))
    if not recent_power_history:
        history = [current_p, current_p, current_p]
    elif len(recent_power_history) == 1:
        history = [recent_power_history[0], recent_power_history[0], recent_power_history[0]]
    elif len(recent_power_history) == 2:
        history = [recent_power_history[0], recent_power_history[0], recent_power_history[1]]
    else:
        history = recent_power_history[-3:]

    # For next step forecast t+1:
    # lag_1 is current power P_t
    # lag_2 is P_(t-1)
    # lag_3 is P_(t-2)
    p_lag_1 = float(history[-1])
    p_lag_2 = float(history[-2])
    p_lag_3 = float(history[-3])
    rolling_mean_3 = (p_lag_1 + p_lag_2 + p_lag_3) / 3.0
    trend_1_2 = p_lag_1 - p_lag_2

    ts_val = current_record.get("timestamp")
    if isinstance(ts_val, str):
        try:
            dt = datetime.fromisoformat(ts_val.replace("Z", "+00:00"))
        except Exception:
            dt = datetime.now(timezone.utc)
    elif isinstance(ts_val, datetime):
        dt = ts_val
    else:
        dt = datetime.now(timezone.utc)

    row = {
        "power_lag_1": p_lag_1,
        "power_lag_2": p_lag_2,
        "power_lag_3": p_lag_3,
        "power_rolling_mean_3": rolling_mean_3,
        "power_trend_1_2": trend_1_2,
        "temperature": float(current_record.get("temperature", 25.0)),
        "humidity": float(current_record.get("humidity", 50.0)),
        "occupancy": int(current_record.get("occupancy", 0)),
        "hour": dt.hour,
        "minute": dt.minute,
    }

    return pd.DataFrame([[row[col] for col in FORECAST_FEATURES]], columns=FORECAST_FEATURES)

