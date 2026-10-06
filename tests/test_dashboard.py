"""
Tests for Dashboard Components, API Client, Data Normalization, and State Management.
Phase 3.1 Verification Suite.
"""

import unittest
from unittest.mock import patch, MagicMock
import json

from dashboard.api_client import ApiClient, get_api_client
from dashboard.utils.formatting import (
    format_watts,
    format_kwh,
    format_temp,
    format_humidity,
    format_occupancy,
    format_lux,
    format_delta_watts,
    format_timestamp,
    get_icon,
)
from dashboard.utils.data import normalize_analysis_payload, calculate_power_breakdown
from dashboard.components.alerts import severity_badge
from dashboard.components.cards import forecast_direction_indicator
from dashboard.components.appliances import appliance_status_card, appliance_wattage_badge
from dashboard.components.status import (
    live_indicator,
    backend_connection_indicator,
    last_updated_indicator,
    data_freshness_indicator,
)
from dashboard.config import APPLIANCE_META, TIME_RANGE_OPTIONS, SCENARIO_OPTIONS


class TestDashboardFormatting(unittest.TestCase):
    """Verifies numeric, unit, and icon formatting utilities."""

    def test_format_watts(self):
        self.assertEqual(format_watts(500), ("500", "W"))
        self.assertEqual(format_watts(1500), ("1.50", "kW"))
        self.assertEqual(format_watts(0), ("0", "W"))
        self.assertEqual(format_watts(None), ("--", "W"))

    def test_format_kwh(self):
        self.assertEqual(format_kwh(1.500), ("1.500", "kWh"))
        self.assertEqual(format_kwh(0.005), ("5.0", "Wh"))
        self.assertEqual(format_kwh(None), ("--", "kWh"))

    def test_format_sensors(self):
        self.assertEqual(format_temp(24.5), "24.5 °C")
        self.assertEqual(format_temp(None), "-- °C")
        self.assertEqual(format_humidity(55.2), "55.2 %")
        self.assertEqual(format_humidity(None), "-- %")
        self.assertEqual(format_lux(450), "450 lux")
        self.assertEqual(format_lux(None), "-- lux")
        self.assertEqual(format_occupancy(1), "Occupied")
        self.assertEqual(format_occupancy(0), "Vacant")
        self.assertEqual(format_occupancy(None), "Unknown")

    def test_format_delta_watts(self):
        self.assertEqual(format_delta_watts(75.0), ("+75 W", "up"))
        self.assertEqual(format_delta_watts(-120.0), ("-120 W", "down"))
        self.assertEqual(format_delta_watts(1250.0), ("+1.25 kW", "up"))
        self.assertEqual(format_delta_watts(0.0), ("0 W", "flat"))
        self.assertEqual(format_delta_watts(None), ("0 W", "flat"))

    def test_get_icon(self):
        svg = get_icon("zap", size=24, color="#FF0000")
        self.assertIn("<svg", svg)
        self.assertIn('width="24"', svg)
        self.assertIn('stroke="#FF0000"', svg)

        # Fallback icon
        fallback_svg = get_icon("non_existent_icon")
        self.assertIn("<svg", fallback_svg)


class TestDataNormalization(unittest.TestCase):
    """Verifies that API payloads with missing/null fields are normalized safely."""

    def test_normalize_empty_payload(self):
        normalized = normalize_analysis_payload({})
        self.assertIn("timestamp", normalized)
        self.assertIn("energy", normalized)
        self.assertIn("sensors", normalized)
        self.assertIn("appliances", normalized)
        self.assertIn("forecast", normalized)
        self.assertIn("ai", normalized)
        self.assertIn("waste", normalized)
        self.assertIn("recommendation", normalized)
        self.assertIn("action_items", normalized)
        self.assertEqual(normalized["severity"], "NORMAL")
        self.assertEqual(normalized["energy"]["current_power_w"], 0)
        self.assertEqual(normalized["sensors"]["temperature"], 24.0)

    def test_normalize_valid_payload(self):
        raw = {
            "timestamp": "2026-10-04T12:00:00Z",
            "energy": {"current_power_w": 1650, "energy_kwh": 0.45},
            "sensors": {"temperature": 27.5, "humidity": 60.0, "occupancy": 1, "light_level": 700},
            "appliances": {"ac": 1, "fan": 0, "tv": 0, "room_light": 1, "refrigerator": 1, "heater": 0, "microwave": 0},
            "forecast": {"predicted_next_power_w": 1720.0},
            "ai": {"is_anomaly": False, "anomaly_score": 0.12},
            "waste": {"is_wasteful": False, "wasted_power_w": 0.0},
            "severity": "NORMAL",
            "recommendation": "Optimal consumption",
            "action_items": [],
        }
        normalized = normalize_analysis_payload(raw)
        self.assertEqual(normalized["energy"]["current_power_w"], 1650)
        self.assertEqual(normalized["sensors"]["temperature"], 27.5)
        self.assertEqual(normalized["appliances"]["ac"], 1)
        self.assertEqual(normalized["forecast"]["predicted_next_power_w"], 1720.0)

    def test_calculate_power_breakdown(self):
        appliances = {"ac": 1, "room_light": 1, "heater": 0}
        breakdown = calculate_power_breakdown(appliances)
        self.assertEqual(breakdown["ac"]["power_w"], 1500)
        self.assertEqual(breakdown["room_light"]["power_w"], 20)
        self.assertEqual(breakdown["heater"]["power_w"], 0)


class TestApiClientResilience(unittest.TestCase):
    """Verifies that ApiClient never crashes when backend is down or returns errors."""

    @patch("requests.get")
    def test_check_health_offline(self, mock_get):
        import requests
        mock_get.side_effect = requests.exceptions.ConnectionError("Connection refused")
        
        client = ApiClient(base_url="http://localhost:8000", timeout=1.0)
        is_online, health = client.check_health()
        
        self.assertFalse(is_online)
        self.assertEqual(health["status"], "offline")
        self.assertIn("Connection refused", client.last_error)

    @patch("requests.get")
    def test_check_health_success(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "status": "ok",
            "mqtt_connected": True,
            "models_loaded": True,
            "total_telemetry_records": 7200,
            "uptime_seconds": 120.5,
        }
        mock_get.return_value = mock_resp

        client = ApiClient(base_url="http://localhost:8000")
        is_online, health = client.check_health()
        
        self.assertTrue(is_online)
        self.assertEqual(health["status"], "ok")
        self.assertTrue(health["mqtt_connected"])

    @patch("requests.get")
    def test_fetch_analysis_offline(self, mock_get):
        import requests
        mock_get.side_effect = requests.exceptions.Timeout("Timed out")

        client = ApiClient(base_url="http://localhost:8000")
        success, payload, err = client.fetch_analysis()

        self.assertFalse(success)
        self.assertIsNotNone(err)
        # Verify it still returns a normalized dictionary rather than None or crashing
        self.assertIn("energy", payload)
        self.assertIn("sensors", payload)

    @patch("requests.get")
    def test_fetch_analysis_success(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "energy": {"current_power_w": 250},
            "sensors": {"temperature": 23.0},
            "severity": "NORMAL",
        }
        mock_get.return_value = mock_resp

        client = ApiClient()
        success, payload, err = client.fetch_analysis()

        self.assertTrue(success)
        self.assertIsNone(err)
        self.assertEqual(payload["energy"]["current_power_w"], 250)


class TestComponentMarkup(unittest.TestCase):
    """Verifies that reusable UI components render accurate, semantic markup."""

    def test_severity_badge_classes(self):
        self.assertIn("severity-badge normal", severity_badge("NORMAL"))
        self.assertIn("severity-badge warning", severity_badge("WARNING"))
        self.assertIn("severity-badge high", severity_badge("HIGH"))
        self.assertIn("severity-badge critical", severity_badge("CRITICAL"))

    def test_forecast_direction(self):
        up_html = forecast_direction_indicator(current_w=1000, forecast_w=1200)
        self.assertIn("Rising", up_html)
        
        down_html = forecast_direction_indicator(current_w=1200, forecast_w=1000)
        self.assertIn("Easing", down_html)

        flat_html = forecast_direction_indicator(current_w=1000, forecast_w=1005)
        self.assertIn("Steady", flat_html)

    def test_appliance_card_markup(self):
        card_html = appliance_status_card(
            appliance_key="ac",
            name="Air Conditioner",
            is_on=True,
            rated_watts=1500,
            current_watts=1500,
            is_selected=True,
        )
        self.assertIn("appliance-card active selected", card_html)
        self.assertIn("Air Conditioner", card_html)
        self.assertIn("1500W", card_html)
        self.assertIn("ON", card_html)

    def test_status_indicators(self):
        live_html = live_indicator(is_live=True)
        self.assertIn("LIVE", live_html)
        self.assertIn("live-dot", live_html)

        paused_html = live_indicator(is_live=False)
        self.assertIn("PAUSED", paused_html)

        conn_online = backend_connection_indicator(is_online=True)
        self.assertIn("API ONLINE", conn_online)

        conn_offline = backend_connection_indicator(is_online=False)
        self.assertIn("API OFFLINE", conn_offline)


class TestDashboardStateManagement(unittest.TestCase):
    """Verifies that session state functions handle time range, appliances, live/pause, and theme properly."""

    def setUp(self):
        import streamlit as st
        # Clear mock session state for each test
        for k in list(st.session_state.keys()):
            del st.session_state[k]

    def test_state_initialization(self):
        from dashboard.state import (
            init_session_state,
            get_current_page,
            get_selected_appliance,
            get_selected_time_range,
            is_live_mode,
            get_selected_scenario,
            get_theme_mode,
        )
        init_session_state()
        self.assertEqual(get_current_page(), "Dashboard")
        self.assertEqual(get_selected_appliance(), "All Appliances")
        self.assertEqual(get_selected_time_range(), "5 minutes")
        self.assertTrue(is_live_mode())
        self.assertEqual(get_selected_scenario(), "LIVE TELEMETRY")
        self.assertIn(get_theme_mode(), ["light", "dark"])

    def test_state_transitions(self):
        from dashboard.state import (
            init_session_state,
            set_selected_appliance,
            get_selected_appliance,
            set_selected_time_range,
            get_selected_time_range,
            set_live_mode,
            is_live_mode,
            toggle_live_mode,
            set_selected_scenario,
            get_selected_scenario,
            toggle_theme_mode,
            get_theme_mode,
        )
        init_session_state()

        # Appliance selection
        set_selected_appliance("Air Conditioner")
        self.assertEqual(get_selected_appliance(), "Air Conditioner")

        # Time range selection
        set_selected_time_range("1 hour")
        self.assertEqual(get_selected_time_range(), "1 hour")
        self.assertIn(get_selected_time_range(), TIME_RANGE_OPTIONS)

        # Live / Pause mode
        set_live_mode(False)
        self.assertFalse(is_live_mode())
        toggle_live_mode()
        self.assertTrue(is_live_mode())

        # Scenario selection
        set_selected_scenario("WASTEFUL")
        self.assertEqual(get_selected_scenario(), "WASTEFUL")
        self.assertIn(get_selected_scenario(), SCENARIO_OPTIONS)

        # Theme toggle
        current_theme = get_theme_mode()
        toggle_theme_mode()
        self.assertNotEqual(get_theme_mode(), current_theme)


class TestDashboardAppLifecycle(unittest.TestCase):
    """Verifies that the complete Streamlit dashboard app renders without exceptions."""

    def test_app_pages_lifecycle(self):
        from streamlit.testing.v1 import AppTest
        for page in ["Dashboard", "Energy", "AI Insights", "Appliances", "Analytics", "System"]:
            at = AppTest.from_file("dashboard/app.py")
            at.session_state["is_live"] = False
            at.session_state["active_page"] = page
            at.session_state["current_page"] = page
            at.run()
            self.assertEqual(len(at.exception), 0, f"Exception on page {page}: {at.exception}")


if __name__ == "__main__":
    unittest.main()


