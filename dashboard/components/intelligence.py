"""
Energy Intelligence & Diagnostic Components (Phase 3.3).
Provides:
1. AI Explanation Panel (Observed, Expected, Difference, Condition, Evidence, Action).
2. Telemetry Point Investigation Panel (Interactive point breakdown).
3. AI Anomaly Investigation Panel (Isolation Forest deep-dive).
4. Appliance Intelligence Detail Panel (Derived estimated load, contribution %, context).
5. Forecast Intelligence Panel (Next interval forecast horizon, expected change, honest methodology).
"""

from typing import Dict, Any, Optional, List
import pandas as pd
import streamlit as st

from dashboard.config import APPLIANCE_META
from dashboard.utils.formatting import get_icon, format_watts, render_html
from dashboard.components.alerts import severity_badge
from dashboard.state import (
    get_selected_timestamp,
    set_selected_timestamp,
    get_selected_anomaly,
    set_selected_anomaly,
    clear_investigation_selection,
    get_selected_appliance,
    set_selected_appliance,
)


def render_ai_explanation_panel(analysis: Dict[str, Any], theme: str = "dark") -> None:
    """
    Renders the Explainable AI Diagnostics breakdown panel.
    Strictly derived from actual backend data:
    - Observed Measured Load
    - Expected Appliance Load (Model 1)
    - Difference (Delta)
    - Detected Condition (Wasteful / High Load / Normal / Outlier)
    - Evidence (Occupancy state, conflicting rules, active high-draw devices)
    - Recommended Action (from backend recommendation engine)
    """
    if not analysis:
        st.info("Awaiting telemetry analysis from backend...")
        return

    energy = analysis.get("energy", {})
    sensors = analysis.get("sensors", {})
    appliances = analysis.get("appliances", {})
    ai = analysis.get("ai", {})
    waste = analysis.get("waste", {})
    severity = analysis.get("severity", "NORMAL")
    recommendation = analysis.get("recommendation", "Operating normally.")
    action_items = analysis.get("action_items", [])

    measured_w = float(energy.get("current_power_w", 0.0))
    expected_w = float(energy.get("predicted_power_w", measured_w))
    diff_w = measured_w - expected_w

    is_anomaly = bool(ai.get("is_anomaly", False))
    is_waste = bool(waste.get("is_wasteful", False))
    waste_reasons = waste.get("waste_reasons", [])
    occupancy = sensors.get("occupancy", 0)
    occ_str = "Occupied" if occupancy == 1 else "Vacant"

    # Identify condition from backend results
    if severity == "CRITICAL":
        detected_condition = "Critical System Load / Conflicting Appliance Operation"
        accent_color = "var(--danger)"
    elif is_waste:
        detected_condition = "Wasteful Energy Consumption Detected"
        accent_color = "var(--warning)"
    elif is_anomaly:
        detected_condition = "Statistical Telemetry Outlier (Isolation Forest)"
        accent_color = "var(--warning)"
    elif measured_w > 3500:
        detected_condition = "High Simultaneous Household Load"
        accent_color = "var(--warning)"
    else:
        detected_condition = "Nominal Baseline Consumption"
        accent_color = "var(--success)"

    # Identify evidence from real sensor/appliance states
    active_high_power = []
    for k, meta in APPLIANCE_META.items():
        if appliances.get(k, 0) == 1 and meta["watts"] >= 1000:
            active_high_power.append(meta["name"])

    evidence_points = []
    if waste_reasons:
        evidence_points.extend(waste_reasons)
    elif occupancy == 0 and active_high_power:
        evidence_points.append(f"Home is vacant while high-draw equipment ({', '.join(active_high_power)}) remains active.")
    elif len(active_high_power) >= 2:
        evidence_points.append(f"Multiple high-draw appliances operating concurrently: {', '.join(active_high_power)}.")
    elif is_anomaly:
        evidence_points.append(f"Telemetry feature vector deviated beyond statistical confidence interval (Score: {ai.get('anomaly_score', 0):+.3f}).")
    else:
        evidence_points.append(f"All active loads match current environmental telemetry and {occ_str} status.")

    evidence_html = "".join([f"<li style='margin-bottom:0.25rem;'>{e}</li>" for e in evidence_points])
    rec_text = recommendation if recommendation else "No intervention required. System is operating at peak efficiency."

    m_str, m_unit = format_watts(measured_w)
    e_str, e_unit = format_watts(expected_w)
    sign = "+" if diff_w >= 0 else ""
    d_str, d_unit = format_watts(diff_w)

    render_html(
        f"""
        <div class="apple-card" style="border-left: 4px solid {accent_color}; margin-top:0.75rem;">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.8rem;">
                <div style="display:flex; align-items:center; gap:0.5rem;">
                    {get_icon('activity', size=18, color=accent_color)}
                    <span style="font-weight:600; font-size:1rem; color:var(--text-primary);">AI Explanation & Diagnostics</span>
                </div>
                {severity_badge(severity)}
            </div>

            <!-- Structured Metric Breakdown Grid -->
            <div style="display:grid; grid-template-columns: 1fr 1fr 1fr; gap:0.75rem; margin-bottom:0.9rem;">
                <div style="background:var(--surface); border:1px solid var(--border-subtle); padding:0.6rem 0.8rem; border-radius:10px;">
                    <div style="font-size:0.7rem; color:var(--text-secondary); text-transform:uppercase; font-weight:600;">Observed Load</div>
                    <div style="font-size:1.3rem; font-weight:700; color:var(--text-primary);">{m_str} <span style="font-size:0.8rem; font-weight:normal;">{m_unit}</span></div>
                </div>
                <div style="background:var(--surface); border:1px solid var(--border-subtle); padding:0.6rem 0.8rem; border-radius:10px;">
                    <div style="font-size:0.7rem; color:var(--text-secondary); text-transform:uppercase; font-weight:600;">Expected Load (Model 1)</div>
                    <div style="font-size:1.3rem; font-weight:700; color:var(--text-secondary);">{e_str} <span style="font-size:0.8rem; font-weight:normal;">{e_unit}</span></div>
                </div>
                <div style="background:var(--surface); border:1px solid var(--border-subtle); padding:0.6rem 0.8rem; border-radius:10px;">
                    <div style="font-size:0.7rem; color:var(--text-secondary); text-transform:uppercase; font-weight:600;">Variance Difference</div>
                    <div style="font-size:1.3rem; font-weight:700; color:{accent_color};">{sign}{d_str} <span style="font-size:0.8rem; font-weight:normal;">{d_unit}</span></div>
                </div>
            </div>

            <!-- Condition and Evidence Section -->
            <div style="background:var(--surface); border:1px solid var(--border-subtle); padding:0.75rem 0.9rem; border-radius:12px; margin-bottom:0.75rem;">
                <div style="font-size:0.75rem; font-weight:600; color:var(--text-secondary); text-transform:uppercase; margin-bottom:0.3rem;">
                    Detected Condition:
                </div>
                <div style="font-size:0.95rem; font-weight:600; color:var(--text-primary); margin-bottom:0.5rem;">
                    {detected_condition}
                </div>
                <div style="font-size:0.75rem; font-weight:600; color:var(--text-secondary); text-transform:uppercase; margin-bottom:0.25rem;">
                    Empirical Evidence:
                </div>
                <ul style="font-size:0.85rem; color:var(--text-primary); margin:0; padding-left:1.2rem; line-height:1.4;">
                    {evidence_html}
                </ul>
            </div>

            <!-- Recommended Action -->
            <div style="display:flex; align-items:flex-start; gap:0.6rem; background:rgba(0,113,227,0.06); border:1px solid rgba(0,113,227,0.15); padding:0.65rem 0.85rem; border-radius:10px;">
                <span style="color:var(--accent); margin-top:2px;">{get_icon('zap', size=16, color='var(--accent)')}</span>
                <div style="font-size:0.85rem; color:var(--text-primary); line-height:1.4;">
                    <strong>Prescribed Action:</strong> {rec_text}
                </div>
            </div>
        </div>
        """
    )


def render_forecast_intelligence_card(
    forecast_data: Optional[Dict[str, Any]],
    current_w: Optional[float] = None,
    theme: str = "dark"
) -> None:
    """
    Renders the Next Interval Forecast intelligence card (Section 13 & 14).
    Displays current load, forecast power, expected change, direction, and horizon.
    """
    if not forecast_data:
        render_html(
            """
            <div class="apple-card">
                <div style="font-size:0.85rem; color:var(--text-secondary);">
                    Next interval forecast unavailable. Insufficient telemetry buffer for autoregression.
                </div>
            </div>
            """
        )
        return

    cur_w = float(current_w) if current_w is not None else float(forecast_data.get("current_power_w", 0.0))
    next_w = float(forecast_data.get("predicted_next_power_w", forecast_data.get("forecast_power_w", cur_w)))
    change_w = float(forecast_data.get("expected_change_w", next_w - cur_w))
    horizon = forecast_data.get("forecast_horizon", "Next 2.5 seconds")
    direction = forecast_data.get("direction", "Steady")
    model_name = forecast_data.get("model", "Short-Term Autoregression (Linear Regression)")

    sign = "+" if change_w >= 0 else ""
    c_str, c_unit = format_watts(cur_w)
    f_str, f_unit = format_watts(next_w)
    ch_str, ch_unit = format_watts(change_w)

    dir_color = "var(--warning)" if change_w > 50 else ("var(--success)" if change_w < -50 else "var(--text-secondary)")
    dir_icon = "trending-up" if change_w > 0 else ("trending-down" if change_w < 0 else "activity")

    render_html(
        f"""
        <div class="apple-card">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.75rem;">
                <div style="display:flex; align-items:center; gap:0.5rem;">
                    {get_icon('clock', size=18, color='var(--accent)')}
                    <span style="font-weight:600; font-size:0.95rem; color:var(--text-primary);">Next Interval Forecast</span>
                </div>
                <span class="status-chip online" style="font-size:0.7rem;">{horizon}</span>
            </div>

            <div style="display:grid; grid-template-columns: 1fr 1fr 1fr; gap:0.6rem; margin-bottom:0.8rem;">
                <div style="background:var(--surface); border:1px solid var(--border-subtle); padding:0.5rem 0.7rem; border-radius:10px;">
                    <div style="font-size:0.68rem; color:var(--text-secondary); text-transform:uppercase;">Current</div>
                    <div style="font-size:1.15rem; font-weight:700; color:var(--text-primary);">{c_str} <span style="font-size:0.7rem; font-weight:normal;">{c_unit}</span></div>
                </div>
                <div style="background:var(--surface); border:1px solid var(--border-subtle); padding:0.5rem 0.7rem; border-radius:10px;">
                    <div style="font-size:0.68rem; color:var(--text-secondary); text-transform:uppercase;">Forecast</div>
                    <div style="font-size:1.15rem; font-weight:700; color:var(--accent);">{f_str} <span style="font-size:0.7rem; font-weight:normal;">{f_unit}</span></div>
                </div>
                <div style="background:var(--surface); border:1px solid var(--border-subtle); padding:0.5rem 0.7rem; border-radius:10px;">
                    <div style="font-size:0.68rem; color:var(--text-secondary); text-transform:uppercase;">Expected Change</div>
                    <div style="font-size:1.15rem; font-weight:700; color:{dir_color};">{sign}{ch_str} <span style="font-size:0.7rem; font-weight:normal;">{ch_unit}</span></div>
                </div>
            </div>

            <div style="display:flex; align-items:center; gap:0.4rem; font-size:0.78rem; color:var(--text-secondary); margin-bottom:0.4rem;">
                {get_icon(dir_icon, size=15, color=dir_color)}
                <span>Trajectory: <strong style="color:var(--text-primary);">{direction}</strong> ({sign}{ch_str} {ch_unit})</span>
            </div>

            <div style="font-size:0.72rem; color:var(--text-tertiary); line-height:1.4; border-top:1px solid var(--border-subtle); padding-top:0.5rem; margin-top:0.4rem;">
                Generated by {model_name} using lagged telemetry (t-1, t-2, t-3) and environmental features. Horizon represents the single next 2.5s telemetry interval.
            </div>
        </div>
        """
    )


def render_telemetry_investigation_panel(df_history: pd.DataFrame, theme: str = "dark") -> None:
    """
    Renders the Telemetry Point Investigation Panel (Section 5).
    Allows interactive inspection of any timestamp in the historical record.
    Displays:
    - Timestamp
    - Measured Power
    - Expected Power
    - Difference
    - Temperature, Humidity, Occupancy, Light Level
    - Active Appliances
    - Anomaly Score & Waste Status
    """
    if df_history.empty or "datetime" not in df_history.columns:
        return

    # Check if a timestamp is selected in state
    selected_ts = get_selected_timestamp()

    # Create an expander or card for the investigation panel
    render_html(
        f"""
        <div style="display:flex; align-items:center; gap:0.45rem; margin:1rem 0 0.5rem 0;">
            <span style="color:var(--accent); display:inline-flex; align-items:center;">{get_icon('activity', size=18, color='var(--accent)')}</span>
            <span style="font-size:1.1rem; font-weight:600; color:var(--text-primary);">Telemetry Point Investigation</span>
        </div>
        """
    )
    
    # Selection control: allows picking any point in the time horizon
    time_options = df_history["datetime"].dt.strftime("%H:%M:%S (%Y-%m-%d)").tolist()
    timestamps_raw = df_history["datetime"].astype(str).tolist()
    
    current_index = 0
    if selected_ts:
        # Match nearest or exact timestamp
        for i, raw in enumerate(timestamps_raw):
            if selected_ts in raw or raw in selected_ts:
                current_index = i
                break

    col_select, col_btn = st.columns([3, 1])
    with col_select:
        selected_label = st.selectbox(
            "Select Telemetry Timestamp to Investigate",
            options=time_options,
            index=current_index,
            key="telemetry_point_selector",
            help="Select any historical reading to analyze all concurrent sensor and appliance measurements"
        )
    with col_btn:
        st.markdown("<div style='height:1.75rem;'></div>", unsafe_allow_html=True)
        if st.button("Reset / Live Point", key="btn_reset_investigation", use_container_width=True):
            clear_investigation_selection()
            st.rerun()

    chosen_idx = time_options.index(selected_label) if selected_label in time_options else current_index
    record = df_history.iloc[chosen_idx]

    # Extract verified fields
    ts_val = record["datetime"].strftime("%Y-%m-%d %H:%M:%S UTC")
    power_w = float(record.get("power_w", 0.0))
    expected_w = float(record.get("predicted_power_w", power_w))
    diff_w = power_w - expected_w
    sign = "+" if diff_w >= 0 else ""
    
    temp = record.get("temperature", 0.0)
    humidity = record.get("humidity", 0.0)
    occ = int(record.get("occupancy", 0))
    occ_str = "Occupied" if occ == 1 else "Vacant"
    light = record.get("light_level", 0.0)
    active_apps = record.get("active_appliances_str", "None")
    
    is_anomaly = int(record.get("is_anomaly", 0)) == 1
    anom_score = float(record.get("anomaly_score", 0.0))
    is_wasteful = int(record.get("wasteful", 0)) == 1

    # Severity determination
    if is_wasteful and is_anomaly:
        sev = "CRITICAL"
        status_text = "Severe Outlier & Wasteful Usage"
        color = "var(--danger)"
    elif is_wasteful:
        sev = "HIGH"
        status_text = "Wasteful Energy Consumption"
        color = "var(--warning)"
    elif is_anomaly:
        sev = "WARNING"
        status_text = "Statistical Outlier Detected"
        color = "var(--warning)"
    else:
        sev = "NORMAL"
        status_text = "Nominal Operation"
        color = "var(--success)"

    p_str, p_unit = format_watts(power_w)
    exp_str, exp_unit = format_watts(expected_w)
    d_str, d_unit = format_watts(diff_w)

    render_html(
        f"""
        <div class="apple-card" style="border-left: 4px solid {color}; margin-top:0.5rem; margin-bottom:1rem;">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.75rem;">
                <div style="display:flex; align-items:center; gap:0.5rem;">
                    {get_icon('clock', size=18, color=color)}
                    <span style="font-weight:600; font-size:1rem; color:var(--text-primary);">{ts_val}</span>
                </div>
                {severity_badge(sev)}
            </div>

            <!-- Primary Power Metrics -->
            <div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(130px, 1fr)); gap:0.6rem; margin-bottom:0.8rem;">
                <div style="background:var(--surface); border:1px solid var(--border-subtle); padding:0.5rem 0.75rem; border-radius:10px;">
                    <div style="font-size:0.68rem; color:var(--text-secondary); text-transform:uppercase;">Measured Load</div>
                    <div style="font-size:1.2rem; font-weight:700; color:var(--text-primary);">{p_str} <span style="font-size:0.7rem; font-weight:normal;">{p_unit}</span></div>
                </div>
                <div style="background:var(--surface); border:1px solid var(--border-subtle); padding:0.5rem 0.75rem; border-radius:10px;">
                    <div style="font-size:0.68rem; color:var(--text-secondary); text-transform:uppercase;">Expected Load</div>
                    <div style="font-size:1.2rem; font-weight:700; color:var(--text-secondary);">{exp_str} <span style="font-size:0.7rem; font-weight:normal;">{exp_unit}</span></div>
                </div>
                <div style="background:var(--surface); border:1px solid var(--border-subtle); padding:0.5rem 0.75rem; border-radius:10px;">
                    <div style="font-size:0.68rem; color:var(--text-secondary); text-transform:uppercase;">Variance</div>
                    <div style="font-size:1.2rem; font-weight:700; color:{color};">{sign}{d_str} <span style="font-size:0.7rem; font-weight:normal;">{d_unit}</span></div>
                </div>
                <div style="background:var(--surface); border:1px solid var(--border-subtle); padding:0.5rem 0.75rem; border-radius:10px;">
                    <div style="font-size:0.68rem; color:var(--text-secondary); text-transform:uppercase;">Isolation Score</div>
                    <div style="font-size:1.2rem; font-weight:700; color:var(--text-primary);">{anom_score:+.3f}</div>
                </div>
            </div>

            <!-- Environmental Telemetry Context -->
            <div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(130px, 1fr)); gap:0.6rem; margin-bottom:0.8rem;">
                <div style="background:var(--surface); border:1px solid var(--border-subtle); padding:0.4rem 0.6rem; border-radius:8px;">
                    <span style="font-size:0.7rem; color:var(--text-secondary);">Temperature:</span>
                    <strong style="font-size:0.85rem; color:var(--text-primary); margin-left:0.3rem;">{temp:.1f} °C</strong>
                </div>
                <div style="background:var(--surface); border:1px solid var(--border-subtle); padding:0.4rem 0.6rem; border-radius:8px;">
                    <span style="font-size:0.7rem; color:var(--text-secondary);">Humidity:</span>
                    <strong style="font-size:0.85rem; color:var(--text-primary); margin-left:0.3rem;">{humidity:.1f} %</strong>
                </div>
                <div style="background:var(--surface); border:1px solid var(--border-subtle); padding:0.4rem 0.6rem; border-radius:8px;">
                    <span style="font-size:0.7rem; color:var(--text-secondary);">Occupancy:</span>
                    <strong style="font-size:0.85rem; color:var(--text-primary); margin-left:0.3rem;">{occ_str}</strong>
                </div>
                <div style="background:var(--surface); border:1px solid var(--border-subtle); padding:0.4rem 0.6rem; border-radius:8px;">
                    <span style="font-size:0.7rem; color:var(--text-secondary);">Ambient Light:</span>
                    <strong style="font-size:0.85rem; color:var(--text-primary); margin-left:0.3rem;">{light:.0f} lx</strong>
                </div>
            </div>

            <!-- Active Appliances & Diagnostics -->
            <div style="background:var(--surface); border:1px solid var(--border-subtle); padding:0.6rem 0.8rem; border-radius:10px;">
                <div style="font-size:0.75rem; color:var(--text-secondary); margin-bottom:0.2rem;">
                    <strong>Active Appliances:</strong> <span style="color:var(--text-primary);">{active_apps}</span>
                </div>
                <div style="font-size:0.75rem; color:var(--text-secondary);">
                    <strong>Diagnostic Status:</strong> <span style="color:{color}; font-weight:600;">{status_text}</span>
                    (Waste Flag: {"TRUE" if is_wasteful else "FALSE"} • Anomaly Flag: {"TRUE" if is_anomaly else "FALSE"})
                </div>
            </div>
        </div>
        """
    )


def render_anomaly_investigation_panel(df_history: pd.DataFrame, current_analysis: Dict[str, Any], theme: str = "dark") -> None:
    """
    Renders the AI Anomaly Investigation Panel (Section 6).
    Activates when anomalies exist or when an anomaly is selected.
    Displays:
    - Event (Timestamp, measured power, anomaly score, severity)
    - Context (Occupancy, temp, humidity, light, active devices)
    - Expected Behavior (Expected power, deviation)
    - Waste Analysis (Waste flag, rule explanation, avoidable load)
    - Recommendation (from backend engine)
    """
    if df_history.empty or "is_anomaly" not in df_history.columns:
        return

    anomalies = df_history[df_history["is_anomaly"] == 1].copy()

    render_html(
        f"""
        <div style="display:flex; align-items:center; gap:0.45rem; margin:1rem 0 0.5rem 0;">
            <span style="color:var(--warning); display:inline-flex; align-items:center;">{get_icon('alert-triangle', size=18, color='var(--warning)')}</span>
            <span style="font-size:1.1rem; font-weight:600; color:var(--text-primary);">AI Anomaly Deep-Dive Investigation</span>
        </div>
        """
    )

    if anomalies.empty:
        render_html(
            f"""
            <div class="apple-card" style="border-left: 4px solid var(--success);">
                <div style="display:flex; align-items:center; gap:0.5rem;">
                    <span style="color:var(--success); display:inline-flex; align-items:center;">{get_icon('check-circle', size=16, color='var(--success)')}</span>
                    <span style="font-weight:600; font-size:0.95rem; color:var(--text-primary);">Zero Anomalies Detected in Current Horizon</span>
                </div>
                <div style="font-size:0.82rem; color:var(--text-secondary); margin-top:0.3rem;">
                    All telemetry vectors align with nominal statistical distributions and rule constraints.
                </div>
            </div>
            """
        )
        return

    # User can select which anomaly occurrence to investigate
    anomaly_options = [
        f"{row['datetime'].strftime('%H:%M:%S')} — {int(row['power_w'])}W (Score: {row['anomaly_score']:+.3f})"
        for _, row in anomalies.iterrows()
    ]
    
    selected_idx = 0
    selected_anomaly_ts = get_selected_anomaly()
    if selected_anomaly_ts:
        for i, (_, row) in enumerate(anomalies.iterrows()):
            if str(selected_anomaly_ts) in str(row["datetime"]):
                selected_idx = i
                break

    chosen_anomaly_label = st.selectbox(
        "Select Anomaly Incident to Inspect",
        options=anomaly_options,
        index=selected_idx,
        key="anomaly_incident_select"
    )

    idx_in_anom = anomaly_options.index(chosen_anomaly_label) if chosen_anomaly_label in anomaly_options else 0
    anom_row = anomalies.iloc[idx_in_anom]

    # Contextual fields
    ts_str = anom_row["datetime"].strftime("%Y-%m-%d %H:%M:%S UTC")
    power_w = float(anom_row["power_w"])
    expected_w = float(anom_row.get("predicted_power_w", power_w))
    dev_w = power_w - expected_w
    score = float(anom_row.get("anomaly_score", -0.05))
    occ_str = "Occupied" if anom_row.get("occupancy", 0) == 1 else "Vacant"
    temp = float(anom_row.get("temperature", 0.0))
    hum = float(anom_row.get("humidity", 0.0))
    light = float(anom_row.get("light_level", 0.0))
    devices = anom_row.get("active_appliances_str", "None")
    is_waste = int(anom_row.get("wasteful", 0)) == 1

    # Backend recommendation and rule explanations
    waste_reasons = current_analysis.get("waste", {}).get("waste_reasons", [])
    recommendation = current_analysis.get("recommendation", "Review concurrent appliance operations.")

    p_str, p_unit = format_watts(power_w)
    e_str, e_unit = format_watts(expected_w)
    d_str, d_unit = format_watts(dev_w)
    sign = "+" if dev_w >= 0 else ""

    render_html(
        f"""
        <div class="apple-card" style="border-left: 4px solid var(--danger); margin-top:0.5rem; margin-bottom:1rem;">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.8rem;">
                <div style="display:flex; align-items:center; gap:0.5rem;">
                    {get_icon('alert-octagon', size=20, color='var(--danger)')}
                    <span style="font-weight:600; font-size:1.05rem; color:var(--text-primary);">Anomaly Event: {ts_str}</span>
                </div>
                {severity_badge("CRITICAL" if is_waste else "HIGH")}
            </div>

            <!-- Event & Expected Deviation -->
            <div style="display:grid; grid-template-columns: 1fr 1fr 1fr; gap:0.6rem; margin-bottom:0.8rem;">
                <div style="background:var(--surface); border:1px solid var(--border-subtle); padding:0.5rem 0.75rem; border-radius:10px;">
                    <div style="font-size:0.68rem; color:var(--text-secondary); text-transform:uppercase;">Measured Load</div>
                    <div style="font-size:1.25rem; font-weight:700; color:var(--danger);">{p_str} <span style="font-size:0.7rem; font-weight:normal;">{p_unit}</span></div>
                </div>
                <div style="background:var(--surface); border:1px solid var(--border-subtle); padding:0.5rem 0.75rem; border-radius:10px;">
                    <div style="font-size:0.68rem; color:var(--text-secondary); text-transform:uppercase;">Expected Load</div>
                    <div style="font-size:1.25rem; font-weight:700; color:var(--text-secondary);">{e_str} <span style="font-size:0.7rem; font-weight:normal;">{e_unit}</span></div>
                </div>
                <div style="background:var(--surface); border:1px solid var(--border-subtle); padding:0.5rem 0.75rem; border-radius:10px;">
                    <div style="font-size:0.68rem; color:var(--text-secondary); text-transform:uppercase;">Outlier Score</div>
                    <div style="font-size:1.25rem; font-weight:700; color:var(--text-primary);">{score:+.4f}</div>
                </div>
            </div>

            <!-- Environmental Context -->
            <div style="background:var(--surface); border:1px solid var(--border-subtle); padding:0.65rem 0.85rem; border-radius:10px; margin-bottom:0.75rem;">
                <div style="font-size:0.72rem; font-weight:600; color:var(--text-secondary); text-transform:uppercase; margin-bottom:0.35rem;">Telemetry Context</div>
                <div style="display:flex; flex-wrap:wrap; gap:1rem; font-size:0.85rem; color:var(--text-primary);">
                    <span><strong>Occupancy:</strong> {occ_str}</span>
                    <span><strong>Temperature:</strong> {temp:.1f} °C</span>
                    <span><strong>Humidity:</strong> {hum:.1f} %</span>
                    <span><strong>Light:</strong> {light:.0f} lx</span>
                </div>
                <div style="font-size:0.85rem; color:var(--text-primary); margin-top:0.4rem;">
                    <strong>Active Devices:</strong> {devices}
                </div>
            </div>

            <!-- Waste & Prescribed Action -->
            <div style="background:rgba(255,159,10,0.08); border:1px solid rgba(255,159,10,0.2); padding:0.65rem 0.85rem; border-radius:10px;">
                <div style="font-size:0.82rem; color:var(--text-primary); margin-bottom:0.3rem;">
                    <strong>Waste Diagnostic:</strong> {"Identified avoidable wasteful load" if is_waste else "High power surge without rule violation"}
                </div>
                <div style="font-size:0.82rem; color:var(--text-primary);">
                    <strong>Engine Recommendation:</strong> {recommendation}
                </div>
            </div>
        </div>
        """
    )


def render_appliance_detail_panel(
    selected_appliance: str,
    appliances_dict: Optional[Dict[str, int]],
    current_power: Optional[float],
    df_history: pd.DataFrame,
    theme: str = "dark"
) -> None:
    """
    Renders the Appliance Intelligence Detail Drawer (Section 4 & Section 18).
    Displays:
    - Appliance name & rated power
    - Current State (ON/OFF)
    - Estimated Appliance Load (clearly labeled!)
    - Share of Current Load (%)
    - Status Chip (NORMAL, ATTENTION, WASTEFUL, HIGH LOAD)
    - Related Waste Events in current window
    - Usage Context (Occupancy, Temperature)
    """
    if not selected_appliance or selected_appliance == "All Appliances":
        return

    # Find meta by name or key
    app_key = None
    app_meta = None
    for k, meta in APPLIANCE_META.items():
        if meta["name"].lower() == selected_appliance.lower() or k.lower() == selected_appliance.lower():
            app_key = k
            app_meta = meta
            break

    if not app_key or not app_meta:
        return

    states = appliances_dict or {}
    is_on = int(states.get(app_key, 0)) == 1
    rated_w = float(app_meta["watts"])
    est_w = rated_w if is_on else 0.0
    total_w = float(current_power) if current_power and current_power > 0 else 1.0
    share_pct = (est_w / total_w) * 100.0 if total_w > 0 else 0.0

    # Historical stats in current buffer
    times_on = 0
    times_waste = 0
    times_anomaly = 0
    total_samples = len(df_history)

    if not df_history.empty and app_key in df_history.columns:
        app_on_mask = df_history[app_key] == 1
        times_on = int(app_on_mask.sum())
        if "wasteful" in df_history.columns:
            times_waste = int((app_on_mask & (df_history["wasteful"] == 1)).sum())
        if "is_anomaly" in df_history.columns:
            times_anomaly = int((app_on_mask & (df_history["is_anomaly"] == 1)).sum())

    duty_cycle = (times_on / total_samples * 100.0) if total_samples > 0 else 0.0

    # Determine status
    if is_on and times_waste > 0:
        status_label = "WASTEFUL"
        chip_class = "severity-badge warning"
        color = "var(--warning)"
    elif is_on and total_w > 3500 and rated_w >= 1000:
        status_label = "HIGH LOAD"
        chip_class = "severity-badge danger"
        color = "var(--danger)"
    elif is_on:
        status_label = "NORMAL"
        chip_class = "severity-badge normal"
        color = "var(--success)"
    else:
        status_label = "STANDBY"
        chip_class = "status-chip offline"
        color = "var(--text-tertiary)"

    e_str, e_unit = format_watts(est_w)
    r_str, r_unit = format_watts(rated_w)

    render_html(
        f"""
        <div class="apple-card" style="border-left: 4px solid {color}; margin-top:0.75rem; margin-bottom:1rem;">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.75rem;">
                <div style="display:flex; align-items:center; gap:0.5rem;">
                    {get_icon(app_meta.get('icon', 'zap'), size=20, color=color)}
                    <span style="font-weight:600; font-size:1.05rem; color:var(--text-primary);">{app_meta['name']} Intelligence</span>
                </div>
                <div style="display:flex; align-items:center; gap:0.4rem;">
                    <span class="{chip_class}">{status_label}</span>
                    <span class="status-chip {'online' if is_on else 'offline'}">{'ON' if is_on else 'OFF'}</span>
                </div>
            </div>

            <!-- Granular Metric Grid -->
            <div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(130px, 1fr)); gap:0.6rem; margin-bottom:0.8rem;">
                <div style="background:var(--surface); border:1px solid var(--border-subtle); padding:0.5rem 0.75rem; border-radius:10px;">
                    <div style="font-size:0.68rem; color:var(--text-secondary); text-transform:uppercase;">Rated Capacity</div>
                    <div style="font-size:1.2rem; font-weight:700; color:var(--text-primary);">{r_str} <span style="font-size:0.7rem; font-weight:normal;">{r_unit}</span></div>
                </div>
                <div style="background:var(--surface); border:1px solid var(--border-subtle); padding:0.5rem 0.75rem; border-radius:10px;">
                    <div style="font-size:0.68rem; color:var(--text-secondary); text-transform:uppercase;">Estimated Appliance Load</div>
                    <div style="font-size:1.2rem; font-weight:700; color:var(--accent);">{e_str} <span style="font-size:0.7rem; font-weight:normal;">{e_unit}</span></div>
                </div>
                <div style="background:var(--surface); border:1px solid var(--border-subtle); padding:0.5rem 0.75rem; border-radius:10px;">
                    <div style="font-size:0.68rem; color:var(--text-secondary); text-transform:uppercase;">Household Share</div>
                    <div style="font-size:1.2rem; font-weight:700; color:var(--text-primary);">{share_pct:.1f}%</div>
                </div>
                <div style="background:var(--surface); border:1px solid var(--border-subtle); padding:0.5rem 0.75rem; border-radius:10px;">
                    <div style="font-size:0.68rem; color:var(--text-secondary); text-transform:uppercase;">Window Duty Cycle</div>
                    <div style="font-size:1.2rem; font-weight:700; color:var(--text-primary);">{duty_cycle:.1f}%</div>
                </div>
            </div>

            <!-- Historical Incident Attribution -->
            <div style="background:var(--surface); border:1px solid var(--border-subtle); padding:0.6rem 0.8rem; border-radius:10px; font-size:0.8rem; color:var(--text-secondary);">
                <span>Related Waste Events in Buffer: <strong style="color:var(--text-primary);">{times_waste}</strong></span>
                <span style="margin:0 0.5rem;">•</span>
                <span>Related Anomalies: <strong style="color:var(--text-primary);">{times_anomaly}</strong></span>
                <span style="margin:0 0.5rem;">•</span>
                <span>Category: <strong style="color:var(--text-primary);">{app_meta['category']}</strong></span>
            </div>
            
            <div style="font-size:0.7rem; color:var(--text-tertiary); margin-top:0.4rem;">
                * Note: Individual appliance wattage is calculated from rated capacity and binary telemetry states as <em>Estimated Appliance Load</em> (not directly metered per-device CT clamp).
            </div>
        </div>
        """
    )
