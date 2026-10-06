"""
Interactive Control Components.
Includes Time Range Selector, Live/Pause Control, Refresh Control, and Scenario Selector.
Manages session state architecture for telemetry streaming and future Phase 3.2 filtering.
"""

from typing import Optional
import streamlit as st

from dashboard.config import TIME_RANGE_OPTIONS, SCENARIO_OPTIONS
from dashboard.utils.formatting import get_icon


def time_range_selector() -> str:
    """
    Renders the Time Range Selector.
    Stores 'selected_time_range' in Streamlit session state.
    """
    current_val = st.session_state.get("selected_time_range", "5 minutes")
    try:
        current_idx = TIME_RANGE_OPTIONS.index(current_val)
    except ValueError:
        current_idx = 2

    chosen = st.selectbox(
        "Time Horizon",
        options=TIME_RANGE_OPTIONS,
        index=current_idx,
        help="Controls the historical aggregation window for analytics",
        key="time_range_select",
    )
    if chosen != current_val:
        st.session_state.selected_time_range = chosen
    return chosen


def live_pause_control() -> bool:
    """
    Renders the Live / Pause streaming toggle.
    Stores 'is_live' boolean in Streamlit session state.
    """
    is_live = st.session_state.get("is_live", True)
    
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("Live", key="ctrl_live_btn", type="primary" if is_live else "secondary", use_container_width=True):
            st.session_state.is_live = True
            st.rerun()
    with col2:
        if st.button("Pause", key="ctrl_pause_btn", type="secondary" if is_live else "primary", use_container_width=True):
            st.session_state.is_live = False
            st.rerun()
            
    return st.session_state.get("is_live", True)


def refresh_control() -> None:
    """
    Renders a manual refresh trigger button.
    Forces an immediate state re-evaluation.
    """
    if st.button("Refresh Telemetry", key="ctrl_refresh_btn", use_container_width=True):
        st.rerun()


def scenario_selector() -> str:
    """
    Renders the Simulation Scenario Selector.
    Options: LIVE TELEMETRY, NORMAL, WASTEFUL, HIGH LOAD, SPIKE.
    When a scenario is selected, routes the canonical telemetry through POST /scenario
    into the real backend pipeline (ML models + rules + SQLite database).
    """
    from dashboard.api_client import get_api_client
    from dashboard.state import set_last_scenario_status

    current_scenario = st.session_state.get("selected_scenario", "LIVE TELEMETRY")
    try:
        current_idx = SCENARIO_OPTIONS.index(current_scenario)
    except ValueError:
        current_idx = 0

    chosen = st.selectbox(
        "Simulation Mode",
        options=SCENARIO_OPTIONS,
        index=current_idx,
        help="Injects canonical testing scenarios into the live ML and rule pipeline",
        key="scenario_select",
    )
    if chosen != current_scenario:
        client = get_api_client()
        success, resp, err = client.trigger_scenario(chosen)
        st.session_state.selected_scenario = chosen
        if success:
            set_last_scenario_status(f"Scenario '{chosen}' successfully processed by AI pipeline.")
        else:
            set_last_scenario_status(f"Failed to inject scenario '{chosen}': {err}")
        st.rerun()

    return chosen
