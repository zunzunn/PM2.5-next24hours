# Review-1 Complete PPT Script & Team Speaking Guide
**Course:** Community Project (Mini Project) — `BCP308` (III Semester)  
**Project Title:** Next-Day PM2.5 Forecast (Project 34, Batch B-12)  
**Department:** Artificial Intelligence & Machine Learning, Dayananda Sagar College of Engineering  
**Evaluation Date:** 23-11-2026 | **Total Marks:** 50 Marks (5 Rubrics × 10 Marks each)

---

## Part 1: Quick Rubric-to-Slide Mapping (How to get 50/50)

| Rubric Criterion (10 Marks each) | NBA Requirement | Covered in Slide(s) | Presenting Member (Sequential) |
|:---|:---|:---:|:---:|
| **1. Problem Definition & Complexity** | Complexity (WP1–WP7) | Slide 2 & 3 | Member 1 (Shourya) |
| **2. Literature Survey & Research Gap** | Research & Analysis | Slide 4 | Member 2 (Pravar Singh) |
| **3. Proposed Solution & Cost Estimate** | Cost & Technical Solution | Slide 5 & 6 | Member 3 (Shubham Pant) |
| **4. Relevance to Society, Environment & Sustainability**| Environment & Sustainability (SDG) | Slide 7 | Member 4 (Shubham Sharma) |
| **5. Teamwork, Communication & Project Planning** | Teamwork & Project Management | Slide 8 | Team Lead (Shourya) / All |

---

## Part 2: Slide-by-Slide Script for Presentation

### Slide 1: Title & Team Introduction
- **Slide Contents:**
  - Project Title: Next-Day PM2.5 Forecast
  - Course: Community Project (BCP308) — III Sem AIML | Batch B-12, Project 34
  - Guide: Prof. Ensteih Silvia
  - Team: Shourya (1DS25AI098), Pravar Singh (1DS25AI074), Shubham Pant (1DS25AI103), Shubham Sharma (1DS25AI104)
- **Speaker:** Shourya (Team Lead)
- **Script (15 seconds):**
  > *"Respected guide and evaluators, good morning. We are Team B-12 representing Project 34. Today we present our Review-1 progress for our community project: 'Next-Day PM2.5 Forecast', designed to shift air quality management from passive monitoring to predictive community health advisories."*

---

### Slide 2: Problem Definition & Societal Scale
*(Assesses Rubric 1: Problem Definition — 10 Marks)*
- **Slide Contents:**
  - The Core Problem: Current systems report *retrospective* or *real-time* air quality; citizens only know air was toxic after breathing it.
  - Scale of Problem: WHO estimates 4+ million premature deaths annually from ambient PM2.5.
  - Impacted Community: School children, elderly citizens, and daily outdoor workers in polluted municipal wards.
  - The Solution Objective: Provide an actionable 24-hour advance forecast to identify safe outdoor exposure windows.
- **Speaker:** Shourya
- **Script (30 seconds):**
  > *"Today, air quality monitoring is purely retrospective. Sensor networks tell citizens what they inhaled hours ago, providing zero lead time to protect themselves. According to the WHO, ambient fine particulate matter causes over 4 million premature deaths each year. Vulnerable populations—like outdoor laborers, school children, and senior citizens—face severe respiratory hazards during peak diurnal pollution spikes. Our project solves this by delivering 24-hour predictive forecasts, empowering communities to plan outdoor schedules around safe air windows."*

---

### Slide 3: Complex Engineering Problem Attributes (WP1 – WP7)
*(Assesses Rubric 1: Complexity — 10 Marks)*
- **Slide Contents:**
  - **WP1 (Depth of Knowledge):** Multivariate non-linear time series modeling beyond routine linear regression.
  - **WP2 (Conflicting Requirements):** Trade-off between multi-hour forecast horizon, computational limits, and advisory simplicity.
  - **WP3 (Depth of Analysis):** Modeling coupled meteorological interactions (temperature, wind speed, pressure, humidity).
  - **WP4 (Familiarity):** Handling extreme non-stationary seasonal pollution episodes.
  - **WP7 (Interdependence):** Ingestion $\rightarrow$ Imputation $\rightarrow$ Lag Feature Engineering $\rightarrow$ ML Forecasting $\rightarrow$ CPCB Advisory Engine.
- **Speaker:** Shourya
- **Script (25 seconds):**
  > *"This is classified as a Complex Engineering Problem under NBA criteria. It demands depth of knowledge in time-series dynamics (WP1), balancing trade-offs between prediction lead time and public advisory clarity (WP2). It requires non-linear modeling of coupled weather variables (WP3), robust handling of seasonal pollution surges (WP4), and seamless interdependence across our end-to-end data, ML, and public health pipelines (WP7)."*

---

### Slide 4: Literature Survey & Research Gap Identified
*(Assesses Rubric 2: Literature Survey & Research Gap — 10 Marks)*
- **Slide Contents:**
  - Table of 6 Reviewed Works:
    1. *Zhang et al. (2017)*: Multi-site regression $\rightarrow$ Limitation: Lacks actionable exposure advisories.
    2. *Li et al. (2020)*: LSTM Networks $\rightarrow$ Limitation: Accuracy degrades beyond 12h horizon.
    3. *Wang & Zhang (2021)*: XGBoost Regressor $\rightarrow$ Limitation: Lacks automated temporal lag feature pipelines.
    4. *Liu et al. (2022)*: ST-GCN Spatiotemporal $\rightarrow$ Limitation: High compute; infeasible for lightweight deployment.
    5. *Chen et al. (2023)*: RF-LSTM Hybrid $\rightarrow$ Limitation: Did not benchmark against a persistence baseline.
    6. *CPCB Report (2024)*: Empirical AQI Standards $\rightarrow$ Limitation: Pure monitoring without predictive capabilities.
  - **Research Gap:** Existing literature focuses on macro city-wide index numbers without localized 24-hour actionable health advisories, and fails to rigorously benchmark against a strict persistence baseline ($y_t = y_{t-24}$).
- **Speaker:** Pravar Singh
- **Script (35 seconds):**
  > *"We surveyed six foundational studies across journal publications and government reports. While models like LSTMs and XGBoost show promise, current literature exhibits two critical gaps: First, existing studies focus on macro-level academic indices without translating forecasts into actionable exposure prevention windows for citizens. Second, published works rarely benchmark predictive gains against a strict persistence baseline ($y_t = y_{t-24}$) to prove real predictive value. Our project directly bridges these gaps."*

---

### Slide 5: Proposed Architecture & Dataset Details
*(Assesses Rubric 3: Proposed Solution — 10 Marks)*
- **Slide Contents:**
  - Architecture Flow: Ingestion $\rightarrow$ Missingness Imputation $\rightarrow$ 24h/48h Temporal Lag Engineering $\rightarrow$ Model Benchmarking (Persistence vs. GBDT/RF) $\rightarrow$ CPCB Advisory Engine.
  - Dataset: UCI Beijing Multi-Site Air Quality Dataset (ID: 501).
  - Scope: 420,768 records across 12 monitoring stations (35,064 hourly records per station), 18 features (pollutants + meteorology).
  - Chronological Partitioning: Strict 80% train / 20% holdout test split (zero look-ahead leakage).
- **Speaker:** Shubham Pant
- **Script (35 seconds):**
  > *"Our proposed solution implements a complete end-to-end pipeline. We utilize the UCI Multi-Site Air Quality dataset, spanning 420,768 records across 12 stations with continuous pollutant and meteorological parameters. We clean sensor dropout using linear interpolation, then engineer 24-hour and 48-hour lagged predictors, rolling statistics, and cyclical trigonometric features. We enforce a strict chronological 80-20 train/test split to guarantee zero look-ahead bias, ensuring the model only uses historical data available 24 hours prior."*

---

### Slide 6: Cost Estimation & Current Demonstrated Results
*(Assesses Rubric 3: Cost Estimate & Technical Solution — 10 Marks)*
- **Slide Contents:**
  - **Estimated Budget Table:**
    - Compute Resources (Google Colab Free Tier): ₹0
    - Internet & Data Access (Campus Network): ₹0
    - Report Documentation (Digital Submission): ₹0
    - **Total Project Cost:** **₹ 0 (Nil — Free Tier Used)**
  - **Demonstrated Results on Real Dataset:**
    - Persistence Baseline ($t-24$): $\text{RMSE} = 89.95\ \mu\text{g/m}^3,\ R^2 = -0.14$
    - Trained ML Model (GBDT): $\text{RMSE} = 41.27\ \mu\text{g/m}^3,\ R^2 = 0.76$
    - **Performance Gain:** **54.1% reduction in RMSE** over baseline!
- **Speaker:** Shubham Pant
- **Script (30 seconds):**
  > *"Under the cost rubric, our project operates with zero expenditure (₹0) by utilizing Google Colab's free GPU tier, campus infrastructure, and open-source stacks. As of today's Review-1, we have not just planned but built the working pipeline: on real data, our persistence baseline yielded an RMSE of 89.95, while our trained Gradient Boosted model achieved an RMSE of 41.27 and an R² of 0.76, outperforming the baseline by 54.1% error reduction."*

---

### Slide 7: Relevance to Society, Environment & UN SDG 11
*(Assesses Rubric 4: Environment & Sustainability — 10 Marks)*
- **Slide Contents:**
  - **UN Sustainable Development Goal:** **SDG 11 — Sustainable Cities and Communities**
  - **Target 11.6:** Reduce adverse per capita urban environmental impact, focusing on air quality.
  - **Indicator 11.6.2:** Annual mean levels of fine particulate matter ($\text{PM}_{2.5}$ and $\text{PM}_{10}$) in cities.
  - **Downstream Advisory Engine:** Maps hourly predictions to Indian CPCB categories (Good, Satisfactory, Moderate, Poor, Severe) and computes clear "Safe Outdoor Windows" for school sports, outdoor laborers, and morning walks.
- **Speaker:** Shubham Sharma
- **Script (30 seconds):**
  > *"Our project directly aligns with UN SDG 11.6 and Indicator 11.6.2 for urban particulate reduction. To make this actionable, we implemented an advisory engine based on Indian CPCB air quality bands. Rather than outputting abstract regression values, the system translates the next day's 24-hour profile into clear advisories, highlighting specific safe diurnal exposure windows—such as identifying that 11:00 AM to 6:00 PM has satisfactory air while morning hours are hazardous—directly protecting vulnerable urban citizens."*

---

### Slide 8: Team Organization, Work Breakdown & Schedule
*(Assesses Rubric 5: Teamwork, Communication & Project Planning — 10 Marks)*
- **Slide Contents:**
  - **WBS Gantt Timeline:**
    - Oct 01 – Oct 15: Literature Review & Approved Synopsis (Completed)
    - Oct 16 – Oct 31: Dataset Acquisition & Cleaning Pipeline (Completed)
    - Nov 01 – Nov 15: Feature Engineering & Baseline Setup (Completed)
    - Nov 16 – Nov 30: ML Modeling & Hyperparameter Tuning (Currently in Progress)
    - Dec 01 – Dec 15: Multi-Station Expansion & Demo Packaging
    - Dec 16 – Dec 31: Final Review Submission & Report
  - **Roles:** Shourya (Lead/Modeling), Pravar (Data Pipeline), Shubham Pant (Features/Baseline), Shubham Sharma (Advisory/Evaluation).
- **Speaker:** Shourya
- **Script (25 seconds):**
  > *"Our project is organized under a structured Work Breakdown Structure with distinct milestones. As shown in our Gantt timeline, we have completed data cleaning, feature engineering, and baseline benchmarking ahead of schedule. Each member owns a verified deliverable. In the upcoming weeks, we will expand hyperparameter tuning to deep LSTM networks and package the advisory engine into an interactive interface for the final review. Thank you, and we are ready for your questions."*

---

## Part 3: "Random Calling" Defense Script (If Evaluators Point at ANY Member)

If the evaluator interrupts and points directly at any student: *"You, what was YOUR specific contribution to this project?"*, deliver this exact 30-second response:

### 1. If SHOURYA is called at random:
> *"I am the Team Lead and SPOC. My technical ownership is **System Architecture and ML Model Training & Tuning**.  
> I established our strict chronological train/test split (80% train, 20% holdout test) to eliminate look-ahead leakage. I trained our Gradient Boosted Decision Tree regressor on 27,368 training hours and evaluated on 6,843 test hours. My model achieved an **$R^2$ of 0.76** and an **$\text{RMSE}$ of $41.27\ \mu\text{g/m}^3$**, beating our persistence baseline ($89.95\ \mu\text{g/m}^3$) by **54.1% error reduction**."*

### 2. If PRAVAR SINGH is called at random:
> *"I own the **Dataset Acquisition and Preprocessing Pipeline**.  
> I acquired the official UCI Beijing Multi-Site dataset containing 420,768 records across 12 stations. Real sensor data suffered from 925 missing hourly records. Rather than dropping rows—which breaks time-series continuity—or synthesizing fake data, I designed and validated a **linear temporal interpolation pipeline with boundary forward/backward fill**, establishing clean continuous chronological series for modeling."*

### 3. If SHUBHAM PANT is called at random:
> *"I own **Feature Engineering and Persistence Baseline Benchmarking**.  
> Because this is a 24-hour ahead forecast, standard regression features cannot use current-day data. I engineered **24-hour and 48-hour lagged variables, 24-hour rolling mean and standard deviation**, and cyclical $\sin/\cos$ trigonometric transformations for hours and months. I also implemented the **Persistence Baseline model ($y_t = y_{t-24}$)**, establishing our benchmark $\text{RMSE}$ of $89.95\ \mu\text{g/m}^3$ and negative $R^2$ (-0.14) to prove real algorithmic gain."*

### 4. If SHUBHAM SHARMA is called at random:
> *"I own the **Downstream Advisory Engine and Societal/SDG Impact Evaluation**.  
> Raw numerical predictions are useless to everyday citizens, so I built the translation engine that maps 24-hour continuous $\text{PM}_{2.5}$ predictions into official **CPCB Air Quality bands** (Good, Satisfactory, Moderate, Poor, Severe). My module automatically calculates and flags **recommended safe outdoor exposure windows**, fulfilling our UN SDG 11.6 objective to protect school children, elderly citizens, and outdoor workers."*
