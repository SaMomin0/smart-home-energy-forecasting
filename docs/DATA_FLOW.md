# End-to-End Data Flow Specification

**Project Title:** AI-Based Smart Home Energy Consumption Forecasting & Wasteful Usage Detection  
**Document:** End-to-End Data Flow & Transformation Pipeline  
**Author:** AI-for-IoT Capstone Team  
**Status:** Certified Release Candidate (Phase 3.4)

---

## 1. Complete Telemetry Pipeline Sequence

The diagram below traces the end-to-end lifecycle of a single telemetry frame from physical sensor acquisition in Wokwi through MQTT transmission, validation, storage, inference, and visualization.

```text
[Step 1: Environmental Acquisition]
    DHT22 (Temp, Humidity) | PIR (Motion / Occupancy) | LDR (Illuminance ADC)
                          ↓
[Step 2: Appliance Finite State Machine]
    Virtual Appliance Controller (AC, Fan, TV, Room Light, Fridge, Heater, Microwave)
                          ↓
[Step 3: Instantaneous Power Calculation]
    Total Power (W) = Sum of (Appliance Rated Watts × Binary State)
                          ↓
[Step 4: Serialized Telemetry JSON]
    Wokwi WiFiClient publishes to HiveMQ MQTT Topic 'smart_home/telemetry'
                          ↓
[Step 5: Ingestion & Pydantic Validation]
    Python Paho-MQTT Collector parses JSON and validates with Pydantic Schema
                          ↓
[Step 6: Timestamping & Numerical Integration]
    ISO-8601 UTC timestamp assigned; Energy (Wh) integrated using Δt = 2.5s
                          ↓
[Step 7: Multi-Model Feature Engineering]
    Feature extraction produces regression, forecasting lags, and isolation vectors
                          ↓
[Step 8: Machine Learning & Rules Inference]
    Model 1 (Expected Load) + Model 2 (Lagged Forecast) + Model 3 (Anomaly) + Rule Engine
                          ↓
[Step 9: Database Persistence]
    Record persisted to SQLite relational store ('data/smart_home.db')
                          ↓
[Step 10: FastAPI REST Dissemination]
    Endpoints (/analysis, /history, /latest, /forecast) expose normalized payload
                          ↓
[Step 11: Streamlit Dashboard & Plotly Rendering]
    Apple-styled cards, interactive Plotly charts, and investigation drawers update
```

---

## 2. Mathematical Energy Integration Formula

Power is an instantaneous measurement of the rate of energy consumption in **Watts ($W$)** or **Joules per second ($J/s$)**.  
Energy represents cumulative work performed over time in **Watt-hours ($Wh$)** or **Kilowatt-hours ($kWh$)**.

### Continuous Integration
$$E(t) = \int_{0}^{t} P(\tau) \, d\tau$$

### Discrete Trapezoidal Integration
In the digital IoT pipeline, measurements arrive discretely at interval $\Delta t = 2.5\text{ seconds}$ ($2,500\text{ ms}$). The incremental energy consumed during interval $i$ is calculated as:

$$\Delta E_i \, (\text{Wh}) = \frac{P_i + P_{i-1}}{2} \times \frac{\Delta t}{3600}$$

For constant-step streaming where $P$ is held across the nominal interval:
$$\Delta E_i \, (\text{Wh}) = P_i \, (\text{W}) \times \frac{2.5\text{ s}}{3600\text{ s/h}} \approx P_i \times 0.00069444\text{ Wh}$$

Cumulative household energy in Kilowatt-hours ($kWh$) is accumulated sequentially:
$$E_{\text{total}} \, (\text{kWh}) = \frac{\sum_{i=1}^{N} \Delta E_i \, (\text{Wh})}{1000}$$

---

## 3. Data Transformation Stages & Payloads

### Stage 1: ESP32 Edge Telemetry (MQTT JSON)
Published every 2.5s over `smart_home/telemetry`:
```json
{
  "device_id": "esp32_energy_monitor",
  "uptime_ms": 142500,
  "temperature": 27.5,
  "humidity": 58.2,
  "occupancy": 1,
  "light_level": 420,
  "ac": 1,
  "fan": 0,
  "tv": 1,
  "room_light": 0,
  "refrigerator": 1,
  "heater": 0,
  "microwave": 0,
  "power_w": 1770,
  "status_msg": "Nominal evening occupancy"
}
```

### Stage 2: Validated Database Record (SQLite `telemetry` table)
Enriched with chronological primary keys, integration state, and diagnostic flags:
```sql
CREATE TABLE telemetry (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    uptime_ms INTEGER,
    temperature REAL,
    humidity REAL,
    occupancy INTEGER,
    light_level REAL,
    ac INTEGER,
    fan INTEGER,
    tv INTEGER,
    room_light INTEGER,
    refrigerator INTEGER,
    heater INTEGER,
    microwave INTEGER,
    power_w REAL,
    energy_wh REAL,
    energy_kwh REAL,
    predicted_power_w REAL,
    prediction_error_w REAL,
    is_anomaly INTEGER,
    anomaly_score REAL,
    wasteful INTEGER,
    severity TEXT,
    status_msg TEXT
);
```

### Stage 3: Feature Engineering Matrices

#### Model 1 Feature Vector ($1 \times 21$):
```text
[temperature, humidity, occupancy, light_level, ac, fan, tv, room_light,
 refrigerator, heater, microwave, appliance_count, high_power_count,
 hour, minute, day_of_week, occupied_ac, occupied_fan, occupied_light,
 occupied_heater, daylight_light]
```

#### Model 2 Forecasting Feature Vector ($1 \times 10$):
```text
[power_lag_1 (t-1), power_lag_2 (t-2), power_lag_3 (t-3),
 power_rolling_mean_3, power_trend_1_2,
 temperature, humidity, occupancy, hour, minute]
```

#### Model 3 Anomaly Feature Vector ($1 \times 8$):
```text
[power_w, temperature, humidity, occupancy, appliance_count,
 high_power_count, hour, total_appliance_power]
```

---

## 4. Controlled Scenario Data Flow (`POST /scenario`)

To support deterministic academic evaluation and live viva demonstrations, the FastAPI backend exposes `POST /scenario`.

1. Evaluator selects a preset: `NORMAL`, `WASTEFUL`, `HIGH LOAD`, or `SPIKE`.
2. The endpoint constructs a canonical sensor and appliance telemetry vector representing that real-world operational state.
3. The vector is injected directly into `process_telemetry_payload()`.
4. It passes through the exact same processing, ML models, and rule engine as physical MQTT packets.
5. The resulting analysis updates SQLite, the live cache, and all dashboard components.
6. The dashboard displays an explicit notification: `Scenario '<name>' successfully processed by AI pipeline`.
