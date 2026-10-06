"""
Explainable Rule-Based Wasteful Usage Detection Engine.
Operates independently from statistical/ML anomaly detection to identify explicit,
human-interpretable electrical energy waste patterns and conflicting operating states.
"""

from typing import Dict, Any, List, Tuple
from backend.config import APPLIANCE_RATINGS, DAYLIGHT_LUX_THRESHOLD, HIGH_POWER_WARNING_THRESHOLD_W


def evaluate_waste_rules(record: Dict[str, Any]) -> Dict[str, Any]:
    """
    Evaluates explainable smart home domain rules against current telemetry.

    Returns:
        Dict with:
            - wasteful (bool): True if at least one wasteful condition is detected
            - reasons (List[str]): List of human-readable explanations
            - potential_waste_watts (int): Total power actively being wasted
    """
    reasons: List[str] = []
    waste_watts = 0

    occ = int(record.get("occupancy", 0))
    light_lvl = int(record.get("light_level", 400))
    power_w = int(record.get("power_w", 0))

    ac = int(record.get("ac", 0))
    fan = int(record.get("fan", 0))
    tv = int(record.get("tv", 0))
    room_light = int(record.get("room_light", 0))
    refrigerator = int(record.get("refrigerator", 1))
    heater = int(record.get("heater", 0))
    microwave = int(record.get("microwave", 0))

    # -------------------------------------------------------------------------
    # RULE 1: Vacancy Waste (High-draw or active devices left on in vacant rooms)
    # -------------------------------------------------------------------------
    if occ == 0:
        if ac:
            reasons.append("Air Conditioner (1500W) is cooling an unoccupied home.")
            waste_watts += APPLIANCE_RATINGS["ac"]
        if heater:
            reasons.append("Space Heater (2000W) is heating an unoccupied home.")
            waste_watts += APPLIANCE_RATINGS["heater"]
        if tv:
            reasons.append("Television (120W) is left powered ON while the home is unoccupied.")
            waste_watts += APPLIANCE_RATINGS["tv"]
        if room_light:
            reasons.append("Room Light (20W) is left ON in an unoccupied room.")
            waste_watts += APPLIANCE_RATINGS["room_light"]
        if fan and not ac:
            reasons.append("Ceiling Fan (75W) is spinning in an unoccupied room.")
            waste_watts += APPLIANCE_RATINGS["fan"]

    # -------------------------------------------------------------------------
    # RULE 2: Daylight Lighting Waste (Light ON during ample daylight)
    # -------------------------------------------------------------------------
    if room_light and light_lvl > DAYLIGHT_LUX_THRESHOLD:
        # Avoid duplicate counting if already flagged under vacancy
        if occ != 0:
            reasons.append(f"Room Light is ON despite ample natural daylight ({light_lvl} lux).")
            waste_watts += APPLIANCE_RATINGS["room_light"]

    # -------------------------------------------------------------------------
    # RULE 3: Operational Conflict (AC and Heater simultaneously active)
    # -------------------------------------------------------------------------
    if ac and heater:
        reasons.append("Conflicting climate control: Both Air Conditioner (cooling) and Space Heater (heating) are active.")
        waste_watts += min(APPLIANCE_RATINGS["ac"], APPLIANCE_RATINGS["heater"])

    # -------------------------------------------------------------------------
    # RULE 4: Multi-Appliance Concurrent High Load
    # -------------------------------------------------------------------------
    high_power_active = []
    if ac:
        high_power_active.append("AC (1500W)")
    if heater:
        high_power_active.append("Heater (2000W)")
    if microwave:
        high_power_active.append("Microwave (1000W)")

    if len(high_power_active) >= 2 or power_w >= HIGH_POWER_WARNING_THRESHOLD_W:
        reasons.append(
            f"High grid load warning: Multiple high-power appliances active simultaneously ({', '.join(high_power_active)}) - Total: {power_w} W."
        )

    is_wasteful = len(reasons) > 0

    return {
        "wasteful": is_wasteful,
        "reasons": reasons,
        "potential_waste_watts": waste_watts,
    }
