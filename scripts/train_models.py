"""
Model Training Script for Smart Home Energy AI (Phase 2).
Trains:
  1. Linear Regression Model: Estimates expected household power consumption from
     environmental states, appliance configurations, and interactions.
  2. Isolation Forest Model: Detects multivariate operational anomalies and high-demand spikes.
Saves serialized model artifacts (.joblib) and detailed audit metadata (.json).
"""

import sys
import json
import logging
from pathlib import Path
from datetime import datetime, timezone

# Ensure project root is on sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

import pandas as pd
import numpy as np
import joblib
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import IsolationForest
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

from backend.config import (
    CSV_PATH,
    MODELS_DIR,
    REGRESSION_MODEL_PATH,
    FORECAST_MODEL_PATH,
    ISOLATION_FOREST_PATH,
    REGRESSION_META_PATH,
    FORECAST_META_PATH,
    ISOLATION_META_PATH,
    RANDOM_STATE,
    TEST_SPLIT_SIZE,
    ISOLATION_CONTAMINATION,
    ISOLATION_N_ESTIMATORS,
)
from backend.features import (
    REGRESSION_FEATURES,
    ISOLATION_FEATURES,
    extract_features_df,
)

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
logger = logging.getLogger("smart_home.train")


def train_linear_regression(df_features: pd.DataFrame, df_raw: pd.DataFrame):
    """
    Trains and evaluates the Linear Regression expected power predictor.
    """
    logger.info("--- TRAINING LINEAR REGRESSION PREDICTOR ---")
    X = df_features[REGRESSION_FEATURES]
    y = df_raw["power_w"].astype(float)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=TEST_SPLIT_SIZE, random_state=RANDOM_STATE
    )

    logger.info(f"Dataset split: Train={len(X_train)} samples, Test={len(X_test)} samples")

    model = LinearRegression(fit_intercept=True)
    model.fit(X_train, y_train)

    # Predictions
    y_pred_train = model.predict(X_train)
    y_pred_test = model.predict(X_test)

    # Actual Scikit-Learn Metrics
    mae_test = float(mean_absolute_error(y_test, y_pred_test))
    # root_mean_squared_error support across sklearn versions:
    try:
        from sklearn.metrics import root_mean_squared_error
        rmse_test = float(root_mean_squared_error(y_test, y_pred_test))
    except ImportError:
        rmse_test = float(np.sqrt(mean_squared_error(y_test, y_pred_test)))

    r2_test = float(r2_score(y_test, y_pred_test))

    print("\n" + "="*60)
    print(" LINEAR REGRESSION EVALUATION METRICS (TEST SET)")
    print("="*60)
    print(f"  Target Variable           : power_w (Household Total Watts)")
    print(f"  Features Count            : {len(REGRESSION_FEATURES)}")
    print(f"  Mean Absolute Error (MAE) : {mae_test:.4f} W")
    print(f"  Root Mean Sq. Error (RMSE): {rmse_test:.4f} W")
    print(f"  R-Squared Score (R²)      : {r2_test:.6f}")
    print("="*60)

    # Feature Coefficients Inspection (Physical Validation)
    print("\nLEARNED FEATURE COEFFICIENTS (Physical Load Attribution):")
    coef_dict = {}
    for col, coef in zip(REGRESSION_FEATURES, model.coef_):
        coef_dict[col] = round(float(coef), 3)
        if any(app in col for app in ["ac", "heater", "microwave", "fan", "tv", "light", "refrigerator"]):
            print(f"  - {col:22s}: {coef:10.2f}")
    print(f"  - Intercept (Base Offset): {model.intercept_:10.2f}\n")

    # Serialize Model
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, REGRESSION_MODEL_PATH)
    logger.info(f"Saved Linear Regression model to: {REGRESSION_MODEL_PATH}")

    # Save Metadata
    metadata = {
        "model_type": "LinearRegression",
        "model_role": "Expected Appliance Load Estimation (Model 1)",
        "trained_at_utc": datetime.now(timezone.utc).isoformat(),
        "total_dataset_samples": len(df_raw),
        "train_samples": len(X_train),
        "test_samples": len(X_test),
        "features": REGRESSION_FEATURES,
        "metrics": {
            "mae_watts": round(mae_test, 4),
            "rmse_watts": round(rmse_test, 4),
            "r2_score": round(r2_test, 6),
        },
        "intercept": round(float(model.intercept_), 3),
        "coefficients": coef_dict,
        "methodology_note": (
            "Because electrical power in the virtual IoT simulator is strictly physical "
            "and additive (Sum of active appliance rated wattages), Linear Regression "
            "recovers the physical appliance wattage ratings as feature coefficients."
        ),
    }

    with open(REGRESSION_META_PATH, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)
    logger.info(f"Saved regression metadata to: {REGRESSION_META_PATH}")

    return model, metadata


def train_short_term_forecasting(df_raw: pd.DataFrame):
    """
    Trains and evaluates the Short-Term Energy Forecasting Model (Model 2).
    Predicts the next power reading using historical lagged measurements.
    
    STRICT DATA LEAKAGE PREVENTION:
      Target y is power_w at time t.
      Feature matrix X only contains information from t-1, t-2, t-3 and context.
      Train/Test split is strictly chronological (first 80% train, last 20% test).
    """
    logger.info("--- TRAINING SHORT-TERM POWER FORECASTING MODEL (MODEL 2) ---")
    from backend.config import FORECAST_MODEL_PATH, FORECAST_META_PATH
    from backend.features import FORECAST_FEATURES, build_lag_features_df

    X, y = build_lag_features_df(df_raw)

    # Chronological time-series split (no shuffling, no lookahead bias)
    split_idx = int(len(X) * (1.0 - TEST_SPLIT_SIZE))
    X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
    y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]

    logger.info(f"Chronological split: Train={len(X_train)} samples, Test={len(X_test)} samples")

    model = LinearRegression(fit_intercept=True)
    model.fit(X_train, y_train)

    y_pred_test = model.predict(X_test)

    mae_test = float(mean_absolute_error(y_test, y_pred_test))
    try:
        from sklearn.metrics import root_mean_squared_error
        rmse_test = float(root_mean_squared_error(y_test, y_pred_test))
    except ImportError:
        rmse_test = float(np.sqrt(mean_squared_error(y_test, y_pred_test)))
    r2_test = float(r2_score(y_test, y_pred_test))

    print("\n" + "="*60)
    print(" SHORT-TERM POWER FORECASTING EVALUATION METRICS (TEST SET)")
    print("="*60)
    print(f"  Model Type                : Linear Regression (Lagged Autoregression)")
    print(f"  Target Horizon            : Next Telemetry Interval (t+1, 2.5s ahead)")
    print(f"  Features Count            : {len(FORECAST_FEATURES)}")
    print(f"  Mean Absolute Error (MAE) : {mae_test:.4f} W")
    print(f"  Root Mean Sq. Error (RMSE): {rmse_test:.4f} W")
    print(f"  R-Squared Score (R²)      : {r2_test:.6f}")
    print("="*60)

    print("\nFORECASTING FEATURE COEFFICIENTS:")
    coef_dict = {}
    for col, coef in zip(FORECAST_FEATURES, model.coef_):
        coef_dict[col] = round(float(coef), 4)
        print(f"  - {col:22s}: {coef:10.4f}")
    print(f"  - Intercept (Base Offset): {model.intercept_:10.4f}\n")

    # Serialize Model
    joblib.dump(model, FORECAST_MODEL_PATH)
    logger.info(f"Saved Forecasting model to: {FORECAST_MODEL_PATH}")

    metadata = {
        "model_type": "LinearRegression",
        "model_role": "Short-Term Energy Forecasting (Model 2)",
        "horizon": "next telemetry interval (2.5 seconds)",
        "trained_at_utc": datetime.now(timezone.utc).isoformat(),
        "total_samples": len(X),
        "train_samples": len(X_train),
        "test_samples": len(X_test),
        "split_method": "Chronological (No Shuffle)",
        "features": FORECAST_FEATURES,
        "metrics": {
            "mae_watts": round(mae_test, 4),
            "rmse_watts": round(rmse_test, 4),
            "r2_score": round(r2_test, 6),
        },
        "coefficients": coef_dict,
        "intercept": round(float(model.intercept_), 4),
        "methodology_note": (
            "Model 2 forecasts future household power based on historical measurements "
            "(t-1, t-2, t-3) and environmental context. No target data leakage exists "
            "because the current power is strictly excluded from input features."
        ),
    }

    with open(FORECAST_META_PATH, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)
    logger.info(f"Saved forecasting metadata to: {FORECAST_META_PATH}")

    return model, metadata


def train_isolation_forest(df_features: pd.DataFrame, df_raw: pd.DataFrame):
    """
    Trains and saves the Isolation Forest unsupervised anomaly detector.
    """
    logger.info("--- TRAINING ISOLATION FOREST ANOMALY DETECTOR ---")
    X = df_features[ISOLATION_FEATURES]

    model = IsolationForest(
        n_estimators=ISOLATION_N_ESTIMATORS,
        contamination=ISOLATION_CONTAMINATION,
        random_state=RANDOM_STATE,
        n_jobs=-1,
    )
    model.fit(X)

    # Evaluate predictions on the training corpus
    preds = model.predict(X) # 1 = inlier (normal), -1 = outlier (anomaly)
    scores = model.decision_function(X) # lower score = more anomalous

    anomaly_count = int(np.sum(preds == -1))
    anomaly_pct = round((anomaly_count / len(preds)) * 100.0, 2)

    print("\n" + "="*60)
    print(" ISOLATION FOREST ANOMALY DETECTOR SUMMARY")
    print("="*60)
    print(f"  Contamination Setting     : {ISOLATION_CONTAMINATION} ({ISOLATION_CONTAMINATION*100:.1f}%)")
    print(f"  Estimator Trees (n_est)   : {ISOLATION_N_ESTIMATORS}")
    print(f"  Detected Outliers         : {anomaly_count} / {len(preds)} ({anomaly_pct}%)")
    print(f"  Score Min / Max           : {scores.min():.4f} / {scores.max():.4f}")
    print("="*60 + "\n")

    # Serialize Model
    joblib.dump(model, ISOLATION_FOREST_PATH)
    logger.info(f"Saved Isolation Forest model to: {ISOLATION_FOREST_PATH}")

    # Save Metadata
    metadata = {
        "model_type": "IsolationForest",
        "trained_at_utc": datetime.now(timezone.utc).isoformat(),
        "total_samples": len(X),
        "contamination": ISOLATION_CONTAMINATION,
        "n_estimators": ISOLATION_N_ESTIMATORS,
        "features": ISOLATION_FEATURES,
        "detected_anomalies_count": anomaly_count,
        "detected_anomalies_pct": anomaly_pct,
        "score_range": {
            "min": round(float(scores.min()), 4),
            "max": round(float(scores.max()), 4),
            "mean": round(float(scores.mean()), 4),
        },
    }

    with open(ISOLATION_META_PATH, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)
    logger.info(f"Saved isolation forest metadata to: {ISOLATION_META_PATH}")

    return model, metadata


def main():
    print("===================================================================")
    print("  AI FOR IOT CAPSTONE: PHASE 2 MODEL TRAINING PIPELINE             ")
    print("===================================================================")

    if not CSV_PATH.exists():
        logger.error(f"Dataset not found at {CSV_PATH}. Running generate_training_data first...")
        from scripts.generate_training_data import main as run_generator
        run_generator()

    logger.info(f"Loading training data from {CSV_PATH}...")
    df_raw = pd.read_csv(CSV_PATH)
    logger.info(f"Loaded {len(df_raw)} records. Extracting engineered features...")

    # Extract all engineered features
    df_features = extract_features_df(df_raw)

    # 1. Train Expected Power Linear Regression (Model 1)
    train_linear_regression(df_features, df_raw)

    # 2. Train Short-Term Power Forecaster (Model 2 - Lagged Autoregression)
    train_short_term_forecasting(df_raw)

    # 3. Train Isolation Forest Anomaly Detector (Model 3)
    train_isolation_forest(df_features, df_raw)

    print("\n[COMPLETE] Phase 2 AI Model Training Finished Successfully.")
    print(f"  - Model 1 (Expected Load): {REGRESSION_MODEL_PATH}")
    print(f"  - Model 2 (Forecasting)  : {FORECAST_MODEL_PATH}")
    print(f"  - Model 3 (Anomaly)      : {ISOLATION_FOREST_PATH}")
    print("===================================================================\n")


if __name__ == "__main__":
    main()
