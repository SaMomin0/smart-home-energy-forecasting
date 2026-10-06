"""
FastAPI REST API Layer for Phase 2 AI Smart Home Backend.
Serves real-time telemetry, model predictions, anomaly scores, waste rules,
and dynamic recommendations for the downstream Phase 3 Dashboard.
"""

import time
import logging
from contextlib import asynccontextmanager
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse

from backend.config import CSV_PATH
from backend.database import (
    init_db,
    get_latest_telemetry,
    get_history,
    get_telemetry_count,
    export_to_csv,
)
from backend.predictor import get_predictor
from backend.forecaster import get_forecaster
from backend.anomaly import get_anomaly_detector
from backend.collector import (
    get_collector,
    get_cached_latest,
    get_cached_analysis,
    is_mqtt_connected,
    process_telemetry_payload,
)
from backend.schemas import (
    HealthResponse,
    AnalysisResponse,
    PredictionResponse,
    ForecastResponse,
    AnomalyResponse,
    WasteResponse,
    RecommendationResponse,
    TelemetryInput,
    ScenarioRequest,
)

logger = logging.getLogger("smart_home.api")
START_TIME = time.time()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initializes database and automatically spins up the MQTT collector in the background."""
    logger.info("[STARTUP] Initializing Smart Home AI Backend...")
    init_db()
    # Preload models
    get_predictor()
    get_forecaster()
    get_anomaly_detector()

    # Start background MQTT collector
    collector = get_collector()
    collector.start_background()
    logger.info("[STARTUP] MQTT Background Collector initialized.")
    yield
    # Teardown
    logger.info("[SHUTDOWN] Stopping MQTT Background Collector...")
    collector.stop()


app = FastAPI(
    title="Smart Home Energy AI Backend (Phase 2)",
    description=(
        "AI-Based Smart Home Energy Consumption Forecasting & Wasteful Usage Detection. "
        "Consumes ESP32/Wokwi MQTT telemetry, runs Linear Regression expected power estimation, "
        "Isolation Forest anomaly detection, and explainable waste rule synthesis."
    ),
    version="2.0.0",
    lifespan=lifespan,
)

# Enable CORS for Phase 3 Streamlit Dashboard or any frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _get_current_analysis_or_db() -> Dict[str, Any]:
    """Helper to fetch analysis from live in-memory cache, or compute from latest SQLite row."""
    cached = get_cached_analysis()
    if cached is not None:
        return cached

    # Fallback to latest record stored in SQLite
    row = get_latest_telemetry()
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No telemetry available yet. Ensure Wokwi simulation is running or generate synthetic data.",
        )

    # Reconstruct from DB row
    forecaster = get_forecaster()
    forecast_res = forecaster.forecast_next(dict(row))

    return {
        "timestamp": row["timestamp"],
        "sensors": {
            "temperature": row["temperature"],
            "humidity": row["humidity"],
            "occupancy": row["occupancy"],
            "light_level": row["light_level"],
        },
        "appliances": {
            "ac": row["ac"],
            "fan": row["fan"],
            "tv": row["tv"],
            "room_light": row["room_light"],
            "refrigerator": row["refrigerator"],
            "heater": row["heater"],
            "microwave": row["microwave"],
        },
        "energy": {
            "current_power_w": row["power_w"],
            "predicted_power_w": row["predicted_power_w"] or row["power_w"],
            "difference_w": row["prediction_error_w"] or 0.0,
            "percentage_difference": round(
                ((row["prediction_error_w"] or 0.0) / max(row["power_w"], 1)) * 100.0, 2
            ),
            "energy_wh": row["energy_wh"],
            "energy_kwh": row["energy_kwh"],
        },
        "forecast": {
            "predicted_next_power_w": forecast_res["forecast_power_w"],
            "forecast_horizon": forecast_res["forecast_horizon"],
            "expected_change_w": forecast_res["expected_change_w"],
            "model": forecast_res["model"],
        },
        "ai": {
            "anomaly": bool(row["is_anomaly"]),
            "anomaly_score": row["anomaly_score"],
        },
        "waste": {
            "wasteful": bool(row["wasteful"]),
            "reasons": [row["status_msg"]] if row["wasteful"] and row["status_msg"] else [],
            "potential_waste_watts": 0,
        },
        "severity": row["severity"] or "NORMAL",
        "recommendation": row["recommendation"] or "System operating normally.",
        "action_items": [],
    }


# =============================================================================
# API ENDPOINTS
# =============================================================================

@app.get("/health", response_model=HealthResponse, tags=["Health"])
def get_health():
    """Returns system status, MQTT connectivity, model readiness, and total records count."""
    predictor = get_predictor()
    forecaster = get_forecaster()
    detector = get_anomaly_detector()
    models_ready = predictor.is_loaded and forecaster.is_loaded and detector.is_loaded

    return HealthResponse(
        status="ok",
        mqtt_connected=is_mqtt_connected(),
        models_loaded=models_ready,
        total_telemetry_records=get_telemetry_count(),
        uptime_seconds=round(time.time() - START_TIME, 1),
    )


@app.get("/latest", tags=["Telemetry"])
def get_latest():
    """Returns the most recent raw and processed telemetry packet."""
    live = get_cached_latest()
    if live:
        return live

    db_row = get_latest_telemetry()
    if not db_row:
        raise HTTPException(status_code=404, detail="No telemetry records recorded yet.")
    return db_row


@app.get("/history", tags=["Telemetry"])
def get_historical_telemetry(limit: int = Query(default=50, ge=1, le=1000)):
    """Returns a reverse-chronological list of recent telemetry samples."""
    return get_history(limit=limit)


@app.get("/prediction", response_model=PredictionResponse, tags=["AI Inference"])
def get_prediction():
    """
    Model 1: Returns Linear Regression expected current appliance load estimation
    based on current active appliances and environmental conditions.
    """
    analysis = _get_current_analysis_or_db()
    energy = analysis["energy"]
    predictor = get_predictor()

    return PredictionResponse(
        actual_power_w=energy["current_power_w"],
        predicted_power_w=energy["predicted_power_w"],
        difference_w=energy["difference_w"],
        percentage_difference=energy["percentage_difference"],
        model_r2=predictor.metadata.get("metrics", {}).get("r2_score"),
    )


@app.get("/forecast", response_model=ForecastResponse, tags=["AI Inference"])
def get_forecast():
    """
    Model 2: Returns Short-Term Power Forecast for the next telemetry interval (t+1, 2.5s ahead)
    using historical power measurements (t-1, t-2, t-3) and environmental context.
    Completely separate from Model 1 expected load estimation.
    """
    analysis = _get_current_analysis_or_db()
    forecast_data = analysis.get("forecast")
    current_w = analysis["energy"]["current_power_w"]

    if not forecast_data:
        forecaster = get_forecaster()
        latest_telemetry = get_latest_telemetry()
        forecast_res = forecaster.forecast_next(latest_telemetry or {})
        return ForecastResponse(
            current_power_w=forecast_res["current_power_w"],
            forecast_power_w=forecast_res["forecast_power_w"],
            forecast_horizon=forecast_res["forecast_horizon"],
            forecast_error_w=forecast_res["forecast_error_w"],
            expected_change_w=forecast_res["expected_change_w"],
            model=forecast_res["model"],
        )

    next_w = float(forecast_data["predicted_next_power_w"])
    expected_change = float(forecast_data.get("expected_change_w", next_w - current_w))
    abs_err = round(abs(next_w - current_w), 2)

    return ForecastResponse(
        current_power_w=current_w,
        forecast_power_w=next_w,
        forecast_horizon=forecast_data["forecast_horizon"],
        forecast_error_w=abs_err,
        expected_change_w=expected_change,
        model=forecast_data.get("model", "Linear Regression"),
    )


@app.get("/anomaly", response_model=AnomalyResponse, tags=["AI Inference"])
def get_anomaly():
    """Returns Isolation Forest unsupervised anomaly detection results and anomaly score."""
    analysis = _get_current_analysis_or_db()
    ai = analysis["ai"]
    severity = analysis["severity"]

    note = "Unsupervised Isolation Forest detected statistical outlier" if ai["anomaly"] else "Power consumption profile matches normal patterns"
    return AnomalyResponse(
        is_anomaly=ai["anomaly"],
        anomaly_score=ai["anomaly_score"],
        severity=severity,
        note=note,
    )


@app.get("/waste", response_model=WasteResponse, tags=["Rules Engine"])
def get_waste():
    """Returns explainable rule-based wasteful usage detection status, reasons, and wasted watts."""
    analysis = _get_current_analysis_or_db()
    waste = analysis["waste"]

    return WasteResponse(
        wasteful=waste["wasteful"],
        reasons=waste["reasons"],
        potential_waste_watts=waste.get("potential_waste_watts", 0),
    )


@app.get("/recommendation", response_model=RecommendationResponse, tags=["Recommendations"])
def get_recommendation():
    """Returns dynamic, human-interpretable energy-saving recommendations and action items."""
    analysis = _get_current_analysis_or_db()
    return RecommendationResponse(
        severity=analysis["severity"],
        recommendation=analysis["recommendation"],
        actions=analysis.get("action_items", []),
    )


@app.get("/analysis", response_model=AnalysisResponse, tags=["Unified Analysis"])
def get_complete_analysis():
    """
    Master unified endpoint consumed by Phase 3 Dashboard.
    Provides complete state: Sensors, Appliances, Energy, Regression, Isolation Forest,
    Waste Rules, Severity, and Dynamic Recommendations.
    """
    return _get_current_analysis_or_db()


@app.post("/ingest", tags=["Ingest"])
def ingest_manual_telemetry(payload: TelemetryInput):
    """
    Allows submitting telemetry directly via HTTP POST for testing and integration verification.
    Processed through the exact same AI and rules pipeline as MQTT messages.
    """
    import json
    analysis = process_telemetry_payload(json.dumps(payload.model_dump()))
    if not analysis:
        raise HTTPException(status_code=400, detail="Failed processing telemetry payload.")
    return {"status": "success", "analysis": analysis}


@app.post("/scenario", tags=["Simulation"])
def trigger_scenario(req: ScenarioRequest):
    """
    Triggers a household scenario preset (NORMAL, WASTEFUL, HIGH LOAD, SPIKE, LIVE TELEMETRY).
    Processes canonical firmware telemetry through the genuine AI and rule pipeline.
    """
    import json
    name = req.scenario.strip().upper().replace("_", " ")

    if name in ("LIVE TELEMETRY", "LIVE"):
        return {
            "status": "success",
            "scenario": "LIVE TELEMETRY",
            "message": "Live telemetry streaming active."
        }

    # Canonical scenario payloads matching firmware simulator presets
    if name == "NORMAL":
        payload = {
            "uptime_ms": int(time.time() * 1000) % 100000000,
            "temperature": 24.5,
            "humidity": 50.0,
            "occupancy": 1,
            "light_level": 150,
            "ac": 0, "fan": 1, "tv": 0, "room_light": 1, "refrigerator": 1, "heater": 0, "microwave": 0,
            "power_w": 245,
            "status_msg": "Normal household activity"
        }
    elif name in ("WASTEFUL", "WASTE"):
        payload = {
            "uptime_ms": int(time.time() * 1000) % 100000000,
            "temperature": 29.5,
            "humidity": 58.0,
            "occupancy": 0, # Vacant
            "light_level": 600,
            "ac": 1, "fan": 0, "tv": 1, "room_light": 1, "refrigerator": 1, "heater": 0, "microwave": 0,
            "power_w": 1790,
            "status_msg": "AC & TV active in vacant room"
        }
    elif name in ("HIGH LOAD", "HIGH_LOAD"):
        payload = {
            "uptime_ms": int(time.time() * 1000) % 100000000,
            "temperature": 26.0,
            "humidity": 52.0,
            "occupancy": 1,
            "light_level": 450,
            "ac": 1, "fan": 1, "tv": 0, "room_light": 1, "refrigerator": 1, "heater": 1, "microwave": 1,
            "power_w": 4745,
            "status_msg": "Simultaneous high-draw heating and cooling appliances"
        }
    elif name == "SPIKE":
        payload = {
            "uptime_ms": int(time.time() * 1000) % 100000000,
            "temperature": 25.0,
            "humidity": 51.0,
            "occupancy": 1,
            "light_level": 400,
            "ac": 0, "fan": 1, "tv": 1, "room_light": 1, "refrigerator": 1, "heater": 1, "microwave": 0,
            "power_w": 2365,
            "status_msg": "Sudden space heater power surge (+2000W spike)"
        }
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported scenario preset: {req.scenario}")

    analysis = process_telemetry_payload(json.dumps(payload))
    if not analysis:
        raise HTTPException(status_code=500, detail="Failed to evaluate scenario in ML pipeline.")

    return {
        "status": "success",
        "scenario": name,
        "analysis": analysis,
    }


@app.get("/export/csv", tags=["Data Export"])
def export_dataset_csv():
    """Dumps all SQLite historical telemetry to CSV and returns the file for download."""
    count = export_to_csv()
    if not CSV_PATH.exists():
        raise HTTPException(status_code=404, detail="No data available to export.")
    return FileResponse(
        path=str(CSV_PATH),
        filename="energy_data.csv",
        media_type="text/csv",
    )
