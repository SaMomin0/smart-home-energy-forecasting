"""
Short-Term Power Forecasting Layer (Model 2).
Predicts the next power consumption value (t+1, next 2.5s interval) using historical power lags
(t-1, t-2, t-3) and environmental context via Scikit-Learn Linear Regression.
Completely separate from Model 1 (Expected Appliance Load Estimation).
"""

import json
import logging
from collections import deque
from pathlib import Path
from typing import Dict, Any, List, Optional
import joblib
import pandas as pd
import numpy as np

from backend.config import FORECAST_MODEL_PATH, FORECAST_META_PATH, TELEMETRY_INTERVAL_S
from backend.features import FORECAST_FEATURES, build_live_forecast_feature_row

logger = logging.getLogger("smart_home.forecaster")


class PowerForecaster:
    """Short-term power consumption forecaster using lagged historical telemetry."""

    def __init__(self, model_path: Path = FORECAST_MODEL_PATH, meta_path: Path = FORECAST_META_PATH):
        self.model_path = model_path
        self.meta_path = meta_path
        self.model = None
        self.metadata: Dict[str, Any] = {}
        # Sliding buffer of recent observed power readings
        self.power_history = deque(maxlen=20)
        self.load_model()

    def load_model(self) -> bool:
        """Loads serialized model and metadata from disk."""
        if self.model_path.exists():
            try:
                self.model = joblib.load(self.model_path)
                logger.info(f"Loaded Short-Term Forecasting model from {self.model_path}")
                if self.meta_path.exists():
                    with open(self.meta_path, "r", encoding="utf-8") as f:
                        self.metadata = json.load(f)
                return True
            except Exception as e:
                logger.error(f"Failed loading forecast model: {e}")
                self.model = None
                return False
        else:
            logger.warning(f"Forecasting model not found at {self.model_path}. Please train models first.")
            return False

    @property
    def is_loaded(self) -> bool:
        return self.model is not None

    def record_observation(self, power_w: float):
        """Appends observed power to rolling time-series window."""
        self.power_history.append(float(power_w))

    def forecast_next(
        self,
        current_record: Dict[str, Any],
        custom_history: Optional[List[float]] = None
    ) -> Dict[str, Any]:
        """
        Forecasts power for the next telemetry interval (t+1, e.g. 2.5s ahead)
        using historical power measurements (t-1, t-2, t-3) and environmental context.

        DATA LEAKAGE PREVENTION:
        The target for t+1 is unseen and strictly excluded from the feature matrix.
        """
        current_power = int(current_record.get("power_w", 0))

        # Use custom historical sequence or internal sliding buffer
        if custom_history is not None:
            history = list(custom_history)
        else:
            history = list(self.power_history)
            if not history or history[-1] != current_power:
                history.append(float(current_power))

        horizon_label = f"next telemetry interval ({TELEMETRY_INTERVAL_S}s)"

        if not self.is_loaded:
            # Fallback naive persistence forecast: Next step power ≈ current power
            return {
                "current_power_w": current_power,
                "forecast_power_w": float(current_power),
                "forecast_horizon": horizon_label,
                "forecast_error_w": 0.0,
                "expected_change_w": 0.0,
                "model": "Naive Persistence (Model Unloaded)",
                "status": "unloaded_fallback",
            }

        df_row = build_live_forecast_feature_row(history, current_record)
        pred_next = float(self.model.predict(df_row)[0])
        # Power is non-negative
        pred_next = max(0.0, round(pred_next, 2))

        expected_change = round(pred_next - current_power, 2)
        abs_diff = round(abs(expected_change), 2)

        return {
            "current_power_w": current_power,
            "forecast_power_w": pred_next,
            "forecast_horizon": horizon_label,
            "forecast_error_w": abs_diff,
            "expected_change_w": expected_change,
            "model": "Linear Regression (Lagged Autoregression)",
            "r2_score": self.metadata.get("metrics", {}).get("r2_score"),
            "status": "trained",
        }


# Global singleton forecaster instance
_forecaster_instance: Optional[PowerForecaster] = None


def get_forecaster() -> PowerForecaster:
    global _forecaster_instance
    if _forecaster_instance is None:
        _forecaster_instance = PowerForecaster()
    return _forecaster_instance
