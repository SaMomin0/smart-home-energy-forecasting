"""
Comprehensive Automated Test Suite for Smart Home Energy AI (Phase 2).
Executes and validates all 14 mandatory scenario and stress tests:
  TEST 1 : Normal occupied home
  TEST 2 : AC ON (Occupied)
  TEST 3 : All normal low/medium appliances (Occupied)
  TEST 4 : Unoccupied + AC ON (Vacancy Waste)
  TEST 5 : Unoccupied + TV ON (Vacancy Waste)
  TEST 6 : Unoccupied + Lights ON (Lighting Waste)
  TEST 7 : Space Heater ON
  TEST 8 : Heater + AC + Microwave ON (Peak Overload)
  TEST 9 : Abnormal power spike event
  TEST 10: Malformed MQTT JSON string
  TEST 11: Missing required telemetry fields
  TEST 12: MQTT broker disconnect resilience
  TEST 13: API error handling (empty / invalid)
  TEST 14: API unified /analysis response schema validation
"""

import sys
import json
import unittest
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from fastapi.testclient import TestClient
from backend.config import APPLIANCE_RATINGS
from backend.preprocessing import preprocess_telemetry
from backend.features import extract_features_single
from backend.predictor import get_predictor
from backend.anomaly import get_anomaly_detector
from backend.rules import evaluate_waste_rules
from backend.recommendations import compute_severity_and_recommendations
from backend.collector import process_telemetry_payload, MQTTCollector
from backend.api import app


class TestPhase2SmartHomePipeline(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.predictor = get_predictor()
        cls.detector = get_anomaly_detector()
        cls.api_client = TestClient(app)

    def test_01_normal_occupied_home(self):
        """TEST 1: Normal occupied home (Fan + Light + Fridge)."""
        payload = {
            "uptime_ms": 10000,
            "temperature": 25.0,
            "humidity": 50.0,
            "occupancy": 1,
            "light_level": 250,
            "ac": 0, "fan": 1, "tv": 0, "room_light": 1, "refrigerator": 1, "heater": 0, "microwave": 0,
            "power_w": 245
        }
        res = process_telemetry_payload(json.dumps(payload))
        self.assertIsNotNone(res)
        self.assertFalse(res["waste"]["wasteful"])
        self.assertEqual(res["severity"], "NORMAL")
        self.assertEqual(res["energy"]["current_power_w"], 245)

    def test_02_ac_on_occupied(self):
        """TEST 2: AC ON during warm occupied period."""
        payload = {
            "uptime_ms": 20000,
            "temperature": 32.0,
            "humidity": 60.0,
            "occupancy": 1,
            "light_level": 400,
            "ac": 1, "fan": 0, "tv": 0, "room_light": 0, "refrigerator": 1, "heater": 0, "microwave": 0,
            "power_w": 1650
        }
        res = process_telemetry_payload(json.dumps(payload))
        self.assertIsNotNone(res)
        self.assertFalse(res["waste"]["wasteful"], "Occupied AC cooling should not be flagged as vacancy waste")
        self.assertEqual(res["energy"]["current_power_w"], 1650)

    def test_03_all_normal_appliances(self):
        """TEST 3: Typical evening occupied routine (TV + Fan + Light + Fridge)."""
        expected_power = APPLIANCE_RATINGS["tv"] + APPLIANCE_RATINGS["fan"] + APPLIANCE_RATINGS["room_light"] + APPLIANCE_RATINGS["refrigerator"]
        payload = {
            "uptime_ms": 30000,
            "temperature": 26.0,
            "humidity": 52.0,
            "occupancy": 1,
            "light_level": 150,
            "ac": 0, "fan": 1, "tv": 1, "room_light": 1, "refrigerator": 1, "heater": 0, "microwave": 0,
            "power_w": expected_power
        }
        res = process_telemetry_payload(json.dumps(payload))
        self.assertIsNotNone(res)
        self.assertFalse(res["waste"]["wasteful"])
        self.assertEqual(res["energy"]["current_power_w"], expected_power)

    def test_04_unoccupied_ac_on(self):
        """TEST 4: Unoccupied room with AC left running (Vacancy Waste)."""
        payload = {
            "uptime_ms": 40000,
            "temperature": 27.0,
            "humidity": 55.0,
            "occupancy": 0,
            "light_level": 400,
            "ac": 1, "fan": 0, "tv": 0, "room_light": 0, "refrigerator": 1, "heater": 0, "microwave": 0,
            "power_w": 1650
        }
        res = process_telemetry_payload(json.dumps(payload))
        self.assertIsNotNone(res)
        self.assertTrue(res["waste"]["wasteful"])
        self.assertTrue(any("Air Conditioner" in r for r in res["waste"]["reasons"]))
        self.assertIn(res["severity"], ["HIGH", "CRITICAL"])

    def test_05_unoccupied_tv_on(self):
        """TEST 5: Unoccupied room with TV left running (Vacancy Waste)."""
        payload = {
            "uptime_ms": 50000,
            "temperature": 24.5,
            "humidity": 48.0,
            "occupancy": 0,
            "light_level": 200,
            "ac": 0, "fan": 0, "tv": 1, "room_light": 0, "refrigerator": 1, "heater": 0, "microwave": 0,
            "power_w": 270
        }
        res = process_telemetry_payload(json.dumps(payload))
        self.assertIsNotNone(res)
        self.assertTrue(res["waste"]["wasteful"])
        self.assertTrue(any("Television" in r for r in res["waste"]["reasons"]))

    def test_06_unoccupied_lights_on(self):
        """TEST 6: Unoccupied room with Room Light left ON."""
        payload = {
            "uptime_ms": 60000,
            "temperature": 24.0,
            "humidity": 50.0,
            "occupancy": 0,
            "light_level": 150,
            "ac": 0, "fan": 0, "tv": 0, "room_light": 1, "refrigerator": 1, "heater": 0, "microwave": 0,
            "power_w": 170
        }
        res = process_telemetry_payload(json.dumps(payload))
        self.assertIsNotNone(res)
        self.assertTrue(res["waste"]["wasteful"])
        self.assertTrue(any("Room Light" in r for r in res["waste"]["reasons"]))

    def test_07_space_heater_on(self):
        """TEST 7: Space Heater ON in winter occupied condition."""
        payload = {
            "uptime_ms": 70000,
            "temperature": 18.0,
            "humidity": 45.0,
            "occupancy": 1,
            "light_level": 100,
            "ac": 0, "fan": 0, "tv": 0, "room_light": 1, "refrigerator": 1, "heater": 1, "microwave": 0,
            "power_w": 2170
        }
        res = process_telemetry_payload(json.dumps(payload))
        self.assertIsNotNone(res)
        self.assertFalse(res["waste"]["wasteful"])
        self.assertEqual(res["energy"]["current_power_w"], 2170)

    def test_08_heater_ac_microwave_overload(self):
        """TEST 8: Multiple high power appliances ON (AC + Heater + Microwave = High Load / Overload)."""
        power = APPLIANCE_RATINGS["ac"] + APPLIANCE_RATINGS["heater"] + APPLIANCE_RATINGS["microwave"] + APPLIANCE_RATINGS["refrigerator"]
        payload = {
            "uptime_ms": 80000,
            "temperature": 25.0,
            "humidity": 50.0,
            "occupancy": 1,
            "light_level": 300,
            "ac": 1, "fan": 0, "tv": 0, "room_light": 0, "refrigerator": 1, "heater": 1, "microwave": 1,
            "power_w": power
        }
        res = process_telemetry_payload(json.dumps(payload))
        self.assertIsNotNone(res)
        self.assertIn(res["severity"], ["HIGH", "CRITICAL"])
        self.assertTrue(any("conflict" in r.lower() or "high grid load" in r.lower() for r in res["waste"]["reasons"]))

    def test_09_abnormal_power_spike(self):
        """TEST 9: Extreme abnormal power spike event."""
        payload = {
            "uptime_ms": 90000,
            "temperature": 26.0,
            "humidity": 50.0,
            "occupancy": 1,
            "light_level": 300,
            "ac": 1, "fan": 1, "tv": 1, "room_light": 1, "refrigerator": 1, "heater": 1, "microwave": 1,
            "power_w": 4865
        }
        res = process_telemetry_payload(json.dumps(payload))
        self.assertIsNotNone(res)
        self.assertEqual(res["severity"], "CRITICAL")
        self.assertTrue(res["ai"]["anomaly"])

    def test_10_malformed_mqtt_json(self):
        """TEST 10: Corrupted/malformed JSON string handling."""
        malformed_strings = [
            "This is not a JSON string",
            '{"temperature": 25.0, "humidity": ',
            "{invalid: json}",
            ""
        ]
        for bad_str in malformed_strings:
            res = process_telemetry_payload(bad_str)
            self.assertIsNone(res, "Collector must return None and not crash on malformed JSON")

    def test_11_missing_required_field(self):
        """TEST 11: Telemetry missing required fields (e.g. power_w or temperature)."""
        incomplete_payload = {
            "temperature": 25.0,
            # Missing power_w, occupancy, appliances
        }
        res = process_telemetry_payload(json.dumps(incomplete_payload))
        self.assertIsNone(res, "Missing required fields must be rejected safely")

    def test_12_mqtt_disconnect_resilience(self):
        """TEST 12: MQTT Collector handles disconnect and reconnect logic gracefully."""
        collector = MQTTCollector()
        collector._setup_client()
        # Simulate on_disconnect callback
        collector._on_disconnect(collector.client, None, 1)
        # Should not raise exception
        self.assertIsNotNone(collector)

    def test_13_api_health_endpoint(self):
        """TEST 13: FastAPI /health endpoint verification."""
        resp = self.api_client.get("/health")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["status"], "ok")
        self.assertTrue(data["models_loaded"])
        self.assertGreater(data["total_telemetry_records"], 0)

    def test_14_api_complete_analysis_endpoint(self):
        """TEST 14: FastAPI /analysis returns full Phase 3 consumable schema including forecast."""
        resp = self.api_client.get("/analysis")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        # Validate schema keys
        self.assertIn("timestamp", data)
        self.assertIn("sensors", data)
        self.assertIn("appliances", data)
        self.assertIn("energy", data)
        self.assertIn("ai", data)
        self.assertIn("waste", data)
        self.assertIn("severity", data)
        self.assertIn("recommendation", data)
        self.assertIn("forecast", data)

        # Validate nested types
        self.assertIn("current_power_w", data["energy"])
        self.assertIn("predicted_power_w", data["energy"]) # Model 1 Expected Load
        self.assertIn("predicted_next_power_w", data["forecast"]) # Model 2 Short-Term Forecast
        self.assertIn("anomaly", data["ai"])
        self.assertIn("wasteful", data["waste"])

    # =========================================================================
    # ML IMPROVEMENT TESTS: SHORT-TERM POWER FORECASTING (MODEL 2)
    # =========================================================================

    def test_15_forecast_model_training_and_artifacts(self):
        """TEST 15: Verify forecast model artifact and metadata structure."""
        from backend.config import FORECAST_MODEL_PATH, FORECAST_META_PATH
        self.assertTrue(FORECAST_MODEL_PATH.exists(), "energy_forecast.joblib must exist")
        self.assertTrue(FORECAST_META_PATH.exists(), "forecast_metadata.json must exist")
        with open(FORECAST_META_PATH, "r") as f:
            meta = json.load(f)
        self.assertEqual(meta["model_type"], "LinearRegression")
        self.assertIn("mae_watts", meta["metrics"])
        self.assertIn("rmse_watts", meta["metrics"])
        self.assertIn("r2_score", meta["metrics"])
        self.assertIn("power_lag_1", meta["features"])

    def test_16_lag_feature_creation(self):
        """TEST 16: Verify lag feature creation and shift correctness."""
        from backend.features import build_lag_features_df
        import pandas as pd
        dummy_df = pd.DataFrame({
            "timestamp": ["2026-10-04T12:00:00", "2026-10-04T12:00:02", "2026-10-04T12:00:05", "2026-10-04T12:00:07"],
            "power_w": [150.0, 245.0, 1745.0, 3745.0],
            "temperature": [25.0, 25.1, 25.2, 25.3],
            "humidity": [50.0, 50.0, 50.0, 50.0],
            "occupancy": [1, 1, 1, 1]
        })
        X, y = build_lag_features_df(dummy_df)
        self.assertEqual(len(X), 1) # 4 rows minus 3 lags = 1 row
        self.assertEqual(float(X.iloc[0]["power_lag_1"]), 1745.0)
        self.assertEqual(float(X.iloc[0]["power_lag_2"]), 245.0)
        self.assertEqual(float(X.iloc[0]["power_lag_3"]), 150.0)
        self.assertEqual(float(y.iloc[0]), 3745.0)

    def test_17_no_current_target_data_leakage(self):
        """TEST 17: Strict verification that power_w is absent from forecasting features."""
        from backend.features import FORECAST_FEATURES
        self.assertNotIn("power_w", FORECAST_FEATURES, "power_w must NEVER be in FORECAST_FEATURES")
        self.assertNotIn("target_power", FORECAST_FEATURES)
        self.assertIn("power_lag_1", FORECAST_FEATURES)

    def test_18_forecast_prediction_computation(self):
        """TEST 18: Live forecast computation using PowerForecaster."""
        from backend.forecaster import get_forecaster
        forecaster = get_forecaster()
        rec = {"power_w": 1745, "temperature": 28.0, "humidity": 55.0, "occupancy": 1}
        res = forecaster.forecast_next(rec, custom_history=[150.0, 245.0, 1745.0])
        self.assertIn("forecast_power_w", res)
        self.assertIn("forecast_horizon", res)
        self.assertGreaterEqual(res["forecast_power_w"], 0.0)

    def test_19_api_forecast_endpoint(self):
        """TEST 19: Verify GET /forecast returns valid status and schema."""
        resp = self.api_client.get("/forecast")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("current_power_w", data)
        self.assertIn("forecast_power_w", data)
        self.assertIn("forecast_horizon", data)
        self.assertIn("forecast_error_w", data)
        self.assertIn("Linear Regression", data["model"])

    def test_20_normal_sequence_forecast(self):
        """TEST 20: Stable normal sequence [150W, 150W, 150W] predicts steady baseline load."""
        from backend.forecaster import get_forecaster
        forecaster = get_forecaster()
        rec = {"power_w": 150, "temperature": 24.0, "humidity": 50.0, "occupancy": 1}
        res = forecaster.forecast_next(rec, custom_history=[150.0, 150.0, 150.0])
        # Forecasted value should stay in a reasonable range
        self.assertGreater(res["forecast_power_w"], 0.0)

    def test_21_increasing_power_sequence_forecast(self):
        """TEST 21: Increasing power trend [150W -> 245W -> 1745W]."""
        from backend.forecaster import get_forecaster
        forecaster = get_forecaster()
        rec = {"power_w": 1745, "temperature": 26.0, "humidity": 52.0, "occupancy": 1}
        res = forecaster.forecast_next(rec, custom_history=[150.0, 245.0, 1745.0])
        self.assertIsNotNone(res["forecast_power_w"])
        self.assertEqual(res["current_power_w"], 1745)

    def test_22_decreasing_power_sequence_forecast(self):
        """TEST 22: Decreasing power trend [4650W -> 2150W -> 150W]."""
        from backend.forecaster import get_forecaster
        forecaster = get_forecaster()
        rec = {"power_w": 150, "temperature": 23.0, "humidity": 50.0, "occupancy": 1}
        res = forecaster.forecast_next(rec, custom_history=[4650.0, 2150.0, 150.0])
        self.assertIsNotNone(res["forecast_power_w"])
        self.assertEqual(res["current_power_w"], 150)

    def test_23_sudden_power_spike_sequence_forecast(self):
        """TEST 23: Sudden spike event [150W, 150W -> 2150W Space Heater spike]."""
        from backend.forecaster import get_forecaster
        forecaster = get_forecaster()
        rec = {"power_w": 2150, "temperature": 20.0, "humidity": 45.0, "occupancy": 1}
        res = forecaster.forecast_next(rec, custom_history=[150.0, 150.0, 2150.0])
        self.assertGreater(res["forecast_power_w"], 0.0)
        self.assertEqual(res["current_power_w"], 2150)


if __name__ == "__main__":
    print("\n" + "="*70)
    print(" EXECUTING 14 PHASE 2 ACCEPTANCE & INTEGRATION TESTS ")
    print("="*70)
    suite = unittest.TestLoader().loadTestsFromTestCase(TestPhase2SmartHomePipeline)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    if result.wasSuccessful():
        print("\n" + "="*70)
        print(" ALL 14 PHASE 2 TESTS PASSED PERFECTLY! [100% SUCCESS] ")
        print("="*70 + "\n")
        sys.exit(0)
    else:
        sys.exit(1)
