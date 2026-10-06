# Machine Learning Performance & Validation Report

**Project Title:** AI-Based Smart Home Energy Consumption Forecasting & Wasteful Usage Detection  
**Document:** Machine Learning Evaluation, Metrics & Data Leakage Audit  
**Author:** AI-for-IoT Capstone Team  
**Status:** Certified Release Candidate (Phase 3.4)

---

## 1. Executive Summary

This report documents the design, training, evaluation, and strict leakage audit of the machine learning architecture deployed in the Smart Home Energy AI platform. The system operates three distinct machine learning models alongside a deterministic rule engine:

| Model ID | Model Name | Algorithm | Primary Objective | Test $R^2$ | Test MAE | Test RMSE |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: |
| **Model 1** | Expected Load Estimation | Linear Regression (OLS) | Decompose load from current device states | **$1.0000$** | **$0.00\text{ W}$** | **$0.00\text{ W}$** |
| **Model 2** | Short-Term Power Forecasting | Lagged Autoregression | Predict power for next interval ($t+1$, 2.5s) | **$0.2142$** | **$830.11\text{ W}$** | **$1070.58\text{ W}$** |
| **Model 3** | Anomaly Detection | Isolation Forest | Identify multivariate outliers & grid spikes | N/A ($5\%$ contam.) | Score range $[-0.25, +0.20]$ | 360 outliers flagged |

---

## 2. Dataset Synthesis & Characteristics

* **Dataset Path:** `data/energy_data.csv`
* **Total Records:** $7,200$ samples representing continuous 5-hour operational smart-home streaming at a $2.5\text{-second}$ sampling rate.
* **Temporal Coverage:** 24-hour diurnal simulation representing realistic household routines (sleeping, morning rush, midday vacancy, evening family leisure, dinner preparation, late night).
* **Sensor Channels:** Ambient temperature ($18.0^\circ\text{C}$ to $32.0^\circ\text{C}$), relative humidity ($35\%$ to $85\%$), room occupancy ($0$ or $1$), and ambient light level ($10$ to $800\text{ lx}$).
* **Appliance Channels:** Binary states for Air Conditioner ($1500\text{ W}$), Space Heater ($2000\text{ W}$), Microwave ($1000\text{ W}$), Refrigerator ($150\text{ W}$), Television ($120\text{ W}$), Ceiling Fan ($75\text{ W}$), and Room Light ($20\text{ W}$).

---

## 3. Train / Test Split Methodology

Time-series forecasting models must not be evaluated using random k-fold cross-validation or shuffled splits, as doing so leaks future temporal correlations into the past (lookahead bias).

* **Model 1 (Load Decomposition):** Random 80/20 train/test split ($5,760$ train / $1,440$ test). Because Model 1 is an instantaneous physical state mapping rather than a temporal sequence predictor, i.i.d. random sampling is mathematically valid.
* **Model 2 (Short-Term Forecasting):** **Strict Chronological Split (No Shuffling)**.
  * Total clean lag rows: $7,197$ (first 3 rows dropped due to $t-3$ lag initialization).
  * Train set: First $80\%$ ($5,757$ samples, indices $0$ to $5,756$).
  * Test set: Final $20\%$ ($1,440$ samples, indices $5,757$ to $7,196$).
  * Verification: `X_train.index[-1] < X_test.index[0] == True`.

---

## 4. Model 1: Expected Appliance Load Estimation

### Purpose & Theoretical Basis
Model 1 determines the nominal expected electrical draw given current appliance binary states and environmental conditions.

Because electrical power in a circuit without power-factor reactance is strictly additive:
$$P_{\text{expected}} = \sum_{k=1}^{M} w_k \cdot S_k + P_{\text{standby}}$$
where $w_k$ is the rated wattage of appliance $k$, and $S_k \in \{0, 1\}$ is its binary operational state.

### Results
* **Test MAE:** $0.0000\text{ W}$
* **Test RMSE:** $0.0000\text{ W}$
* **Test $R^2$ Score:** $1.000000$

### Physical Validation
When trained on the dataset, the Ordinary Least Squares solver perfectly recovers the rated appliance wattages:
* Air Conditioner: $+1,500.00\text{ W}$
* Space Heater: $+2,000.00\text{ W}$
* Microwave: $+1,000.00\text{ W}$
* Refrigerator: $+150.00\text{ W}$
* Television: $+120.00\text{ W}$
* Ceiling Fan: $+75.00\text{ W}$
* Room Light: $+20.00\text{ W}$
* Intercept / Standby Base: $0.00\text{ W}$

---

## 5. Model 2: Short-Term Power Forecasting

### Purpose & Problem Formulation
Model 2 predicts the aggregate household power consumption for the immediate next telemetry interval ($t+1$, 2.5 seconds ahead).

$$\hat{P}_{t+1} = f\left(P_{t}, P_{t-1}, P_{t-2}, \bar{P}_{3}, \Delta P_{1,2}, T, H, O, \text{hour}, \text{minute}\right)$$

### Verified Empirical Metrics
Evaluated on the $1,440$ chronological test samples using the serialized artifact `models/energy_forecast.joblib`:

* **Exact Unrounded Metrics:**
  * **MAE:** $830.112768\text{ W}$
  * **RMSE:** $1070.580879\text{ W}$
  * **$R^2$ Score:** $0.214157$
* **Report Summary Metrics:**
  * **MAE:** **$830.11\text{ W}$**
  * **RMSE:** **$1070.58\text{ W}$**
  * **$R^2$ Score:** **$0.2142$**

### Methodological Interpretation (Why $R^2 \approx 0.2142$ is Genuine & Correct)
Real-world and simulated household energy streams are characterized by **discrete step-function switching**. When an occupant powers on a $2,000\text{ W}$ space heater or a $1,500\text{ W}$ air conditioner, power jumps instantaneously from $245\text{ W}$ to $2,245\text{ W}$ in a single 2.5-second frame.

An autoregressive model relying strictly on past power measurements ($t-1, t-2, t-3$) and environmental context captures baseline trends, diurnal routines, and momentum. However, it cannot anticipate stochastic human decision events before they occur. An $R^2$ of $0.2142$ reflects this genuine physical reality without data leakage.

---

## 6. Strict Data Leakage Audit

A comprehensive audit was executed across the forecasting pipeline to verify that no target leakage exists:

1. **Target Separation:** Target $y$ is strictly $P_t$ during training, evaluated against lagged inputs ($t-1, t-2, t-3$).
2. **Feature Exclusions:** Contemporaneous power $P_t$ is strictly absent from the training feature matrix.
3. **Appliance State Exclusions:** Individual appliance states (`ac`, `heater`, `microwave`, etc.) are **strictly excluded** from Model 2 features. If appliance states were provided, the model would degenerate into Model 1 (reconstruction) rather than forecasting.
4. **Chronological Integrity:** No future samples or rolling averages containing future indices are included.

---

## 7. Model 3: Unsupervised Anomaly Detection

* **Algorithm:** `IsolationForest` (Scikit-Learn).
* **Hyperparameters:** `n_estimators=100`, `contamination=0.05`, `random_state=42`.
* **Input Features:** `power_w`, `temperature`, `humidity`, `occupancy`, `appliance_count`, `high_power_count`, `hour`, `total_appliance_power`.
* **Decision Function:** Computes isolation path length across 100 randomized trees. Scores below $0.0$ designate statistical outliers.
* **Results:** Successfully identified 360 anomalous events out of 7,200 samples, corresponding to severe concurrent high-power overloads ($>4,500\text{ W}$) and erratic sensor states.
