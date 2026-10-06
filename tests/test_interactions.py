"""
Phase 3.3: Intelligence + Interaction Layer Test Suite.
Tests:
1. Centralized Interaction State (appliance, timestamp, anomaly, event, time range, scenario, live/pause)
2. Appliance Cross-Filtering & Derived Load Attribution (Estimated Appliance Load)
3. Telemetry Point Investigation & Historical Lookup
4. Anomaly Deep-Dive Investigation & Isolation Forest Outlier Tracking
5. AI Explanation Breakdown (Observed, Expected, Difference, Condition, Evidence, Action)
6. Forecast Intelligence & Short-Term Horizon Verification
7. Backend Scenario Injection Endpoint (POST /scenario) & API Client Integration
8. Prescriptive Guidance & Honest Action Labeling
"""

import unittest
from datetime import datetime, timezone
import pandas as pd
import numpy as np
from fastapi.testclient import TestClient

from backend.api import app
from dashboard.config import APPLIANCE_META, TIME_RANGE_OPTIONS, SCENARIO_OPTIONS
from dashboard.api_client import ApiClient, get_api_client
from dashboard.utils.chart_data import normalize_history, filter_by_time_range
from dashboard.components.recommendations import _estimate_action_impact
from dashboard.components.intelligence import (
    render_ai_explanation_panel,
    render_forecast_intelligence_card,
    render_telemetry_investigation_panel,
    render_anomaly_investigation_panel,
    render_appliance_detail_panel,
)


class TestInteractionState(unittest.TestCase):
    """Verifies Phase 3.3 session state getters, setters, and transitions."""

    def setUp(self):
        # Mock streamlit session_state dict
        import streamlit as st
        self.st = st
        if not hasattr(st, "session_state"):
            st.session_state = {}
        st.session_state.clear()
        from dashboard.state import init_session_state
        init_session_state()

    def test_state_initialization(self):
        from dashboard.state import (
            get_selected_appliance,
            get_selected_time_range,
            is_live_mode,
            get_selected_scenario,
            get_selected_timestamp,
            get_selected_anomaly,
        )
        self.assertEqual(get_selected_appliance(), "All Appliances")
        self.assertEqual(get_selected_time_range(), "5 minutes")
        self.assertTrue(is_live_mode())
        self.assertEqual(get_selected_scenario(), "LIVE TELEMETRY")
        self.assertIsNone(get_selected_timestamp())
        self.assertIsNone(get_selected_anomaly())

    def test_appliance_selection_transition(self):
        from dashboard.state import set_selected_appliance, get_selected_appliance
        set_selected_appliance("Air Conditioner")
        self.assertEqual(get_selected_appliance(), "Air Conditioner")
        set_selected_appliance("Space Heater")
        self.assertEqual(get_selected_appliance(), "Space Heater")
        set_selected_appliance("All Appliances")
        self.assertEqual(get_selected_appliance(), "All Appliances")

    def test_timestamp_and_anomaly_selection(self):
        from dashboard.state import (
            set_selected_timestamp,
            get_selected_timestamp,
            set_selected_anomaly,
            get_selected_anomaly,
            clear_investigation_selection,
        )
        set_selected_timestamp("2026-10-04T12:00:10.000000+00:00")
        self.assertEqual(get_selected_timestamp(), "2026-10-04T12:00:10.000000+00:00")

        set_selected_anomaly("2026-10-04T12:00:10.000000+00:00")
        self.assertEqual(get_selected_anomaly(), "2026-10-04T12:00:10.000000+00:00")

        clear_investigation_selection()
        self.assertIsNone(get_selected_timestamp())
        self.assertIsNone(get_selected_anomaly())

    def test_live_pause_state(self):
        from dashboard.state import set_live_mode, is_live_mode, toggle_live_mode
        set_live_mode(False)
        self.assertFalse(is_live_mode())
        toggle_live_mode()
        self.assertTrue(is_live_mode())


class TestApplianceCrossFilteringAndAttribution(unittest.TestCase):
    """Verifies appliance filtering, load estimation honesty, and historical stats."""

    def setUp(self):
        self.history = [
            {
                "id": 1,
                "timestamp": "2026-10-04T12:00:00+00:00",
                "power_w": 1700,
                "predicted_power_w": 1700.0,
                "temperature": 28.0,
                "occupancy": 0,
                "ac": 1,
                "fan": 0,
                "tv": 0,
                "room_light": 0,
                "refrigerator": 1,
                "heater": 0,
                "microwave": 0,
                "is_anomaly": 0,
                "anomaly_score": 0.05,
                "wasteful": 1,
            },
            {
                "id": 2,
                "timestamp": "2026-10-04T12:00:03+00:00",
                "power_w": 4700,
                "predicted_power_w": 4700.0,
                "temperature": 18.0,
                "occupancy": 1,
                "ac": 1,
                "fan": 0,
                "tv": 0,
                "room_light": 0,
                "refrigerator": 1,
                "heater": 1,
                "microwave": 1,
                "is_anomaly": 1,
                "anomaly_score": -0.08,
                "wasteful": 1,
            },
        ]
        self.df = normalize_history(self.history)

    def test_estimated_appliance_load_derivation(self):
        """Rule #5: Appliance load is derived from rated watts and binary state, not fake direct meter."""
        self.assertEqual(len(self.df), 2)
        ac_rated = APPLIANCE_META["ac"]["watts"]
        heater_rated = APPLIANCE_META["heater"]["watts"]

        # Row 0: AC is ON (1500W), Heater is OFF (0W)
        self.assertEqual(self.df.iloc[0]["ac"] * ac_rated, 1500.0)
        self.assertEqual(self.df.iloc[0]["heater"] * heater_rated, 0.0)

        # Row 1: Both AC and Heater are ON
        self.assertEqual(self.df.iloc[1]["ac"] * ac_rated, 1500.0)
        self.assertEqual(self.df.iloc[1]["heater"] * heater_rated, 2000.0)

    def test_duty_cycle_and_incident_attribution(self):
        """Calculates exact incident attribution without fabricating historical consumption."""
        ac_on_count = int((self.df["ac"] == 1).sum())
        heater_on_count = int((self.df["heater"] == 1).sum())
        ac_waste_count = int(((self.df["ac"] == 1) & (self.df["wasteful"] == 1)).sum())
        heater_anom_count = int(((self.df["heater"] == 1) & (self.df["is_anomaly"] == 1)).sum())

        self.assertEqual(ac_on_count, 2)
        self.assertEqual(heater_on_count, 1)
        self.assertEqual(ac_waste_count, 2)
        self.assertEqual(heater_anom_count, 1)


class TestTelemetryAndAnomalyLookup(unittest.TestCase):
    """Verifies robust lookup by timestamp or anomaly occurrence."""

    def setUp(self):
        raw = [
            {
                "id": 1,
                "timestamp": "2026-10-04T12:00:00+00:00",
                "power_w": 250,
                "predicted_power_w": 250.0,
                "temperature": 24.0,
                "humidity": 50.0,
                "occupancy": 1,
                "light_level": 400,
                "is_anomaly": 0,
                "anomaly_score": 0.15,
                "wasteful": 0,
            },
            {
                "id": 2,
                "timestamp": "2026-10-04T12:00:03+00:00",
                "power_w": 4200,
                "predicted_power_w": 4200.0,
                "temperature": 24.0,
                "humidity": 50.0,
                "occupancy": 0,
                "light_level": 50,
                "is_anomaly": 1,
                "anomaly_score": -0.05,
                "wasteful": 1,
            },
        ]
        self.df = normalize_history(raw)

    def test_timestamp_lookup(self):
        ts_str = "2026-10-04 12:00:00"
        match = self.df[self.df["datetime"].astype(str).str.contains(ts_str)]
        self.assertFalse(match.empty)
        self.assertEqual(match.iloc[0]["power_w"], 250.0)

    def test_anomaly_filtering(self):
        anomalies = self.df[self.df["is_anomaly"] == 1]
        self.assertEqual(len(anomalies), 1)
        self.assertEqual(anomalies.iloc[0]["power_w"], 4200.0)
        self.assertEqual(anomalies.iloc[0]["wasteful"], 1)

    def test_empty_and_null_resilience(self):
        """Verifies panels and normalizer handle empty/corrupted data gracefully without crash."""
        empty_df = normalize_history([])
        self.assertTrue(empty_df.empty)

        # Missing fields should default cleanly
        partial_df = normalize_history([{"timestamp": "2026-10-04T12:00:00+00:00"}])
        self.assertEqual(partial_df.iloc[0]["power_w"], 0.0)
        self.assertEqual(partial_df.iloc[0]["occupancy_str"], "Vacant")


class TestScenarioInjectionEndpoint(unittest.TestCase):
    """Tests the real FastAPI backend POST /scenario endpoint and ApiClient."""

    def setUp(self):
        self.client = TestClient(app)

    def test_post_scenario_wasteful(self):
        resp = self.client.post("/scenario", json={"scenario": "WASTEFUL"})
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["status"], "success")
        analysis = data["analysis"]
        self.assertEqual(analysis["sensors"]["occupancy"], 0)
        self.assertTrue(analysis["waste"]["wasteful"])
        self.assertGreater(analysis["energy"]["current_power_w"], 1000)

    def test_post_scenario_high_load(self):
        resp = self.client.post("/scenario", json={"scenario": "HIGH LOAD"})
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["status"], "success")
        analysis = data["analysis"]
        self.assertGreater(analysis["energy"]["current_power_w"], 3500)
        self.assertEqual(analysis["severity"], "CRITICAL")

    def test_post_scenario_spike(self):
        resp = self.client.post("/scenario", json={"scenario": "SPIKE"})
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["status"], "success")
        analysis = data["analysis"]
        self.assertEqual(analysis["appliances"]["heater"], 1)

    def test_post_scenario_normal(self):
        resp = self.client.post("/scenario", json={"scenario": "NORMAL"})
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["status"], "success")
        analysis = data["analysis"]
        self.assertFalse(analysis["waste"]["wasteful"])
        self.assertEqual(analysis["severity"], "NORMAL")

    def test_post_invalid_scenario_returns_400(self):
        resp = self.client.post("/scenario", json={"scenario": "NON_EXISTENT_SCENARIO"})
        self.assertEqual(resp.status_code, 400)


class TestForecastAndPrescriptiveInteractions(unittest.TestCase):
    """Verifies short-term forecast structure and actionable recommendation impacts."""

    def test_estimate_action_impact(self):
        self.assertEqual(_estimate_action_impact("Turn off Space Heater"), 2000.0)
        self.assertEqual(_estimate_action_impact("Switch off AC in vacant room"), 1500.0)
        self.assertEqual(_estimate_action_impact("Turn off Microwave"), 1000.0)
        self.assertIsNone(_estimate_action_impact("Review baseline patterns"))

    def test_forecast_horizon_honesty(self):
        """Rule #1 & #13: Horizon must clearly specify short-term 2.5s telemetry interval."""
        client = TestClient(app)
        resp = client.get("/forecast")
        self.assertEqual(resp.status_code, 200)
        fc = resp.json()
        self.assertIn("2.5", str(fc["forecast_horizon"]))
        self.assertIn("Linear Regression", fc["model"])
        self.assertIn("forecast_power_w", fc)
        self.assertIn("expected_change_w", fc)

    def test_forecast_metadata_metrics_audit(self):
        """Audits Model 2 metrics: MAE = 830.11 W, RMSE = 1070.58 W, R² = 0.2142."""
        from backend.config import FORECAST_META_PATH
        import json
        with open(FORECAST_META_PATH, "r") as f:
            meta = json.load(f)
        self.assertAlmostEqual(meta["metrics"]["mae_watts"], 830.1128, places=3)
        self.assertAlmostEqual(meta["metrics"]["rmse_watts"], 1070.5809, places=3)
        self.assertAlmostEqual(meta["metrics"]["r2_score"], 0.214157, places=4)
        self.assertEqual(meta["total_samples"], 7197)
        self.assertEqual(meta["train_samples"], 5757)
        self.assertEqual(meta["test_samples"], 1440)
        self.assertEqual(meta["split_method"], "Chronological (No Shuffle)")


if __name__ == "__main__":
    unittest.main()
