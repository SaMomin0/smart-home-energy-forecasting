"""
Streamlit Session State Management.
Centralizes UI state, time-range filters, appliance selections, live/paused mode,
active navigation page, and theme switching.
"""

from typing import Dict, Any, Optional
import streamlit as st

from dashboard.config import (
    NAV_PAGES,
    TIME_RANGE_OPTIONS,
    SCENARIO_OPTIONS,
    APPLIANCE_FILTER_OPTIONS,
)


def init_session_state():
    """Initializes all default session state variables if not already defined."""
    if "active_page" not in st.session_state:
        st.session_state["active_page"] = NAV_PAGES[0]  # "Dashboard"
    if "current_page" not in st.session_state:
        st.session_state["current_page"] = st.session_state["active_page"]

    if "selected_appliance" not in st.session_state:
        st.session_state["selected_appliance"] = APPLIANCE_FILTER_OPTIONS[0] # "All Appliances"

    if "selected_time_range" not in st.session_state:
        st.session_state["selected_time_range"] = "5 minutes"

    if "is_live" not in st.session_state:
        st.session_state["is_live"] = True

    if "selected_scenario" not in st.session_state:
        st.session_state["selected_scenario"] = SCENARIO_OPTIONS[0] # "LIVE TELEMETRY"

    if "theme_mode" not in st.session_state:
        st.session_state["theme_mode"] = "dark" # Default dark mode for Apple-inspired aesthetic

    if "last_analysis" not in st.session_state:
        st.session_state["last_analysis"] = None

    if "last_health" not in st.session_state:
        st.session_state["last_health"] = None

    if "previous_power" not in st.session_state:
        st.session_state["previous_power"] = None

    if "refresh_counter" not in st.session_state:
        st.session_state["refresh_counter"] = 0

    # Phase 3.3 Centralized Interaction State
    if "selected_timestamp" not in st.session_state:
        st.session_state["selected_timestamp"] = None

    if "selected_anomaly" not in st.session_state:
        st.session_state["selected_anomaly"] = None

    if "selected_event" not in st.session_state:
        st.session_state["selected_event"] = None

    if "last_scenario_status" not in st.session_state:
        st.session_state["last_scenario_status"] = None


# --- Getters & Setters ---

def get_current_page() -> str:
    return st.session_state.get("active_page") or st.session_state.get("current_page", "Dashboard")


def set_current_page(page: str):
    st.session_state["active_page"] = page
    st.session_state["current_page"] = page


def get_selected_appliance() -> str:
    return st.session_state.get("selected_appliance", "All Appliances")


def set_selected_appliance(appliance_name: str):
    st.session_state["selected_appliance"] = appliance_name


def get_selected_time_range() -> str:
    return st.session_state.get("selected_time_range", "5 minutes")


def set_selected_time_range(time_range: str):
    st.session_state["selected_time_range"] = time_range


def is_live_mode() -> bool:
    return bool(st.session_state.get("is_live", True))


def set_live_mode(live: bool):
    st.session_state["is_live"] = live


def toggle_live_mode():
    st.session_state["is_live"] = not is_live_mode()


def get_selected_scenario() -> str:
    return st.session_state.get("selected_scenario", "LIVE TELEMETRY")


def set_selected_scenario(scenario: str):
    st.session_state["selected_scenario"] = scenario


def get_theme_mode() -> str:
    return st.session_state.get("theme_mode", "dark")


def toggle_theme_mode():
    current = get_theme_mode()
    st.session_state["theme_mode"] = "light" if current == "dark" else "dark"


def get_last_analysis() -> Optional[Dict[str, Any]]:
    return st.session_state.get("last_analysis")


def set_last_analysis(analysis: Dict[str, Any]):
    current_power = analysis.get("energy", {}).get("current_power_w")
    prev = st.session_state.get("previous_power")
    if current_power is not None and prev is None:
        st.session_state["previous_power"] = current_power
    st.session_state["last_analysis"] = analysis


def get_previous_power() -> Optional[int]:
    return st.session_state.get("previous_power")


def update_previous_power(power: int):
    st.session_state["previous_power"] = power


def get_selected_timestamp() -> Optional[str]:
    return st.session_state.get("selected_timestamp")


def set_selected_timestamp(timestamp: Optional[str]):
    st.session_state["selected_timestamp"] = timestamp


def get_selected_anomaly() -> Optional[Any]:
    return st.session_state.get("selected_anomaly")


def set_selected_anomaly(anomaly: Optional[Any]):
    st.session_state["selected_anomaly"] = anomaly


def get_selected_event() -> Optional[Dict[str, Any]]:
    return st.session_state.get("selected_event")


def set_selected_event(event: Optional[Dict[str, Any]]):
    st.session_state["selected_event"] = event


def get_last_scenario_status() -> Optional[str]:
    return st.session_state.get("last_scenario_status")


def set_last_scenario_status(status: Optional[str]):
    st.session_state["last_scenario_status"] = status


def clear_investigation_selection():
    st.session_state["selected_timestamp"] = None
    st.session_state["selected_anomaly"] = None
    st.session_state["selected_event"] = None
