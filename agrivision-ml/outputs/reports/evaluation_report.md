# AgriVision AI – Model Evaluation & Performance Report
**Project:** AgriVision AI – Agricultural Price Intelligence & Demand Forecasting  
**Event:** Build Beyond'26, BMS College of Engineering  
**Role:** Member 2 – AI & Data Science  
**Target Crop:** Tomato (*Solanum lycopersicum*) – Karnataka APMC Mandis  

---

## 1. Executive Summary
This report documents the rigorous evaluation of the machine learning modules powering AgriVision AI. 
To ensure transparency, prevent future lookahead bias, and safeguard against data leakage, all time-series 
evaluations were executed using **strict chronological splitting** rather than random cross-validation.

---

## 2. Dataset Overview & Provenance
- **Dataset Source:** SYNTHETIC DEMO DATA (Karnataka APMC Simulation for Hackathon)
- **Synthetic Data Flag:** `True`
- **Total Records:** 4386 observations
- **Date Range:** 2024-01-01 to 2025-12-31
- **Karnataka APMC Markets Covered:** Bangalore, Belagavi, Chikkaballapur, Kolar, Mysuru, Ramanagara
- **Data Unit:** INR (₹) per Quintal (100 kg) for modal prices; Quintals for wholesale arrivals.

---

## 3. Chronological Split Architecture
To mimic real-world deployment where tomorrow's prices are unknown, data was partitioned along the time dimension:
- **Training Set (70%):** 3066 rows (Initial historical window)
- **Validation Set (15%):** 660 rows (Model tuning & selection)
- **Test Set (15%):** 660 rows (Strict out-of-sample final evaluation)

---

## 4. Agricultural Price Prediction: Model Benchmarking

### Performance Metrics Comparison
| Model Architecture | Validation MAE (₹) | Validation RMSE (₹) | Validation MAPE (%) | Test MAE (₹) | Test RMSE (₹) | Test MAPE (%) | Test R² Score |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Historical 7-Day Baseline** | ₹159.0 | ₹200.96 | 6.52% | ₹127.56 | ₹168.82 | 12.36% | 0.9041 |
| **Random Forest Regressor** | ₹157.05 | ₹195.3 | 6.39% | ₹86.13 | ₹118.65 | 8.06% | 0.9526 |
| **Gradient Boosting Regressor** | ₹156.42 | ₹195.3 | 6.38% | ₹88.09 | ₹122.08 | 8.18% | 0.9499 |

### Champion Model Selection
- **Selected Champion Model:** `GradientBoosting`
- **Test MAE:** ₹88.09/quintal
- **Test MAPE:** 8.18%
- **Test R²:** 0.9499
- **Empirical Residual Std:** ±₹195.14/quintal

The selected model demonstrates significant predictive gains over the lag baseline by successfully capturing 
cross-market momentum, day-of-week volume contractions (e.g. Sunday APMC closures), and seasonal transitions.

---

## 5. Crop Demand Forecasting & Supply Proxy Evaluation
- **Classification Objective:** 7-Day Forward Market Absorption Trend (`Increasing`, `Decreasing`, `Stable`).
- **Test Accuracy:** 49.09%
- **Evaluation Classes:** Decreasing, Increasing, Stable
- **Architectural Notice:** Mandi arrivals quantify *physical wholesale supply throughput*, not end-consumer retail ingestion. 
The module formulates an absorption pressure index from price elasticity and volume velocity.

---

## 6. Real-World Limitations
1. **Supply-Demand Proxy Distinction:** APMC registers record truck arrivals and clearing bids. True consumer retail demand across Bengaluru grocery channels is unobserved.
2. **Extreme Climate Shocks:** Cloudbursts or flash floods impacting the Kolar-Chikkaballapur tomato belt cause non-linear price spikes that historical regression models may under-project without satellite imagery feeds.
3. **Interstate Inflow:** Karnataka tomato prices are heavily influenced by interstate dispatches to Tamil Nadu and Andhra Pradesh.

---

## 7. Recommendations for Post-Hackathon Enhancement
1. **Satellite Remote Sensing Integration:** Ingest Sentinel-2 NDVI vegetative health indices for major Karnataka crop clusters.
2. **Weather API Hook:** Ingest IMD rainfall alerts and heatwave warnings into feature engineering.
3. **Multi-Crop Generalization:** Extend the modular architecture from Tomato to Onion, Potato, and Ragi.
