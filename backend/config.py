"""
Centralized Configuration for Smart Home Energy AI (Phase 2)
Centralizes MQTT, Database, File Paths, ML Parameters, and Severity Rules.
"""

import os
from pathlib import Path
from typing import Dict

# Base Directory Paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
MODELS_DIR = BASE_DIR / "models"

DATA_DIR.mkdir(parents=True, exist_ok=True)
MODELS_DIR.mkdir(parents=True, exist_ok=True)

# Database & CSV Storage Paths
DATABASE_PATH = Path(os.getenv("DATABASE_PATH", str(DATA_DIR / "smart_home.db")))
CSV_PATH = Path(os.getenv("CSV_PATH", str(DATA_DIR / "energy_data.csv")))

# Model File Paths
REGRESSION_MODEL_PATH = Path(os.getenv("REGRESSION_MODEL_PATH", str(MODELS_DIR / "energy_regression.joblib")))
FORECAST_MODEL_PATH = Path(os.getenv("FORECAST_MODEL_PATH", str(MODELS_DIR / "energy_forecast.joblib")))
ISOLATION_FOREST_PATH = Path(os.getenv("ISOLATION_FOREST_PATH", str(MODELS_DIR / "energy_isolation_forest.joblib")))

REGRESSION_META_PATH = Path(os.getenv("REGRESSION_META_PATH", str(MODELS_DIR / "regression_metadata.json")))
FORECAST_META_PATH = Path(os.getenv("FORECAST_META_PATH", str(MODELS_DIR / "forecast_metadata.json")))
ISOLATION_META_PATH = Path(os.getenv("ISOLATION_META_PATH", str(MODELS_DIR / "isolation_metadata.json")))

# MQTT Configuration (Matches Phase 1 Wokwi ESP32)
MQTT_HOST = os.getenv("MQTT_HOST", "broker.hivemq.com")
MQTT_PORT = int(os.getenv("MQTT_PORT", 1883))
MQTT_KEEPALIVE = int(os.getenv("MQTT_KEEPALIVE", 60))
MQTT_TOPIC_TELEMETRY = os.getenv("MQTT_TOPIC_TELEMETRY", "smart_home/telemetry")
MQTT_TOPIC_CONTROL = os.getenv("MQTT_TOPIC_CONTROL", "smart_home/control")

# Telemetry Sampling Interval (Phase 1 publishes every 2.5 seconds = 2500ms)
TELEMETRY_INTERVAL_S = float(os.getenv("TELEMETRY_INTERVAL_S", 2.5))

# Appliance Rated Power in Watts (Matches Phase 1 Wokwi Hardware Ratings exactly)
APPLIANCE_RATINGS: Dict[str, int] = {
    "ac": 1500,
    "fan": 75,
    "tv": 120,
    "room_light": 20,
    "refrigerator": 150,
    "heater": 2000,
    "microwave": 1000,
}

# High-Power Appliance Keys (Rated >= 1000 W)
HIGH_POWER_APPLIANCES = ["ac", "heater", "microwave"]

# Machine Learning Hyperparameters
RANDOM_STATE = 42
TEST_SPLIT_SIZE = 0.2
ISOLATION_CONTAMINATION = float(os.getenv("ISOLATION_CONTAMINATION", 0.05))
ISOLATION_N_ESTIMATORS = 100

# Power & Rule Thresholds (Watts & Lux)
HIGH_POWER_WARNING_THRESHOLD_W = 3000   # Multi-appliance high load alert
HIGH_POWER_CRITICAL_THRESHOLD_W = 4500  # Extreme grid stress limit
DAYLIGHT_LUX_THRESHOLD = 300            # Lux above which room light is considered daylight waste

# Severity Levels
SEVERITY_NORMAL = "NORMAL"
SEVERITY_WARNING = "WARNING"
SEVERITY_HIGH = "HIGH"
SEVERITY_CRITICAL = "CRITICAL"

# FastAPI Configuration
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", 8000))
