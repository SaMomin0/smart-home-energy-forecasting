"""
Smart Home Energy Consumption Forecasting & Wasteful Usage Detection
Apple-Inspired Ultra-Minimized Frontend (High-Density Architecture).

Entrypoint:
    streamlit run dashboard/app.py
"""

import time
import os
from pathlib import Path
from typing import Dict, Any, Optional

import streamlit as st
import pandas as pd

# Must be the very first Streamlit call
st.set_page_config(
    page_title="Smart Home Energy AI",
    page_icon=":zap:",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Internal Dashboard Imports
from dashboard.config import (
    BACKEND_URL,
    DEFAULT_REFRESH_INTERVAL_SECONDS,
    MIN_REFRESH_INTERVAL_SECONDS,
    MAX_REFRESH_INTERVAL_SECONDS,
    NAV_PAGES,
    APPLIANCE_META,
)
from dashboard.api_client import get_api_client
from dashboard.utils.chart_data import normalize_history, filter_by_time_range
from dashboard.utils.formatting import render_html, get_icon
from dashboard.state import (
    init_session_state,
    get_current_page,
    set_current_page,
    get_selected_appliance,
    set_selected_appliance,
    get_selected_time_range,
    set_selected_time_range,
    is_live_mode,
    get_selected_scenario,
    get_theme_mode,
    toggle_theme_mode,
    get_previous_power,
    update_previous_power,
    get_selected_timestamp,
    get_selected_anomaly,
    get_last_scenario_status,
    set_last_scenario_status,
    clear_investigation_selection,
)
from dashboard.components import (
    app_header,
    navigation_bar,
    page_title,
    section_header,
    current_power_card,
    expected_power_card,
    forecast_power_card,
    energy_today_card,
    temperature_card,
    humidity_card,
    occupancy_card,
    light_level_card,
    ai_status_card,
    anomaly_score_card,
    waste_alert_card,
    ai_explanation_panel,
    recommendation_panel,
    action_items_panel,
    appliance_grid,
    system_status_panel,
    model_status_panel,
    time_range_selector,
    live_pause_control,
    refresh_control,
    scenario_selector,
    empty_state,
    loading_state,
    error_state,
    render_ai_explanation_panel,
    render_forecast_intelligence_card,
    render_telemetry_investigation_panel,
    render_anomaly_investigation_panel,
    render_appliance_detail_panel,
)
from dashboard.components.charts import (
    render_power_timeline_chart,
    render_actual_vs_expected_vs_forecast_chart,
    render_appliance_contribution_chart,
    render_energy_composition_chart,
    render_energy_pattern_heatmap,
    render_occupancy_vs_power_chart,
    render_temperature_vs_power_chart,
    render_anomaly_timeline_chart,
    render_power_flow_sankey,
    render_energy_waterfall_chart,
)


def load_stylesheet(filename: str) -> str:
    """Reads a local CSS file from dashboard/styles/."""
    css_path = Path(__file__).parent / "styles" / filename
    if css_path.exists():
        with open(css_path, "r", encoding="utf-8") as f:
            return f.read()
    return ""


def apply_theme_and_styles(theme: str) -> None:
    """Injects core stylesheets and applies light/dark CSS variables to .stApp."""
    theme_css = load_stylesheet("theme.css")
    comp_css = load_stylesheet("components.css")
    resp_css = load_stylesheet("responsive.css")

    if theme == "light":
        theme_override = """
        :root, .stApp {
            --bg-main: #FFFFFF !important;
            --surface: #FFFFFF !important;
            --surface-elevated: rgba(255, 255, 255, 0.95) !important;
            --surface-glass: rgba(245, 247, 248, 0.88) !important;
            --border: rgba(0, 18, 25, 0.08) !important;
            --border-subtle: rgba(0, 18, 25, 0.04) !important;
            --border-highlight: rgba(0, 18, 25, 0.20) !important;
            --text-primary: #080708 !important;
            --text-secondary: #005F73 !important;
            --text-tertiary: #6E7B82 !important;
            --accent: #0A9396 !important;
            --accent-soft: rgba(10, 147, 150, 0.12) !important;
            --success: #0A9396 !important;
            --success-soft: rgba(148, 210, 189, 0.25) !important;
            --warning: #EE9B00 !important;
            --warning-soft: rgba(238, 155, 0, 0.15) !important;
            --danger: #AE2012 !important;
            --danger-soft: rgba(174, 32, 18, 0.15) !important;
        }
        """
    else:
        theme_override = """
        :root, .stApp {
            --bg-main: #080708 !important;
            --surface: #001219 !important;
            --surface-elevated: rgba(0, 18, 25, 0.95) !important;
            --surface-glass: rgba(0, 18, 25, 0.78) !important;
            --border: rgba(148, 210, 189, 0.14) !important;
            --border-subtle: rgba(255, 255, 255, 0.05) !important;
            --border-highlight: rgba(148, 210, 189, 0.32) !important;
            --text-primary: #FFFFFF !important;
            --text-secondary: #94D2BD !important;
            --text-tertiary: #7D8E95 !important;
            --accent: #0A9396 !important;
            --accent-soft: rgba(10, 147, 150, 0.22) !important;
            --success: #94D2BD !important;
            --success-soft: rgba(148, 210, 189, 0.18) !important;
            --warning: #EE9B00 !important;
            --warning-soft: rgba(238, 155, 0, 0.22) !important;
            --danger: #AE2012 !important;
            --danger-soft: rgba(174, 32, 18, 0.25) !important;
            --critical: #9B2226 !important;
            --critical-soft: rgba(155, 34, 38, 0.30) !important;
            --info: #005F73 !important;
        }
        """

    full_css = f"""<style>
{theme_css}
{comp_css}
{resp_css}
{theme_override}
</style>"""
    render_html(full_css)


def render_sidebar() -> float:
    """Renders the ultra-compact sidebar controls and returns refresh interval."""
    with st.sidebar:
        render_html(
            f"""
            <div style="display:flex; align-items:center; gap:0.4rem; margin-bottom:0.75rem;">
                <span style="display:inline-flex; align-items:center; color:var(--accent);">{get_icon('zap', size=18, color='var(--accent)')}</span>
                <span style="font-size:0.95rem; font-weight:700; color:var(--text-primary);">Controls</span>
            </div>
            """
        )

        st.markdown("**Streaming State**")
        live_pause_control()

        interval = st.slider(
            "Refresh (sec)",
            min_value=MIN_REFRESH_INTERVAL_SECONDS,
            max_value=MAX_REFRESH_INTERVAL_SECONDS,
            value=DEFAULT_REFRESH_INTERVAL_SECONDS,
            step=0.5,
            help="Polling interval for live FastAPI telemetry",
        )

        st.divider()
        time_range_selector()
        scenario_selector()

        st.divider()
        theme = get_theme_mode()
        theme_label = "Switch to Light Mode" if theme == "dark" else "Switch to Dark Mode"
        if st.button(theme_label, key="btn_theme_toggle", use_container_width=True):
            toggle_theme_mode()
            st.rerun()

        refresh_control()

        render_html(
            f"""
            <div style="margin-top:1rem; font-size:0.68rem; color:var(--text-tertiary); text-align:center;">
                <code>{BACKEND_URL}</code><br>
                AI for IoT Capstone
            </div>
            """
        )

    return interval


def render_dashboard_page(
    analysis: Dict[str, Any],
    health: Dict[str, Any],
    is_online: bool,
    current_power: Optional[float],
    power_delta: Optional[float],
    df_filtered: pd.DataFrame,
    df_history: pd.DataFrame,
    theme: str,
) -> None:
    """
    Renders the Ultra-Minimized Live Cockpit.
    Everything visible at a glance without massive scrolling:
    1. KPI Strip (4 power metrics)
    2. Environmental Context Strip (4 sensor metrics)
    3. Appliances Ribbon (7 devices in single row)
    4. Main Split: Power Timeline Chart (62%) + AI Intelligence Card (38%)
    5. Segmented Tabs for Deep Inspection (Zero vertical scrolling).
    """
    energy = analysis.get("energy", {})
    sensors = analysis.get("sensors", {})
    appliances = analysis.get("appliances", {})
    forecast = analysis.get("forecast", {})
    ai = analysis.get("ai", {})
    waste = analysis.get("waste", {})
    severity = analysis.get("severity", "NORMAL")
    recommendation = analysis.get("recommendation", "")
    action_items = analysis.get("action_items", [])

    # 1. POWER KPI STRIP (Ultra-Compact)
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        current_power_card(current_w=current_power, delta_w=power_delta)
    with k2:
        expected_power_card(expected_w=energy.get("predicted_power_w"), current_w=current_power)
    with k3:
        forecast_power_card(forecast_w=forecast.get("predicted_next_power_w"), current_w=current_power)
    with k4:
        energy_today_card(energy_kwh=energy.get("energy_kwh"))

    # 2. ENVIRONMENTAL CONTEXT STRIP (Ultra-Compact)
    s1, s2, s3, s4 = st.columns(4)
    with s1:
        temperature_card(temp_c=sensors.get("temperature"))
    with s2:
        humidity_card(humidity_pct=sensors.get("humidity"))
    with s3:
        occupancy_card(occupancy=sensors.get("occupancy"))
    with s4:
        light_level_card(light_level=sensors.get("light_level"))

    # 3. APPLIANCES SINGLE-ROW RIBBON
    appliance_grid(
        appliances_data=appliances,
        waste_reasons=waste.get("waste_reasons"),
        total_power_w=current_power,
        selected_appliance=st.session_state.get("selected_appliance")
    )

    # 4. COCKPIT MAIN SPLIT (62% Live Chart, 38% AI Intelligence)
    c_chart, c_ai = st.columns([1.2, 0.8])
    with c_chart:
        render_html(
            f"""
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.15rem;">
                <span style="font-size:0.75rem; font-weight:700; color:var(--text-secondary); text-transform:uppercase; letter-spacing:0.03em;">
                    Real-Time Power Timeline (Live Stream)
                </span>
                <span style="font-size:0.68rem; color:var(--text-tertiary);">Interactive • Click point to investigate</span>
            </div>
            """
        )
        render_power_timeline_chart(df_filtered, selected_appliance=st.session_state.get("selected_appliance"), theme=theme)

    with c_ai:
        ai_status_card(ai_data=ai, severity=severity)
        waste_alert_card(waste_data=waste, action_items=action_items)

    # 5. APPLE SEGMENTED TABS (Zero Infinite Scrolling)
    tab1, tab2, tab3, tab4 = st.tabs([
        "Model Comparison",
        "Power Flow & Distribution",
        "Point Investigation",
        "Explainable AI"
    ])

    with tab1:
        st.caption("Actual Measured Load vs Model 1 Expected Baseline vs Model 2 Short-Term Forecast")
        render_actual_vs_expected_vs_forecast_chart(df_filtered, forecast_data=forecast, theme=theme)

    with tab2:
        col_flow, col_contrib = st.columns(2)
        with col_flow:
            st.caption("Power Influx to Active Loads (Sankey Flow)")
            render_power_flow_sankey(appliances, current_power_w=current_power, theme=theme)
        with col_contrib:
            st.caption("Instantaneous Load Attribution by Appliance")
            render_appliance_contribution_chart(appliances, theme=theme)

    with tab3:
        render_telemetry_investigation_panel(df_filtered, theme=theme)

    with tab4:
        render_ai_explanation_panel(analysis, theme=theme)


def render_analytics_page(
    analysis: Dict[str, Any],
    df_filtered: pd.DataFrame,
    df_history: pd.DataFrame,
    theme: str,
) -> None:
    """
    Renders the Consolidated Deep Analytics Page.
    Consolidates diurnal patterns, correlation curves, anomaly timeline, and load waterfall.
    """
    page_title("Advanced Analytics & Patterns", "Temporal aggregations, correlation heatmaps, and anomaly timeline")

    col1, col2 = st.columns(2)
    with col1:
        section_header("Diurnal Energy Heatmap", "Day of week × Hour load density", icon="activity")
        render_energy_pattern_heatmap(df_history, theme=theme)
    with col2:
        section_header("Appliance Load Waterfall", "Device contribution cascade", icon="zap")
        render_energy_waterfall_chart(analysis.get("appliances", {}), current_power_w=analysis.get("energy", {}).get("current_power_w", 0), theme=theme)

    col3, col4 = st.columns(2)
    with col3:
        section_header("Occupancy Correlation", "Room presence vs power draw", icon="user")
        render_occupancy_vs_power_chart(df_filtered, theme=theme)
    with col4:
        section_header("Temperature Relationship", "Thermodynamic response curve", icon="thermometer")
        render_temperature_vs_power_chart(df_filtered, theme=theme)

    section_header("Isolation Forest Anomaly Timeline", "Continuous outlier score tracking", icon="shield")
    render_anomaly_timeline_chart(df_filtered, theme=theme)


def render_system_page(health: Dict[str, Any], is_online: bool) -> None:
    """Renders the Consolidated System Architecture & Model Verification Page."""
    page_title("System Architecture & Verified Models", "FastAPI microservices, MQTT telemetry, SQLite persistence, and ML benchmarks")

    col1, col2 = st.columns(2)
    with col1:
        system_status_panel(health_data=health, is_online=is_online)
    with col2:
        model_status_panel()


def main():
    """Main application lifecycle with minimal pages and ultra-minimized layout."""
    init_session_state()
    theme = get_theme_mode()
    apply_theme_and_styles(theme)

    client = get_api_client()
    is_online, health_data = client.check_health()
    success, analysis, error_msg = client.fetch_analysis()

    raw_history = client.fetch_history(limit=500)
    df_history = normalize_history(raw_history)

    time_range = get_selected_time_range()
    df_filtered = filter_by_time_range(df_history, time_range)

    current_power = analysis.get("energy", {}).get("current_power_w")
    previous_power = get_previous_power()
    power_delta = None
    if current_power is not None and previous_power is not None:
        power_delta = float(current_power) - float(previous_power)
    if current_power is not None:
        update_previous_power(current_power)

    # Ultra-Compact Top Header
    is_live = is_live_mode()
    app_header(is_live=is_live, is_online=is_online, latency_ms=None, theme=theme)

    # Minimal Navigation Bar (Dashboard | Analytics | System)
    current_page = get_current_page()
    # Normalize legacy page names to active navbar options
    mapped_page = "Dashboard"
    if current_page in ["Analytics", "AI Insights"]:
        mapped_page = "Analytics"
    elif current_page == "System":
        mapped_page = "System"
    else:
        mapped_page = "Dashboard"

    selected_page = navigation_bar(current_page=mapped_page)
    if selected_page != current_page and selected_page in NAV_PAGES:
        set_current_page(selected_page)

    refresh_interval = render_sidebar()

    # Scenario Injection Feedback Banner
    scenario_msg = get_last_scenario_status()
    if scenario_msg:
        c_msg, c_dismiss = st.columns([6, 1])
        with c_msg:
            st.info(scenario_msg)
        with c_dismiss:
            if st.button("Dismiss", key="btn_dismiss_scenario_msg", use_container_width=True):
                set_last_scenario_status(None)
                st.rerun()

    # Paused Stream Notice
    if not is_live:
        render_html(
            f"""
            <div style="background:rgba(238, 155, 0, 0.12); border:1px solid rgba(238, 155, 0, 0.25); border-radius:8px; padding:0.25rem 0.65rem; margin-bottom:0.35rem; display:flex; align-items:center; justify-content:space-between;">
                <span style="font-size:0.72rem; color:var(--warning); font-weight:600; display:inline-flex; align-items:center; gap:0.3rem;">
                    {get_icon('pause', size=12, color='var(--warning)')} Live Streaming Paused
                </span>
                <span style="font-size:0.68rem; color:var(--text-secondary);">Display frozen for inspection</span>
            </div>
            """
        )

    if not is_online:
        error_state(
            title="FastAPI Backend Offline",
            message=f"Cannot reach {BACKEND_URL}. Ensure the backend service is running.",
        )

    # Page Routing (With full backward compatibility for legacy names)
    active = get_current_page()
    if active in ["Dashboard", "Energy", "Appliances"]:
        render_dashboard_page(
            analysis=analysis,
            health=health_data,
            is_online=is_online,
            current_power=current_power,
            power_delta=power_delta,
            df_filtered=df_filtered,
            df_history=df_history,
            theme=theme,
        )
    elif active in ["Analytics", "AI Insights"]:
        render_analytics_page(
            analysis=analysis,
            df_filtered=df_filtered,
            df_history=df_history,
            theme=theme,
        )
    elif active in ["System"]:
        render_system_page(health=health_data, is_online=is_online)
    else:
        render_dashboard_page(
            analysis=analysis,
            health=health_data,
            is_online=is_online,
            current_power=current_power,
            power_delta=power_delta,
            df_filtered=df_filtered,
            df_history=df_history,
            theme=theme,
        )

    # Live Streaming Auto-Refresh
    if is_live:
        time.sleep(refresh_interval)
        st.rerun()


if __name__ == "__main__":
    main()
