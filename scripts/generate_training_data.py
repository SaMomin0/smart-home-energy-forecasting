"""
Synthetic Energy Telemetry Dataset Generator.
Generates realistic multi-day household behavioral records strictly matching Phase 1 appliance
wattage ratings, environmental circadian cycles, and operational scenarios:
  1. NORMAL (Standard occupied household patterns, circadian routines)
  2. WASTEFUL (Unoccupied room with AC/TV/Lights active)
  3. HIGH_LOAD (Multiple high-wattage heating/cooling devices active)
  4. SPIKE (Transient power bursts from Microwave or Heater)
  5. NIGHT (Low light, quiet baseline, refrigerator cycle)
  6. DAY (Abundant daylight, ambient temperature rise, daytime occupancy shift)
"""

import sys
import random
from pathlib import Path
from datetime import datetime, timedelta, timezone

# Ensure project root is on sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

import pandas as pd
import numpy as np

from backend.config import APPLIANCE_RATINGS, DATA_DIR, CSV_PATH, DATABASE_PATH, TELEMETRY_INTERVAL_S
from backend.database import init_db, save_telemetry


def generate_realistic_dataset(num_samples: int = 6000, start_date: datetime = None) -> pd.DataFrame:
    """
    Synthesizes a realistic time-series dataset of household energy usage.
    Each sample represents a 2.5-second to 1-minute interval over several contiguous days.
    """
    if start_date is None:
        start_date = datetime(2026, 9, 25, 0, 0, 0, tzinfo=timezone.utc)

    random.seed(42)
    np.random.seed(42)

    records = []
    current_time = start_date
    delta_step = timedelta(seconds=int(TELEMETRY_INTERVAL_S * 20)) # Step by 50 seconds for realistic multi-day distribution

    # Appliance base ratings
    R_AC = APPLIANCE_RATINGS["ac"]           # 1500 W
    R_FAN = APPLIANCE_RATINGS["fan"]         #   75 W
    R_TV = APPLIANCE_RATINGS["tv"]           #  120 W
    R_LIGHT = APPLIANCE_RATINGS["room_light"]#   20 W
    R_FRIDGE = APPLIANCE_RATINGS["refrigerator"] # 150 W
    R_HEATER = APPLIANCE_RATINGS["heater"]   # 2000 W
    R_MICRO = APPLIANCE_RATINGS["microwave"] # 1000 W

    cum_energy_wh = 0.0

    print(f"[DATASET GENERATOR] Synthesizing {num_samples} realistic smart home records...")

    for i in range(num_samples):
        hour = current_time.hour
        is_weekend = current_time.weekday() >= 5

        # ---------------------------------------------------------------------
        # 1. Environmental Simulation (Circadian Temperature & Light)
        # ---------------------------------------------------------------------
        # Outdoor / indoor temp cycles: lowest at 5 AM (~21°C), peak at 3 PM (~31°C)
        temp_cycle = 26.0 + 5.0 * np.sin((hour - 9) * np.pi / 12) + random.uniform(-0.8, 0.8)
        temperature = round(float(temp_cycle), 1)

        # Humidity inversely correlates with temperature
        hum_cycle = 65.0 - 15.0 * np.sin((hour - 9) * np.pi / 12) + random.uniform(-2.0, 2.0)
        humidity = round(float(np.clip(hum_cycle, 25.0, 90.0)), 1)

        # Sunlight lux: 0-30 at night, up to 700-950 during mid-day
        if 6 <= hour <= 18:
            light_peak = 800.0 * np.sin((hour - 6) * np.pi / 12) + random.uniform(-30, 40)
            light_level = int(np.clip(light_peak, 50, 950))
        else:
            light_level = random.randint(10, 45)

        # ---------------------------------------------------------------------
        # 2. Behavioral Patterns & Scenarios
        # ---------------------------------------------------------------------
        scenario_dice = random.random()

        # Default appliance baseline: Refrigerator is always cycling (mostly ON)
        refrigerator = 1 if random.random() > 0.1 else 0
        ac = 0
        fan = 0
        tv = 0
        room_light = 0
        heater = 0
        microwave = 0
        occupancy = 0
        status_msg = "Normal"

        if scenario_dice < 0.12:
            # -----------------------------------------------------------------
            # SCENARIO B: WASTEFUL USAGE (Unoccupied with AC, TV, or Lights left ON)
            # -----------------------------------------------------------------
            occupancy = 0
            waste_type = random.choice(["ac_vacant", "tv_vacant", "all_vacant", "daylight_light"])
            if waste_type == "ac_vacant":
                ac = 1
                status_msg = "Waste: AC cooling unoccupied room"
            elif waste_type == "tv_vacant":
                tv = 1
                room_light = 1
                status_msg = "Waste: TV and light left ON in empty home"
            elif waste_type == "all_vacant":
                ac = 1
                tv = 1
                room_light = 1
                status_msg = "Waste: AC, TV & Light ON with room vacant"
            elif waste_type == "daylight_light":
                room_light = 1
                status_msg = "Waste: Room light burning during daylight"

        elif scenario_dice < 0.20:
            # -----------------------------------------------------------------
            # SCENARIO C: HIGH LOAD / OVERLOAD (Multiple Heavy Draw Appliances)
            # -----------------------------------------------------------------
            occupancy = 1
            ac = 1
            heater = 1
            microwave = 1 if random.random() > 0.4 else 0
            room_light = 1
            status_msg = "High Load: Multiple heavy appliances active concurrently"

        elif scenario_dice < 0.26:
            # -----------------------------------------------------------------
            # SCENARIO D: TRANSIENT SPIKE EVENT
            # -----------------------------------------------------------------
            occupancy = 1
            room_light = 1
            # Microwave or Space Heater pulse
            if random.random() > 0.5:
                microwave = 1
                tv = 1
                status_msg = "Spike: Microwave heating meal"
            else:
                heater = 1
                status_msg = "Spike: Space Heater rapid heating burst"

        else:
            # -----------------------------------------------------------------
            # SCENARIO A: NORMAL CIRCADIAN HOUSEHOLD BEHAVIOR
            # -----------------------------------------------------------------
            if 0 <= hour < 6:
                # Night: Occupants sleeping
                occupancy = 1
                room_light = 0
                fan = 1 if temperature > 25.0 and random.random() > 0.4 else 0
                heater = 1 if temperature < 22.0 and random.random() > 0.5 else 0
                status_msg = "Normal: Night sleep baseline"

            elif 6 <= hour < 9:
                # Morning routine
                occupancy = 1
                room_light = 1 if light_level < 300 else 0
                microwave = 1 if random.random() < 0.25 else 0 # Breakfast
                fan = 1 if temperature > 25 else 0
                status_msg = "Normal: Morning routine"

            elif 9 <= hour < 17:
                # Work hours
                if is_weekend:
                    occupancy = 1
                    tv = 1 if random.random() > 0.4 else 0
                    ac = 1 if temperature > 28.0 else 0
                    fan = 1 if temperature > 24.0 else 0
                    status_msg = "Normal: Weekend daytime leisure"
                else:
                    # Away at work
                    occupancy = 0
                    status_msg = "Normal: Vacant during work hours"

            else:
                # Evening peak (17 to 23)
                occupancy = 1
                room_light = 1 # Nighttime lighting
                tv = 1 if random.random() > 0.3 else 0
                ac = 1 if temperature > 27.0 else 0
                fan = 1 if temperature > 24.0 and not ac else 0
                microwave = 1 if random.random() < 0.15 else 0 # Dinner reheat
                status_msg = "Normal: Evening family leisure"

        # ---------------------------------------------------------------------
        # 3. Deterministic Power Summation (Strictly matching Phase 1 model)
        # ---------------------------------------------------------------------
        power_w = (
            ac * R_AC
            + fan * R_FAN
            + tv * R_TV
            + room_light * R_LIGHT
            + refrigerator * R_FRIDGE
            + heater * R_HEATER
            + microwave * R_MICRO
        )

        # Compute incremental energy
        interval_hours = delta_step.total_seconds() / 3600.0
        sample_wh = power_w * interval_hours
        cum_energy_wh += sample_wh
        cum_energy_kwh = round(cum_energy_wh / 1000.0, 5)

        # IoT pre-ML flags
        waste_flag = 1 if (
            (occupancy == 0 and (ac or tv or heater or room_light)) or
            (room_light and light_level > 300 and occupancy == 1)
        ) else 0

        high_load_flag = 1 if (power_w >= 3000 or (ac + heater + microwave >= 2)) else 0

        record = {
            "timestamp": current_time.isoformat(),
            "uptime_ms": i * int(delta_step.total_seconds() * 1000),
            "temperature": temperature,
            "humidity": humidity,
            "occupancy": occupancy,
            "light_level": light_level,
            "ac": ac,
            "fan": fan,
            "tv": tv,
            "room_light": room_light,
            "refrigerator": refrigerator,
            "heater": heater,
            "microwave": microwave,
            "power_w": power_w,
            "energy_wh": round(sample_wh, 4),
            "energy_kwh": cum_energy_kwh,
            "predicted_power_w": power_w, # Seed value for initial DB
            "prediction_error_w": 0.0,
            "is_anomaly": high_load_flag,
            "anomaly_score": -0.25 if high_load_flag else 0.15,
            "wasteful": waste_flag,
            "severity": "HIGH" if (waste_flag and power_w > 1000) or high_load_flag else ("WARNING" if waste_flag else "NORMAL"),
            "status_msg": status_msg,
            "recommendation": "Maintain standard schedule" if not waste_flag else "Turn off idle appliances in unoccupied room"
        }

        records.append(record)
        current_time += delta_step

    df = pd.DataFrame(records)
    return df


def main():
    print("===================================================================")
    print(" AI FOR IOT CAPSTONE: PHASE 2 TRAINING DATASET GENERATION         ")
    print("===================================================================")

    init_db()

    df = generate_realistic_dataset(num_samples=7200)

    # Save to CSV
    CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(CSV_PATH, index=False)
    print(f"[SUCCESS] Saved {len(df)} samples to CSV: {CSV_PATH}")

    # Seed SQLite database
    print(f"[DATABASE] Seeding SQLite database: {DATABASE_PATH}...")
    for _, row in df.iterrows():
        save_telemetry(row.to_dict())

    print(f"[SUCCESS] SQLite database initialized and seeded with {len(df)} historical telemetry records.")
    print("-------------------------------------------------------------------")
    print("DATASET PROFILE:")
    print(f"  - Total Records       : {len(df)}")
    print(f"  - Power Min / Max     : {df['power_w'].min()} W / {df['power_w'].max()} W")
    print(f"  - Mean Household Power: {df['power_w'].mean():.1f} W")
    print(f"  - Wasteful Samples    : {df['wasteful'].sum()} ({df['wasteful'].mean()*100:.1f}%)")
    print(f"  - High-Load Anomalies : {df['is_anomaly'].sum()} ({df['is_anomaly'].mean()*100:.1f}%)")
    print("===================================================================\n")


if __name__ == "__main__":
    main()
