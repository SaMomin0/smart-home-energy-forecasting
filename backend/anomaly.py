"""
Isolation Forest Unsupervised Anomaly Detection Layer.
Identifies multivariate operational anomalies and statistical power consumption outliers
using scikit-learn's IsolationForest.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
import joblib
import pandas as pd
import numpy as np

from backend.config import ISOLATION_FOREST_PATH, ISOLATION_META_PATH
from backend.features import ISOLATION_FEATURES, extract_features_single

logger = logging.getLogger("smart_home.anomaly")


class AnomalyDetector:
    """Encapsulates Isolation Forest model inference."""

    def __init__(self, model_path: Path = ISOLATION_FOREST_PATH, meta_path: Path = ISOLATION_META_PATH):
        self.model_path = model_path
        self.meta_path = meta_path
        self.model = None
        self.metadata: Dict[str, Any] = {}
        self.load_model()

    def load_model(self) -> bool:
        """Loads Isolation Forest model and metadata from disk."""
        if self.model_path.exists():
            try:
                self.model = joblib.load(self.model_path)
                logger.info(f"Loaded Isolation Forest model from {self.model_path}")
                if self.meta_path.exists():
                    with open(self.meta_path, "r", encoding="utf-8") as f:
                        self.metadata = json.load(f)
                return True
            except Exception as e:
                logger.error(f"Failed loading isolation forest model: {e}")
                self.model = None
                return False
        else:
            logger.warning(f"Isolation Forest model not found at {self.model_path}. Please train models first.")
            return False

    @property
    def is_loaded(self) -> bool:
        return self.model is not None

    def detect(self, telemetry_record: Dict[str, Any]) -> Dict[str, Any]:
        """
        Runs unsupervised anomaly detection on a telemetry record.

        Returns:
            Dict with:
                - is_anomaly (bool): True if statistical anomaly (-1), False if normal (1)
                - anomaly_score (float): Continuous score from decision_function (negative indicates anomaly)
                - raw_prediction (int): 1 (normal) or -1 (anomaly)
        """
        if not self.is_loaded:
            # Rule-of-thumb fallback: excessive power without active heavy devices
            power = int(telemetry_record.get("power_w", 0))
            is_anom = power > 3500
            return {
                "is_anomaly": is_anom,
                "anomaly_score": -0.5 if is_anom else 0.2,
                "raw_prediction": -1 if is_anom else 1,
                "model_status": "unloaded_fallback",
            }

        features_dict = extract_features_single(telemetry_record)
        feature_row = [features_dict[col] for col in ISOLATION_FEATURES]
        df_feat = pd.DataFrame([feature_row], columns=ISOLATION_FEATURES)

        raw_pred = int(self.model.predict(df_feat)[0]) # 1 for inlier, -1 for outlier
        score = float(self.model.decision_function(df_feat)[0]) # negative = anomalous

        is_anomaly = (raw_pred == -1)

        return {
            "is_anomaly": is_anomaly,
            "anomaly_score": round(score, 4),
            "raw_prediction": raw_pred,
            "contamination": self.metadata.get("contamination", 0.05),
            "model_status": "trained",
        }


# Global singleton instance
_anomaly_instance: Optional[AnomalyDetector] = None


def get_anomaly_detector() -> AnomalyDetector:
    global _anomaly_instance
    if _anomaly_instance is None:
        _anomaly_instance = AnomalyDetector()
    return _anomaly_instance
