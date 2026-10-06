"""
Data Validation and Preprocessing Layer.
Validates incoming MQTT telemetry JSON, computes incremental energy (Wh & kWh),
and adds standardized timestamps.
"""

import logging
from datetime import datetime, timezone
from typing import Dict, Any, Tuple

from backend.config import TELEMETRY_INTERVAL_S
from backend.schemas import TelemetryInput

logger = logging.getLogger("smart_home.preprocessing")


def preprocess_telemetry(raw_data: Dict[str, Any], sampling_interval_s: float = TELEMETRY_INTERVAL_S) -> Dict[str, Any]:
    """
    Validates raw dictionary via Pydantic TelemetryInput schema,
    applies business bounds checking, and computes exact energy consumption.

    Raises:
        ValueError if the payload is missing required fields or has impossible values.
    """
    try:
        validated = TelemetryInput(**raw_data)
    except Exception as e:
        logger.error(f"Validation failed for telemetry payload: {e}")
        raise ValueError(f"Corrupted or invalid telemetry payload: {e}")

    # Standardize server-side timestamp in ISO 8601 UTC format
    server_time = datetime.now(timezone.utc).isoformat()

    # Exact physical energy calculation based on actual sampling interval
    # Energy (Wh) = Power (W) * (Interval in seconds / 3600)
    power_w = validated.power_w
    energy_wh = round((power_w * sampling_interval_s) / 3600.0, 5)
    energy_kwh = round(energy_wh / 1000.0, 7)

    processed_record = {
        "timestamp": server_time,
        "uptime_ms": validated.uptime_ms or 0,
        "temperature": round(validated.temperature, 2),
        "humidity": round(validated.humidity, 2),
        "occupancy": validated.occupancy,
        "light_level": validated.light_level,
        "ac": validated.ac,
        "fan": validated.fan,
        "tv": validated.tv,
        "room_light": validated.room_light,
        "refrigerator": validated.refrigerator,
        "heater": validated.heater,
        "microwave": validated.microwave,
        "power_w": power_w,
        "energy_wh": energy_wh,
        "energy_kwh": energy_kwh,
        # IoT node baseline flags for reference/comparison with AI
        "iot_waste_flag": validated.waste_flag or 0,
        "iot_high_load_flag": validated.high_load_flag or 0,
        "status_msg": validated.status_msg or "Normal",
    }

    return processed_record
