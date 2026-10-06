"""
Data Normalization and Transformation Utilities for Dashboard.
Ensures null-safe access to nested backend telemetry structures.
"""

from typing import Dict, Any, Optional, List
from dashboard.config import APPLIANCE_META


def normalize_analysis_payload(raw: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Normalizes a backend /analysis response payload to guarantee that all expected
    nested dictionaries and fields exist with sensible fallbacks.
    Never returns None or partially missing keys.
    """
    if not isinstance(raw, dict):
        raw = {}

    sensors = raw.get("sensors") or {}
    appliances = raw.get("appliances") or {}
    energy = raw.get("energy") or {}
    forecast = raw.get("forecast") or {}
    ai = raw.get("ai") or {}
    waste = raw.get("waste") or {}

    normalized = {
        "timestamp": raw.get("timestamp", ""),
        "sensors": {
            "temperature": float(sensors.get("temperature", 24.0)),
            "humidity": float(sensors.get("humidity", 50.0)),
            "occupancy": int(sensors.get("occupancy", 0)),
            "light_level": int(sensors.get("light_level", 400)),
        },
        "appliances": {
            app_k: int(appliances.get(app_k, 0)) for app_k in APPLIANCE_META.keys()
        },
        "energy": {
            "current_power_w": int(energy.get("current_power_w", 0)),
            "predicted_power_w": float(energy.get("predicted_power_w", 0.0)),
            "difference_w": float(energy.get("difference_w", 0.0)),
            "percentage_difference": float(energy.get("percentage_difference", 0.0)),
            "energy_wh": float(energy.get("energy_wh", 0.0)),
            "energy_kwh": float(energy.get("energy_kwh", 0.0)),
        },
        "forecast": {
            "predicted_next_power_w": float(forecast.get("predicted_next_power_w", energy.get("current_power_w", 0.0))),
            "forecast_horizon": str(forecast.get("forecast_horizon", "next telemetry interval (2.5s)")),
            "expected_change_w": float(forecast.get("expected_change_w", 0.0)),
            "model": str(forecast.get("model", "Linear Regression")),
        },
        "ai": {
            "anomaly": bool(ai.get("anomaly", ai.get("is_anomaly", False))),
            "is_anomaly": bool(ai.get("is_anomaly", ai.get("anomaly", False))),
            "anomaly_score": float(ai.get("anomaly_score", 0.0)),
        },
        "waste": {
            "wasteful": bool(waste.get("wasteful", waste.get("is_wasteful", False))),
            "is_wasteful": bool(waste.get("is_wasteful", waste.get("wasteful", False))),
            "reasons": list(waste.get("reasons") or waste.get("waste_reasons") or []),
            "waste_reasons": list(waste.get("waste_reasons") or waste.get("reasons") or []),
            "potential_waste_watts": int(waste.get("potential_waste_watts", waste.get("wasted_power_w", 0))),
            "wasted_power_w": int(waste.get("wasted_power_w", waste.get("potential_waste_watts", 0))),
        },
        "severity": str(raw.get("severity", "NORMAL")),
        "recommendation": str(raw.get("recommendation", "System operating normally.")),
        "action_items": list(raw.get("action_items") or []),
    }

    return normalized


def calculate_power_breakdown(appliances_dict: Dict[str, int]) -> Dict[str, Dict[str, Any]]:
    """
    Computes appliance power contribution keyed by appliance key.
    Provides fast O(1) lookup and easy iteration via .values().
    """
    breakdown = {}
    for key, meta in APPLIANCE_META.items():
        is_on = bool(appliances_dict.get(key, 0))
        watts = meta["watts"] if is_on else 0
        breakdown[key] = {
            "key": key,
            "name": meta["name"],
            "category": meta["category"],
            "rated_watts": meta["watts"],
            "current_watts": watts,
            "power_w": watts,
            "is_on": is_on,
            "icon": meta["icon"],
            "color": meta["color"],
        }
    return breakdown
