# REST API Reference Manual

**Project Title:** AI-Based Smart Home Energy Consumption Forecasting & Wasteful Usage Detection  
**Document:** FastAPI REST Interface & Schema Reference  
**Base URL:** `http://0.0.0.0:8000` (or `http://localhost:8000`)  
**Interactive Docs:** `http://localhost:8000/docs` (Swagger UI), `http://localhost:8000/redoc` (ReDoc)  
**Author:** AI-for-IoT Capstone Team  
**Status:** Certified Release Candidate (Phase 3.4)

---

## 1. Endpoints Overview

| Method | Endpoint | Data Source | Primary Role |
| :--- | :--- | :--- | :--- |
| `GET` | `/health` | In-memory service state | System connectivity, MQTT status, model readiness |
| `GET` | `/latest` | Latest MQTT frame | Most recent raw telemetry frame received |
| `GET` | `/history` | SQLite database | Historical time-series telemetry with limit filter |
| `GET` | `/prediction` | Model 1 + Live Cache | Expected appliance load decomposition & error |
| `GET` | `/forecast` | Model 2 + Lag Buffer | Next interval (+2.5s) power forecast & trajectory |
| `GET` | `/anomaly` | Model 3 + Live Cache | Isolation Forest outlier flag and decision score |
| `GET` | `/waste` | Rule Engine + Live Cache | Explainable energy waste flags and avoidable Watts |
| `GET` | `/recommendation` | Rules + Recommendation Engine | Actionable optimization guidance and action items |
| `GET` | `/analysis` | Aggregated Pipeline | Unified comprehensive analytics response |
| `GET` | `/export/csv` | SQLite database dump | Downloads historical records as CSV file |
| `POST` | `/scenario` | Controlled Scenario Preset | Injects canonical test vector through AI pipeline |

---

## 2. Detailed Endpoint Documentation

### 1. `GET /health`
* **Purpose:** Heartbeat and operational readiness check.
* **Data Source:** In-memory background state and MQTT client connection handler.
* **Response Example:**
```json
{
  "status": "ok",
  "mqtt_connected": true,
  "models_loaded": true,
  "total_telemetry_records": 7325,
  "uptime_seconds": 1245.8
}
```

---

### 2. `GET /latest`
* **Purpose:** Retrieves the single most recent raw telemetry frame captured from the MQTT broker.
* **Data Source:** Live MQTT buffer (updated every 2.5s).
* **Response Example:**
```json
{
  "device_id": "esp32_energy_monitor",
  "uptime_ms": 142500,
  "temperature": 27.5,
  "humidity": 58.2,
  "occupancy": 1,
  "light_level": 420.0,
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

---

### 3. `GET /history`
* **Purpose:** Returns chronologically ordered historical telemetry records for time-series charts.
* **Data Source:** SQLite relational database (`data/smart_home.db`).
* **Query Parameters:**
  * `limit` (integer, optional, default: 100, max: 1000): Number of latest records to return.
* **Response Example:**
```json
[
  {
    "id": 7325,
    "timestamp": "2026-10-04T16:15:30.000000+00:00",
    "uptime_ms": 142500,
    "temperature": 27.5,
    "humidity": 58.2,
    "occupancy": 1,
    "light_level": 420.0,
    "ac": 1,
    "fan": 0,
    "tv": 1,
    "room_light": 0,
    "refrigerator": 1,
    "heater": 0,
    "microwave": 0,
    "power_w": 1770.0,
    "energy_wh": 145.2,
    "energy_kwh": 0.1452,
    "predicted_power_w": 1770.0,
    "prediction_error_w": 0.0,
    "is_anomaly": 0,
    "anomaly_score": 0.1245,
    "wasteful": 0,
    "severity": "NORMAL",
    "status_msg": "Nominal evening occupancy"
  }
]
```

---

### 4. `GET /prediction`
* **Purpose:** Returns Model 1 (Expected Load Estimation) baseline decomposition.
* **Data Source:** Model 1 regression model evaluated on latest telemetry frame.
* **Response Example:**
```json
{
  "actual_power_w": 1770,
  "predicted_power_w": 1770.0,
  "difference_w": 0.0,
  "percentage_difference": 0.0,
  "status": "normal",
  "model": "Linear Regression"
}
```

---

### 5. `GET /forecast`
* **Purpose:** Returns Model 2 short-term power forecast for the immediate next telemetry interval ($t+1$).
* **Data Source:** Model 2 lagged autoregressive pipeline using historical power buffer ($t-1, t-2, t-3$).
* **Response Example:**
```json
{
  "current_power_w": 1770.0,
  "forecast_power_w": 1772.5,
  "forecast_horizon": "next telemetry interval (2.5 seconds)",
  "forecast_error_w": 2.5,
  "expected_change_w": 2.5,
  "model": "Linear Regression (Lagged Autoregression)"
}
```

---

### 6. `GET /anomaly`
* **Purpose:** Returns Model 3 unsupervised anomaly detection diagnostics.
* **Data Source:** Isolation Forest model evaluated on the latest multi-channel feature vector.
* **Response Example:**
```json
{
  "is_anomaly": false,
  "anomaly_score": 0.1245,
  "severity": "NORMAL",
  "note": "Power consumption profile matches normal patterns"
}
```

---

### 7. `GET /waste`
* **Purpose:** Returns explainable rule engine evaluation.
* **Data Source:** Deterministic rule evaluation over current environmental context and appliance states.
* **Response Example:**
```json
{
  "wasteful": true,
  "reasons": [
    "Air Conditioner (1500W) is cooling an unoccupied home."
  ],
  "potential_waste_watts": 1500.0
}
```

---

### 8. `GET /recommendation`
* **Purpose:** Returns actionable, plain-English optimization guidance and prescriptive actions.
* **Data Source:** Recommendation synthesis engine.
* **Response Example:**
```json
{
  "recommendation": "Turn off Air Conditioner while the home is unoccupied to avoid unnecessary cooling draw.",
  "action_items": [
    "Switch off Air Conditioner"
  ],
  "potential_savings_watts": 1500.0
}
```

---

### 9. `GET /analysis`
* **Purpose:** Unified aggregate analysis consumed in a single round-trip by the Streamlit dashboard.
* **Data Source:** Combines latest telemetry, energy integration, Model 1, Model 2, Model 3, rules, and recommendations.
* **Response Structure:** Contains nested objects: `energy`, `sensors`, `appliances`, `forecast`, `ai`, `waste`, `severity`, `recommendation`, `action_items`.

---

### 10. `GET /export/csv`
* **Purpose:** Dumps all historical records from SQLite to CSV and streams the download file.
* **Data Source:** SQLite database export.
* **Headers:** `Content-Disposition: attachment; filename=energy_data.csv`.

---

### 11. `POST /scenario`
* **Purpose:** Controlled simulation and academic testing endpoint. Injects a predefined canonical telemetry vector through the real AI pipeline.
* **Crucial Note:** This is a **controlled demonstration endpoint** for evaluators and must **never** be misrepresented as live physical sensor telemetry.
* **Request Body:**
```json
{
  "scenario": "WASTEFUL"
}
```
* **Supported Scenario Presets:**
  * `NORMAL`: Nominal baseline household load ($245\text{ W}$, Occupied, no waste).
  * `WASTEFUL`: High-draw devices active in an unoccupied room ($1,790\text{ W}$, Vacant, rule violation flagged).
  * `HIGH LOAD`: Multiple high-draw devices active concurrently ($4,745\text{ W}$, Critical severity, grid stress).
  * `SPIKE`: Sudden activation of high-power space heater ($2,365\text{ W}$, Warning severity).
  * `LIVE TELEMETRY`: Resets simulation stream to real-time incoming MQTT feed.
* **Response Example:**
```json
{
  "status": "success",
  "scenario": "WASTEFUL",
  "analysis": { ... }
}
```
