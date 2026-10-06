"""
Pydantic Schemas for Request Validation and API Responses.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator


class TelemetryInput(BaseModel):
    """Raw incoming telemetry payload from Wokwi ESP32 via MQTT."""
    uptime_ms: Optional[int] = Field(default=0, description="Uptime in milliseconds")
    temperature: float = Field(..., description="Ambient temperature in Celsius")
    humidity: float = Field(..., description="Relative humidity percentage")
    occupancy: int = Field(..., description="Binary occupancy (0=Vacant, 1=Occupied)")
    light_level: int = Field(..., description="Ambient light level in lux or ADC value")
    
    # 7 Appliance states (0 = OFF, 1 = ON)
    ac: int = Field(..., description="Air Conditioner state (0/1)")
    fan: int = Field(..., description="Ceiling Fan state (0/1)")
    tv: int = Field(..., description="Television state (0/1)")
    room_light: int = Field(..., description="Room Light state (0/1)")
    refrigerator: int = Field(..., description="Refrigerator state (0/1)")
    heater: int = Field(..., description="Space Heater state (0/1)")
    microwave: int = Field(..., description="Microwave state (0/1)")
    
    power_w: int = Field(..., description="Total instantaneous power in Watts")
    energy_kwh: Optional[float] = Field(default=0.0, description="Cumulative energy from IoT node")
    waste_flag: Optional[int] = Field(default=0, description="IoT-level waste flag")
    high_load_flag: Optional[int] = Field(default=0, description="IoT-level high load flag")
    status_msg: Optional[str] = Field(default="Normal", description="Status note")

    @field_validator("temperature")
    @classmethod
    def validate_temp(cls, v: float) -> float:
        if v < -30.0 or v > 80.0:
            raise ValueError(f"Temperature {v} C is outside realistic household range (-30 to 80)")
        return v

    @field_validator("humidity")
    @classmethod
    def validate_humidity(cls, v: float) -> float:
        if v < 0.0 or v > 100.0:
            raise ValueError(f"Humidity {v}% must be between 0 and 100")
        return v

    @field_validator("occupancy", "ac", "fan", "tv", "room_light", "refrigerator", "heater", "microwave")
    @classmethod
    def validate_binary(cls, v: int) -> int:
        if v not in (0, 1):
            raise ValueError("State must be binary (0 or 1)")
        return v

    @field_validator("power_w")
    @classmethod
    def validate_power(cls, v: int) -> int:
        if v < 0:
            raise ValueError("Power cannot be negative")
        return v


class SensorsData(BaseModel):
    temperature: float
    humidity: float
    occupancy: int
    light_level: int


class AppliancesData(BaseModel):
    ac: int
    fan: int
    tv: int
    room_light: int
    refrigerator: int
    heater: int
    microwave: int


class EnergyData(BaseModel):
    current_power_w: int
    predicted_power_w: float
    difference_w: float
    percentage_difference: float
    energy_wh: float
    energy_kwh: float


class AIData(BaseModel):
    anomaly: bool
    anomaly_score: float


class WasteData(BaseModel):
    wasteful: bool
    reasons: List[str]


class ForecastData(BaseModel):
    """Short-term power forecast for the next interval (Model 2)."""
    predicted_next_power_w: float
    forecast_horizon: str
    expected_change_w: float
    model: str = "Linear Regression"


class AnalysisResponse(BaseModel):
    """Unified comprehensive response for GET /analysis."""
    timestamp: str
    sensors: SensorsData
    appliances: AppliancesData
    energy: EnergyData
    ai: AIData
    waste: WasteData
    severity: str
    recommendation: str
    forecast: Optional[ForecastData] = None


class PredictionResponse(BaseModel):
    """Response for GET /prediction (Model 1: Expected Load Estimation)."""
    actual_power_w: int
    predicted_power_w: float
    difference_w: float
    percentage_difference: float
    model_r2: Optional[float] = None


class ForecastResponse(BaseModel):
    """Response for GET /forecast (Model 2: Short-Term Power Forecasting)."""
    current_power_w: int
    forecast_power_w: float
    forecast_horizon: str
    forecast_error_w: float
    expected_change_w: float = 0.0
    model: str = "Linear Regression"


class AnomalyResponse(BaseModel):
    """Response for GET /anomaly."""
    is_anomaly: bool
    anomaly_score: float
    severity: str
    note: str


class WasteResponse(BaseModel):
    """Response for GET /waste."""
    wasteful: bool
    reasons: List[str]
    potential_waste_watts: int


class RecommendationResponse(BaseModel):
    """Response for GET /recommendation."""
    severity: str
    recommendation: str
    actions: List[str]


class HealthResponse(BaseModel):
    """Response for GET /health."""
    status: str
    mqtt_connected: bool
    models_loaded: bool
    total_telemetry_records: int
    uptime_seconds: float


class ScenarioRequest(BaseModel):
    """Request for POST /scenario."""
    scenario: str = Field(..., description="Scenario preset: NORMAL, WASTEFUL, HIGH LOAD, SPIKE, or LIVE TELEMETRY")
