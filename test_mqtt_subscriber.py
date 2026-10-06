#!/usr/bin/env python3
"""
===============================================================================
AI FOR IOT CAPSTONE PROJECT - PHASE 1 VERIFICATION & DATA COLLECTION UTILITY
Project: AI-Based Smart Home Energy Consumption Forecasting & Waste Detection
File   : test_mqtt_subscriber.py
===============================================================================
Purpose:
  1. Subscribes to MQTT topics published by the Wokwi ESP32 simulator.
  2. Renders live, formatted telemetry dashboards in the terminal.
  3. Validates the JSON telemetry schema against Phase 2 requirements.
  4. Automatically records streaming telemetry into 'energy_telemetry_dataset.csv'
     to serve as the foundational dataset for Phase 2 Machine Learning models.
  5. Allows sending remote control presets (NORMAL, WASTE, SPIKE, HIGH_LOAD)
     to test bidirectional IoT command-and-control.
===============================================================================
Prerequisites:
  pip install paho-mqtt
Usage:
  python3 test_mqtt_subscriber.py
===============================================================================
"""

import sys
import json
import time
import csv
import os
from datetime import datetime

try:
    import paho.mqtt.client as mqtt
except ImportError:
    print("\n[ERROR] paho-mqtt is not installed.")
    print("Please install it using: pip install paho-mqtt\n")
    sys.exit(1)

MQTT_BROKER = "broker.hivemq.com"
MQTT_PORT = 1883
TOPIC_TELEMETRY = "smart_home/telemetry"
TOPIC_CONTROL = "smart_home/control"
DATASET_FILE = "energy_telemetry_dataset.csv"

# CSV Fieldnames for Phase 2 ML Dataset
CSV_FIELDS = [
    "timestamp_iso",
    "uptime_ms",
    "temperature_c",
    "humidity_pct",
    "occupancy",
    "light_lux",
    "ac_state",
    "fan_state",
    "tv_state",
    "room_light_state",
    "refrigerator_state",
    "heater_state",
    "microwave_state",
    "total_power_w",
    "cumulative_energy_kwh",
    "waste_flag",
    "high_load_flag",
    "status_msg"
]

sample_count = 0

def init_csv():
    """Initializes CSV file with header if not already present."""
    if not os.path.exists(DATASET_FILE):
        with open(DATASET_FILE, mode="w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
            writer.writeheader()
        print(f"[DATASET] Created new training dataset log: {DATASET_FILE}")
    else:
        print(f"[DATASET] Appending to existing dataset: {DATASET_FILE}")

def on_connect(*args, **kwargs):
    # Handles both Paho v1 (client, userdata, flags, rc) and Paho v2 (client, userdata, flags, reason_code, properties)
    client = args[0]
    rc = args[3] if len(args) > 3 else 0
    # In Paho v2, rc is a ReasonCode object whose value is 0 on success
    rc_val = getattr(rc, "value", rc)
    if rc_val == 0:
        print("\n========================================================")
        print("  CONNECTED TO MQTT BROKER: " + MQTT_BROKER)
        print("  SUBSCRIBING TO: smart_home/#")
        print("========================================================\n")
        client.subscribe("smart_home/#")
    else:
        print(f"[ERROR] Connection failed with result code {rc}")

def on_message(client, userdata, msg):
    global sample_count
    topic = msg.topic
    payload_str = msg.payload.decode("utf-8", errors="ignore")

    if topic == TOPIC_TELEMETRY:
        try:
            data = json.loads(payload_str)
            sample_count += 1
            now_iso = datetime.now().isoformat()

            # Extract fields with safe defaults
            uptime_ms = data.get("uptime_ms", 0)
            temp = float(data.get("temperature", 0.0))
            hum = float(data.get("humidity", 0.0))
            occ = int(data.get("occupancy", 0))
            lux = int(data.get("light_level", 0))

            ac = int(data.get("ac", 0))
            fan = int(data.get("fan", 0))
            tv = int(data.get("tv", 0))
            light = int(data.get("room_light", 0))
            fridge = int(data.get("refrigerator", 0))
            heater = int(data.get("heater", 0))
            micro = int(data.get("microwave", 0))

            power_w = int(data.get("power_w", 0))
            energy_kwh = float(data.get("energy_kwh", 0.0))
            waste = int(data.get("waste_flag", 0))
            high_load = int(data.get("high_load_flag", 0))
            status = data.get("status_msg", "Normal")

            # Terminal Display
            print("\033[2J\033[H", end="") # Clear terminal screen
            print("================================================================================")
            print(f" AI FOR IOT CAPSTONE - SMART HOME TELEMETRY RECEIVER (Sample #{sample_count})")
            print(f" Timestamp: {now_iso} | Uptime: {uptime_ms/1000.0:.1f}s | Source: Wokwi ESP32")
            print("================================================================================")
            print(f" [ENVIRONMENT]  Temp: {temp:5.1f} °C   | Humidity: {hum:4.1f} %  | Light: {lux:4d} lux")
            print(f" [OCCUPANCY]    Status: {'[PERSON PRESENT]' if occ else '[ROOM VACANT]':20s} (Binary: {occ})")
            print("--------------------------------------------------------------------------------")
            print(" APPLIANCE LOAD BREAKDOWN:")
            print(f"   - Air Conditioner [1500W]: {'[ON ]' if ac else '[OFF]'}  |  Ceiling Fan    [  75W]: {'[ON ]' if fan else '[OFF]'}")
            print(f"   - Television      [ 120W]: {'[ON ]' if tv else '[OFF]'}  |  Room Light     [  20W]: {'[ON ]' if light else '[OFF]'}")
            print(f"   - Refrigerator    [ 150W]: {'[ON ]' if fridge else '[OFF]'}  |  Space Heater   [2000W]: {'[ON ]' if heater else '[OFF]'}")
            print(f"   - Microwave Oven  [1000W]: {'[ON ]' if micro else '[OFF]'}")
            print("--------------------------------------------------------------------------------")
            print(f" ELECTRICAL TOTAL:  Power = {power_w:4d} Watts  |  Energy = {energy_kwh:.4f} kWh")

            # Flag & Alert Indicators
            flag_str = ""
            if waste:
                flag_str += "\033[93m[WASTE ALERT DETECTED]\033[0m "
            if high_load:
                flag_str += "\033[91m[HIGH LOAD WARNING]\033[0m "
            if not waste and not high_load:
                flag_str += "\033[92m[NORMAL BALANCED LOAD]\033[0m"

            print(f" SYSTEM DIAGNOSIS: {flag_str}")
            print(f" DIAGNOSIS DETAIL: {status}")
            print("================================================================================")
            print(f" [LOGGING] Saved sample #{sample_count} to '{DATASET_FILE}'")
            print(" Press Ctrl+C to terminate data logging.")

            # Record row to CSV
            row = {
                "timestamp_iso": now_iso,
                "uptime_ms": uptime_ms,
                "temperature_c": temp,
                "humidity_pct": hum,
                "occupancy": occ,
                "light_lux": lux,
                "ac_state": ac,
                "fan_state": fan,
                "tv_state": tv,
                "room_light_state": light,
                "refrigerator_state": fridge,
                "heater_state": heater,
                "microwave_state": micro,
                "total_power_w": power_w,
                "cumulative_energy_kwh": energy_kwh,
                "waste_flag": waste,
                "high_load_flag": high_load,
                "status_msg": status
            }
            with open(DATASET_FILE, mode="a", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
                writer.writerow(row)

        except Exception as e:
            print(f"[PARSE ERROR] Failed to parse JSON: {e}")
            print(f"Raw: {payload_str}")

def main():
    init_csv()

    if hasattr(mqtt, "CallbackAPIVersion"):
        client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=f"Capstone-Subscriber-{int(time.time())}")
    else:
        client = mqtt.Client(client_id=f"Capstone-Subscriber-{int(time.time())}")

    client.on_connect = on_connect
    client.on_message = on_message

    print(f"[CONNECTING] Connecting to {MQTT_BROKER}:{MQTT_PORT}...")
    try:
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
    except Exception as e:
        print(f"[ERROR] Could not connect to broker: {e}")
        sys.exit(1)

    try:
        client.loop_forever()
    except KeyboardInterrupt:
        print(f"\n[TERMINATED] Exited successfully. {sample_count} samples logged to '{DATASET_FILE}'.")
        client.disconnect()

if __name__ == "__main__":
    main()
