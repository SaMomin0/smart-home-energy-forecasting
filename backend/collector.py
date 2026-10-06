"""
MQTT Telemetry Collector and Real-Time Stream Processor.
Subscribes to Wokwi ESP32 MQTT topic 'smart_home/telemetry', validates incoming JSON,
executes the end-to-end AI/Rules pipeline, stores records in SQLite/CSV,
and maintains live telemetry state.
"""

import sys
import json
import time
import logging
import threading
from typing import Dict, Any, Optional
from datetime import datetime, timezone

import paho.mqtt.client as mqtt

from backend.config import (
    MQTT_HOST,
    MQTT_PORT,
    MQTT_KEEPALIVE,
    MQTT_TOPIC_TELEMETRY,
    TELEMETRY_INTERVAL_S,
)
from backend.preprocessing import preprocess_telemetry
from backend.database import init_db, save_telemetry
from backend.predictor import get_predictor
from backend.anomaly import get_anomaly_detector
from backend.rules import evaluate_waste_rules
from backend.recommendations import compute_severity_and_recommendations

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("smart_home.collector")

# In-memory thread-safe cache for fastest API reads
_latest_lock = threading.Lock()
_latest_telemetry: Optional[Dict[str, Any]] = None
_latest_analysis: Optional[Dict[str, Any]] = None
_is_connected = False


def get_cached_latest() -> Optional[Dict[str, Any]]:
    with _latest_lock:
        return _latest_telemetry


def get_cached_analysis() -> Optional[Dict[str, Any]]:
    with _latest_lock:
        return _latest_analysis


def is_mqtt_connected() -> bool:
    return _is_connected


def process_telemetry_payload(payload_str: str) -> Optional[Dict[str, Any]]:
    """
    Executes the complete processing pipeline on an incoming JSON string:
      1. Parse & validate JSON
      2. Preprocess & calculate exact energy
      3. Feature engineering & Linear Regression expected power prediction
      4. Isolation Forest statistical anomaly detection
      5. Rule-Based wasteful usage detection
      6. Severity & Dynamic recommendation synthesis
      7. Persist to SQLite
      8. Update in-memory cache
    """
    global _latest_telemetry, _latest_analysis

    # 1. Parse JSON safely
    try:
        raw_dict = json.loads(payload_str)
    except json.JSONDecodeError as err:
        logger.error(f"Malformed MQTT JSON rejected: {err}. Raw payload: {payload_str[:120]}")
        return None

    # 2. Validate and Preprocess
    try:
        clean_record = preprocess_telemetry(raw_dict, sampling_interval_s=TELEMETRY_INTERVAL_S)
    except ValueError as val_err:
        logger.warning(f"Telemetry validation error: {val_err}")
        return None

    # 3. Model Inference: Linear Regression Expected Power (Model 1)
    predictor = get_predictor()
    pred_res = predictor.predict(clean_record)

    # 4. Model Inference: Short-Term Energy Forecasting (Model 2 - Lagged Autoregression)
    from backend.forecaster import get_forecaster
    forecaster = get_forecaster()
    forecaster.record_observation(clean_record["power_w"])
    forecast_res = forecaster.forecast_next(clean_record)

    # 5. Model Inference: Isolation Forest Anomaly Detection (Model 3)
    detector = get_anomaly_detector()
    anom_res = detector.detect(clean_record)

    # 6. Domain Rules: Wasteful Usage Detection
    waste_res = evaluate_waste_rules(clean_record)

    # 7. Severity and Recommendations Synthesis
    severity, primary_rec, action_list = compute_severity_and_recommendations(
        telemetry=clean_record,
        prediction_info=pred_res,
        anomaly_info=anom_res,
        waste_info=waste_res,
    )

    # Assemble complete unified analysis response
    analysis = {
        "timestamp": clean_record["timestamp"],
        "sensors": {
            "temperature": clean_record["temperature"],
            "humidity": clean_record["humidity"],
            "occupancy": clean_record["occupancy"],
            "light_level": clean_record["light_level"],
        },
        "appliances": {
            "ac": clean_record["ac"],
            "fan": clean_record["fan"],
            "tv": clean_record["tv"],
            "room_light": clean_record["room_light"],
            "refrigerator": clean_record["refrigerator"],
            "heater": clean_record["heater"],
            "microwave": clean_record["microwave"],
        },
        "energy": {
            "current_power_w": clean_record["power_w"],
            "predicted_power_w": pred_res["predicted_power_w"],
            "difference_w": pred_res["difference_w"],
            "percentage_difference": pred_res["percentage_difference"],
            "energy_wh": clean_record["energy_wh"],
            "energy_kwh": clean_record["energy_kwh"],
        },
        "forecast": {
            "predicted_next_power_w": forecast_res["forecast_power_w"],
            "forecast_horizon": forecast_res["forecast_horizon"],
            "expected_change_w": forecast_res["expected_change_w"],
            "model": forecast_res["model"],
        },
        "ai": {
            "anomaly": anom_res["is_anomaly"],
            "anomaly_score": anom_res["anomaly_score"],
        },
        "waste": {
            "wasteful": waste_res["wasteful"],
            "reasons": waste_res["reasons"],
            "potential_waste_watts": waste_res["potential_waste_watts"],
        },
        "severity": severity,
        "recommendation": primary_rec,
        "action_items": action_list,
    }

    # 7. Persist to SQLite Database
    db_record = {
        "timestamp": clean_record["timestamp"],
        "uptime_ms": clean_record["uptime_ms"],
        "temperature": clean_record["temperature"],
        "humidity": clean_record["humidity"],
        "occupancy": clean_record["occupancy"],
        "light_level": clean_record["light_level"],
        "ac": clean_record["ac"],
        "fan": clean_record["fan"],
        "tv": clean_record["tv"],
        "room_light": clean_record["room_light"],
        "refrigerator": clean_record["refrigerator"],
        "heater": clean_record["heater"],
        "microwave": clean_record["microwave"],
        "power_w": clean_record["power_w"],
        "energy_wh": clean_record["energy_wh"],
        "energy_kwh": clean_record["energy_kwh"],
        "predicted_power_w": pred_res["predicted_power_w"],
        "prediction_error_w": pred_res["difference_w"],
        "is_anomaly": 1 if anom_res["is_anomaly"] else 0,
        "anomaly_score": anom_res["anomaly_score"],
        "wasteful": 1 if waste_res["wasteful"] else 0,
        "severity": severity,
        "status_msg": clean_record.get("status_msg", "Normal"),
        "recommendation": primary_rec,
    }

    try:
        row_id = save_telemetry(db_record)
        clean_record["db_id"] = row_id
    except Exception as db_err:
        logger.error(f"Failed storing record in SQLite: {db_err}")

    # 8. Update in-memory caches
    with _latest_lock:
        _latest_telemetry = clean_record
        _latest_analysis = analysis

    logger.info(
        f"[TELEMETRY PROCESSED] Power: {clean_record['power_w']}W (Exp: {pred_res['predicted_power_w']}W) | "
        f"Waste: {waste_res['wasteful']} | Anom: {anom_res['is_anomaly']} | Severity: {severity}"
    )

    return analysis


class MQTTCollector:
    """Non-blocking, resilient MQTT client for Phase 1 ESP32 stream."""

    def __init__(self, host: str = MQTT_HOST, port: int = MQTT_PORT, topic: str = MQTT_TOPIC_TELEMETRY):
        self.host = host
        self.port = port
        self.topic = topic
        self.client_id = f"SmartHome-Phase2-Collector-{int(time.time())}"
        self.client = None
        self._thread = None
        self._running = False

    def _setup_client(self):
        if hasattr(mqtt, "CallbackAPIVersion"):
            self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=self.client_id)
        else:
            self.client = mqtt.Client(client_id=self.client_id)

        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_message = self._on_message
        self.client.reconnect_delay_set(min_delay=1, max_delay=10)

    def _on_connect(self, *args, **kwargs):
        global _is_connected
        _is_connected = True
        client = args[0]
        logger.info(f"Connected to MQTT broker {self.host}:{self.port}. Subscribing to '{self.topic}'...")
        client.subscribe(self.topic, qos=0)

    def _on_disconnect(self, *args, **kwargs):
        global _is_connected
        _is_connected = False
        logger.warning(f"Disconnected from MQTT broker. Automatic reconnection in progress...")

    def _on_message(self, client, userdata, msg):
        try:
            payload_str = msg.payload.decode("utf-8", errors="ignore")
            process_telemetry_payload(payload_str)
        except Exception as e:
            logger.error(f"Unexpected error processing MQTT message: {e}")

    def start_background(self):
        """Starts collector loop in a daemon thread."""
        if self._running:
            return
        self._setup_client()
        self._running = True
        try:
            self.client.connect(self.host, self.port, keepalive=MQTT_KEEPALIVE)
            self.client.loop_start()
            logger.info("MQTT Collector background thread started.")
        except Exception as e:
            logger.error(f"Initial MQTT connection failed: {e}. Will retry in background.")

    def stop(self):
        self._running = False
        if self.client:
            self.client.loop_stop()
            self.client.disconnect()
            logger.info("MQTT Collector stopped.")

    def run_blocking(self):
        """Runs the collector in foreground (blocking mode)."""
        self._setup_client()
        self._running = True
        init_db()
        logger.info(f"Starting standalone MQTT Collector. Connecting to {self.host}:{self.port}...")
        try:
            self.client.connect(self.host, self.port, keepalive=MQTT_KEEPALIVE)
            self.client.loop_forever()
        except KeyboardInterrupt:
            logger.info("MQTT Collector terminated by user.")
        finally:
            self.stop()


# Singleton background collector for API usage
_global_collector: Optional[MQTTCollector] = None


def get_collector() -> MQTTCollector:
    global _global_collector
    if _global_collector is None:
        _global_collector = MQTTCollector()
    return _global_collector


def main():
    print("===================================================================")
    print("  AI FOR IOT CAPSTONE: PHASE 2 STANDALONE MQTT COLLECTOR           ")
    print(f"  Target Broker: {MQTT_HOST}:{MQTT_PORT}                           ")
    print(f"  Target Topic : {MQTT_TOPIC_TELEMETRY}                            ")
    print("===================================================================")
    collector = MQTTCollector()
    collector.run_blocking()


if __name__ == "__main__":
    main()
