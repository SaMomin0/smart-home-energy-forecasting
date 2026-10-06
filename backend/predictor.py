"""
Linear Regression Expected Household Power Predictor.
Estimates the expected power consumption based on current household environmental conditions,
appliance operational states, and engineered interaction features.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
import joblib
import pandas as pd
import numpy as np

from backend.config import REGRESSION_MODEL_PATH, REGRESSION_META_PATH
from backend.features import REGRESSION_FEATURES, extract_features_single

logger = logging.getLogger("smart_home.predictor")


class PowerPredictor:
    """Encapsulates Linear Regression inference and feature extraction."""

    def __init__(self, model_path: Path = REGRESSION_MODEL_PATH, meta_path: Path = REGRESSION_META_PATH):
        self.model_path = model_path
        self.meta_path = meta_path
        self.model = None
        self.metadata: Dict[str, Any] = {}
        self.load_model()

    def load_model(self) -> bool:
        """Loads model and metadata from disk if available."""
        if self.model_path.exists():
            try:
                self.model = joblib.load(self.model_path)
                logger.info(f"Loaded Linear Regression model from {self.model_path}")
                if self.meta_path.exists():
                    with open(self.meta_path, "r", encoding="utf-8") as f:
                        self.metadata = json.load(f)
                return True
            except Exception as e:
                logger.error(f"Failed loading regression model: {e}")
                self.model = None
                return False
        else:
            logger.warning(f"Linear Regression model not found at {self.model_path}. Please train models first.")
            return False

    @property
    def is_loaded(self) -> bool:
        return self.model is not None

    def predict(self, telemetry_record: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculates expected power consumption for a given telemetry record.
        Returns:
            Dict containing actual_power_w, predicted_power_w, difference_w, and percentage_difference.
        """
        actual_power = int(telemetry_record.get("power_w", 0))

        if not self.is_loaded:
            # Fallback estimation if model has not been trained yet
            # Uses physical appliance wattage sum as a baseline default
            features = extract_features_single(telemetry_record)
            baseline = float(features["total_appliance_power"])
            diff = actual_power - baseline
            pct_diff = round((diff / (baseline + 1e-5)) * 100.0, 2)
            return {
                "actual_power_w": actual_power,
                "predicted_power_w": round(baseline, 2),
                "difference_w": round(diff, 2),
                "percentage_difference": pct_diff,
                "model_status": "unloaded_fallback",
            }

        # Extract features for regression
        features_dict = extract_features_single(telemetry_record)
        feature_row = [features_dict[col] for col in REGRESSION_FEATURES]
        df_feat = pd.DataFrame([feature_row], columns=REGRESSION_FEATURES)

        predicted_val = float(self.model.predict(df_feat)[0])
        # Power cannot physically be negative in home consumption
        predicted_val = max(0.0, round(predicted_val, 2))

        difference = round(actual_power - predicted_val, 2)
        base = max(predicted_val, 10.0)
        pct_diff = round((difference / base) * 100.0, 2)

        return {
            "actual_power_w": actual_power,
            "predicted_power_w": predicted_val,
            "difference_w": difference,
            "percentage_difference": pct_diff,
            "model_r2": self.metadata.get("r2_score"),
            "model_status": "trained",
        }


# Global singleton instance
_predictor_instance: Optional[PowerPredictor] = None


def get_predictor() -> PowerPredictor:
    global _predictor_instance
    if _predictor_instance is None:
        _predictor_instance = PowerPredictor()
    return _predictor_instance
