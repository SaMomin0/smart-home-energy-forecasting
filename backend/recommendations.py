"""
Recommendation and Severity Synthesis Engine.
Synthesizes outputs from Linear Regression (Prediction), Isolation Forest (Anomaly Detection),
and Rule-Based Analysis (Waste Detection) to calculate unified Severity and generate
dynamic, context-specific energy-saving recommendations.
"""

from typing import Dict, Any, List, Tuple
from backend.config import (
    SEVERITY_NORMAL,
    SEVERITY_WARNING,
    SEVERITY_HIGH,
    SEVERITY_CRITICAL,
    HIGH_POWER_WARNING_THRESHOLD_W,
    HIGH_POWER_CRITICAL_THRESHOLD_W,
)


def compute_severity_and_recommendations(
    telemetry: Dict[str, Any],
    prediction_info: Dict[str, Any],
    anomaly_info: Dict[str, Any],
    waste_info: Dict[str, Any],
) -> Tuple[str, str, List[str]]:
    """
    Combines:
      - Actual vs Predicted Power (Regression)
      - Anomaly Status & Score (Isolation Forest)
      - Rule-Based Waste Flags & Reasons (Rules Engine)
      - Total Household Load

    Returns:
        (severity, primary_recommendation, action_list)
    """
    power_w = int(telemetry.get("power_w", 0))
    is_anomaly = anomaly_info.get("is_anomaly", False)
    is_wasteful = waste_info.get("wasteful", False)
    waste_reasons = waste_info.get("reasons", [])
    potential_waste = waste_info.get("potential_waste_watts", 0)
    diff_w = prediction_info.get("difference_w", 0.0)

    ac = int(telemetry.get("ac", 0))
    heater = int(telemetry.get("heater", 0))
    microwave = int(telemetry.get("microwave", 0))
    tv = int(telemetry.get("tv", 0))
    room_light = int(telemetry.get("room_light", 0))
    fan = int(telemetry.get("fan", 0))
    occ = int(telemetry.get("occupancy", 0))

    actions: List[str] = []
    severity = SEVERITY_NORMAL

    # -------------------------------------------------------------------------
    # 1. EVALUATE SEVERITY TIER
    # -------------------------------------------------------------------------
    if power_w >= HIGH_POWER_CRITICAL_THRESHOLD_W or (ac and heater) or (power_w >= 4000 and is_anomaly):
        severity = SEVERITY_CRITICAL
    elif is_anomaly or power_w >= HIGH_POWER_WARNING_THRESHOLD_W or (is_wasteful and potential_waste >= 1000):
        severity = SEVERITY_HIGH
    elif is_wasteful or abs(diff_w) > 400:
        severity = SEVERITY_WARNING
    else:
        severity = SEVERITY_NORMAL

    # -------------------------------------------------------------------------
    # 2. GENERATE TARGETED ACTIONS
    # -------------------------------------------------------------------------
    if occ == 0:
        if ac:
            actions.append("Turn OFF Air Conditioner (1500W): Room is unoccupied.")
        if heater:
            actions.append("Turn OFF Space Heater (2000W): Room is unoccupied.")
        if tv:
            actions.append("Turn OFF Television (120W): Left running in vacant room.")
        if room_light:
            actions.append("Turn OFF Room Light (20W): No occupants detected.")
        if fan:
            actions.append("Turn OFF Ceiling Fan (75W): Room is vacant.")

    if ac and heater:
        actions.append("Deactivate either AC or Space Heater immediately to eliminate conflicting HVAC thermal waste.")

    if power_w >= HIGH_POWER_WARNING_THRESHOLD_W:
        actions.append(f"Household power ({power_w}W) is near breaker capacity. Shed concurrent heavy loads (Heater/Microwave/AC).")

    if room_light and int(telemetry.get("light_level", 0)) > 300 and occ == 1:
        actions.append("Utilize available natural daylight by opening blinds and switching off the room light.")

    # -------------------------------------------------------------------------
    # 3. SYNTHESIZE PRIMARY SUMMARY RECOMMENDATION
    # -------------------------------------------------------------------------
    if severity == SEVERITY_CRITICAL:
        if ac and heater:
            primary_rec = "CRITICAL ALERT: Severe energy conflict! Turn off competing Space Heater or AC to prevent massive thermal waste."
        else:
            primary_rec = f"CRITICAL OVERLOAD: Extreme power demand ({power_w} W)! Turn off high-wattage appliances immediately to protect circuits."
    elif severity == SEVERITY_HIGH:
        if is_wasteful and occ == 0:
            primary_rec = f"HIGH WASTE ALERT: Home is vacant but major appliances ({potential_waste} W) remain active. Shut off idle equipment."
        elif is_anomaly:
            primary_rec = "ANOMALY DETECTED: Power consumption significantly deviates from normal behavioral patterns. Inspect active devices."
        else:
            primary_rec = f"HIGH DEMAND WARNING: Multi-appliance load ({power_w} W) exceeds 3000 W limit. Reduce simultaneous appliance usage."
    elif severity == SEVERITY_WARNING:
        if is_wasteful:
            primary_rec = f"ENERGY SAVING OPPORTUNITY: {waste_reasons[0]}"
        else:
            primary_rec = "USAGE NOTICE: Minor variance detected between observed and predicted power draw."
    else:
        primary_rec = "OPTIMAL OPERATION: Household energy consumption and appliance states are within expected normal bounds."

    return severity, primary_rec, actions
