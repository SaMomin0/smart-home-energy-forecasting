#!/usr/bin/env python3
"""
Interactive Virtual ESP32 Simulator for VS Code.
Streams real-time MQTT telemetry to broker.hivemq.com:1883 matching sketch.ino.
Allows testing live dashboard updates with interactive keyboard appliance toggles.
"""

import sys
import time
import json
import random
import threading
from datetime import datetime
import paho.mqtt.client as mqtt

BROKER = "broker.hivemq.com"
PORT = 1883
TOPIC_TELEMETRY = "smart_home/telemetry"

state = {
    "temperature": 26.5,
    "humidity": 55.0,
    "occupancy": 1,
    "light_level": 420.0,
    "ac": 0,
    "fan": 0,
    "tv": 0,
    "room_light": 0,
    "refrigerator": 1,
    "heater": 0,
    "microwave": 0,
}

RATED_POWER = {
    "ac": 1500,
    "fan": 75,
    "tv": 120,
    "room_light": 20,
    "refrigerator": 150,
    "heater": 2000,
    "microwave": 1000,
}

running = True
client = mqtt.Client(client_id=f"VirtualESP32-Tester-{random.randint(1000, 9999)}")


def compute_power():
    return sum(RATED_POWER[app] * state[app] for app in RATED_POWER)


def publisher_loop():
    start_time = time.time()
    while running:
        power = compute_power()
        uptime_ms = int((time.time() - start_time) * 1000)

        payload = {
            "device_id": "esp32_energy_monitor",
            "uptime_ms": uptime_ms,
            "temperature": round(state["temperature"], 1),
            "humidity": round(state["humidity"], 1),
            "occupancy": int(state["occupancy"]),
            "light_level": round(state["light_level"], 1),
            "ac": state["ac"],
            "fan": state["fan"],
            "tv": state["tv"],
            "room_light": state["room_light"],
            "refrigerator": state["refrigerator"],
            "heater": state["heater"],
            "microwave": state["microwave"],
            "power_w": power,
            "status_msg": "Live Simulator Stream"
        }

        try:
            client.publish(TOPIC_TELEMETRY, json.dumps(payload))
            print(f"\r[{datetime.now().strftime('%H:%M:%S')}] Published: {power}W | AC:{state['ac']} HTR:{state['heater']} FRIDGE:{state['refrigerator']} OCC:{state['occupancy']} -> Press [1-7, o, q]: ", end="", flush=True)
        except Exception as e:
            print(f"\n[ERROR] Publish failed: {e}")

        time.sleep(2.5)


def main():
    global running
    print("=" * 60)
    print("  Virtual ESP32 Live Telemetry Generator (Cap Ai)")
    print("  Connecting to broker.hivemq.com:1883...")
    print("=" * 60)

    try:
        client.connect(BROKER, PORT, keepalive=60)
        client.loop_start()
        print("Connected to HiveMQ!")
    except Exception as e:
        print(f"Failed to connect to MQTT broker: {e}")
        return

    pub_thread = threading.Thread(target=publisher_loop, daemon=True)
    pub_thread.start()

    print("\nInteractive Appliance Controls:")
    print("  [1] Toggle AC (1500W)")
    print("  [2] Toggle Fan (75W)")
    print("  [3] Toggle TV (120W)")
    print("  [4] Toggle Room Light (20W)")
    print("  [5] Toggle Refrigerator (150W)")
    print("  [6] Toggle Space Heater (2000W)")
    print("  [7] Toggle Microwave (1000W)")
    print("  [o] Toggle Occupancy (0 or 1)")
    print("  [q] Quit\n")

    mapping = {
        "1": "ac",
        "2": "fan",
        "3": "tv",
        "4": "room_light",
        "5": "refrigerator",
        "6": "heater",
        "7": "microwave",
    }

    try:
        while running:
            char = input()
            char = char.strip().lower()
            if char in mapping:
                key = mapping[char]
                state[key] = 1 - state[key]
                print(f"\n>> Toggled {key.upper()} -> {'ON' if state[key] else 'OFF'} (Total: {compute_power()}W)")
            elif char == "o":
                state["occupancy"] = 1 - state["occupancy"]
                print(f"\n>> Toggled Occupancy -> {'OCCUPIED (1)' if state['occupancy'] else 'VACANT (0)'}")
            elif char == "q":
                running = False
                break
    except (KeyboardInterrupt, EOFError):
        running = False

    client.loop_stop()
    client.disconnect()
    print("\nSimulator stopped.")


if __name__ == "__main__":
    main()
