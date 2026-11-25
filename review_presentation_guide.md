# Milestone 2 Review Presentation Guide
**Course:** Community Project (Mini Project) — `BCP308` (III Semester)  
**Project Title:** Next-Day PM2.5 Forecast (Project 34)  
**Batch / Section:** Batch B-12 / AI-B  
**Institution:** Dayananda Sagar College of Engineering  

---

## 1. Quick Review Overview (Where You Stand Today)

- **Official Academic Milestone:** Milestone 2 (Nov 16 – Nov 30: ML Model Development & Tuning).
- **Hardware & Data:** UCI Beijing Multi-Site Air Quality Dataset (35,064 hourly records per station, 420,768 records total).
- **Goal for Today's Review:** Demonstrate that you have moved beyond proposal/theory:
  1. Complete real data cleaning & imputation pipeline (**Milestone 1 completed** — 925 missing values imputed).
  2. Feature engineering (24-hour temporal lags, rolling averages, cyclical time encoding).
  3. Strict **Persistence Baseline Model** ($y_t = y_{t-24}$) established and evaluated ($\text{RMSE} = 89.95$, $R^2 = -0.14$).
  4. Trained **Machine Learning Model** (Histogram Gradient Boosted Decision Trees) beating the baseline by **54.1% reduction in RMSE** ($\text{RMSE} = 41.27$, $R^2 = 0.76$).
  5. A working **24-hour Community Advisory Prototype** mapping predictions to actionable health exposure windows.

---

## 2. 60-Second Elevator Pitch for the Panel

> *"Good morning respected evaluators and guide.  
> Existing air quality systems only tell people what they already breathed yesterday or right now, which is too late to prevent exposure. Under UN SDG 11.6, our project builds a 24-hour ahead $\text{PM}_{2.5}$ predictive forecasting system.  
> Today, for Milestone 2, we are demonstrating our complete end-to-end pipeline on the official UCI Multi-Site Air Quality dataset: we resolved sensor missingness across 35,064 hourly readings, engineered 24-hour temporal and meteorological lag features, established our persistence baseline ($R^2 = -0.14$, $\text{RMSE} = 89.95\ \mu\text{g/m}^3$), and trained our machine learning forecasting model which significantly beats the baseline ($R^2 = 0.76$, $\text{RMSE} = 41.27\ \mu\text{g/m}^3$, reducing error by 54.1%). Finally, we have implemented our community advisory engine that translates these forecasts into safe outdoor activity windows for vulnerable groups."*

---

## 3. Individual Member Speaking Roles (According to Synopsis)

If the panel asks each member to explain their specific work, follow this distribution:

### 1. Pravar Singh (1DS25AI074) — Data Acquisition & Preprocessing Pipeline
- **What to say:**
  > *"I owned the dataset ingestion and preprocessing pipeline. We worked with multi-sensor continuous hourly readings. The major challenge was real-world sensor dropout and missing timestamps (~3-5%). Rather than dropping rows or fabricating synthetic data, I implemented linear temporal interpolation with backward/forward fill for boundary points, preserving continuous chronological alignment required for time-series modeling."*

### 2. Shubham Pant (1DS25AI103) — Feature Engineering & Persistence Baseline
- **What to say:**
  > *"I designed the temporal feature representations and the baseline benchmark. Standard regression fails if you feed raw future values, so all our inputs strictly use information available at time $t-24$. I engineered 24-hour and 48-hour lags, 24-hour rolling mean and standard deviation, and cyclical trigonometric encodings ($\sin/\cos$) for hours and seasons. I also implemented the persistence baseline model ($y_t = y_{t-24}$), which acts as our rigorous benchmark as mandated by our evaluation rubric."*

### 3. Shourya (1DS25AI098) — Team Lead & ML Model Training / Tuning
- **What to say:**
  > *"As team lead, I architected the modeling pipeline and trained our gradient boosted regression models on 27,368 training hours and evaluated on 6,843 holdout test hours. We performed a strict chronological train/test split to prevent temporal data leakage. While the persistence baseline scored an $\text{RMSE}$ of $89.95\ \mu\text{g/m}^3$ and negative $R^2$ (-0.14), our trained GBDT model achieved an $\text{RMSE}$ of $41.27\ \mu\text{g/m}^3$ and an $R^2$ of $0.76$, outperforming the baseline by 54.1% error reduction and demonstrating strong generalizability across sudden seasonal and diurnal swings."*

### 4. Shubham Sharma (1DS25AI104) — Advisory Generation & Deliverable Evaluation
- **What to say:**
  > *"I developed the downstream advisory module that directly addresses our UN SDG 11 community impact. Forecasting numbers alone isn't enough for everyday citizens; our module automatically parses the next 24 hourly predictions against CPCB air quality bands (Good, Satisfactory, Moderate, Poor, Severe) and computes clear, actionable time windows advising school children, outdoor workers, and senior citizens when it is safe or hazardous to conduct outdoor activities."*

---

## 4. Visual Artifacts to Show on Screen

You have 3 ready-to-display figures generated in the `outputs/` folder:

1. **Figure 1: Model vs. Baseline Comparison (`outputs/1_model_vs_baseline_comparison.png`)**
   - Shows ground truth vs. ML forecast vs. persistence baseline over a 120-hour test window.
   - Point out how the persistence baseline lags behind sharp changes, whereas the ML model captures diurnal peaks accurately.
2. **Figure 2: 24-Hour Community Advisory Dashboard (`outputs/2_community_advisory_dashboard.png`)**
   - Color-coded bar chart of the upcoming 24 hours displaying exact hourly $\text{PM}_{2.5}$ predictions with green/yellow/orange alert thresholds.
3. **Figure 3: Diurnal Cycle & Quantitative Metric Summary (`outputs/3_diurnal_and_metrics_summary.png`)**
   - Left panel shows the atmospheric diurnal cycle (morning and evening traffic/atmospheric peaks).
   - Right panel displays the quantitative metric comparison (RMSE, MAE, $R^2$) clearly illustrating how the ML model outperforms the baseline.

---

## 5. Top 5 Viva / Panel Questions & Bulletproof Answers

#### Q1: "Why did you use a Persistence Baseline instead of a simple Mean baseline?"
> **Answer:** *"In continuous hourly atmospheric time series, $\text{PM}_{2.5}$ exhibits strong diurnal autocorrelation. Predicting tomorrow's 8:00 AM level as today's 8:00 AM level ($y_{t-24}$) is a much tougher and more realistic benchmark than a static overall mean. A model that cannot beat $y_{t-24}$ has learned nothing about atmospheric dynamics."*

#### Q2: "Did you use random train_test_split (like `sklearn.model_selection.train_test_split(shuffle=True)`)?"
> **Answer:** *"No, absolutely not. Shuffling time-series data causes look-ahead data leakage where the model trains on future timestamps to predict past ones. We used a strict chronological split where the first 80% is training and the subsequent contiguous 20% is holdout testing."*

#### Q3: "Why predict 24 hours ahead instead of 1 hour ahead?"
> **Answer:** *"A 1-hour ahead forecast has minimal practical community utility—a citizen or school administrator cannot reschedule sports days, shifts, or outdoor work with only 60 minutes notice. A 24-hour ahead forecast provides actionable lead time to plan day-ahead activities safely."*

#### Q4: "How does this map to UN SDG 11?"
> **Answer:** *"SDG Target 11.6 and Indicator 11.6.2 measure urban fine particulate exposure ($\text{PM}_{2.5}$). Our advisory engine directly reduces human exposure hours by identifying and flagging safe diurnal windows for urban communities."*

#### Q5: "What is your next step before the final December review?"
> **Answer:** *"For Milestone 3, we will fine-tune the LSTM sequential architecture, implement hyperparameter search across multiple monitoring stations, and package the advisory engine into a lightweight Streamlit web demo for local ward deployment."*
