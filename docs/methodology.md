# Methodology Documentation

## Project Overview
AI Financial Wellness Copilot is an end-to-end data analytics system
that detects early financial stress signals in member transaction data
and generates personalized AI-powered financial guidance.

---

## Data Source
**Dataset:** Credit Card Fraud Detection Dataset (Kaggle)
- Source: kaggle.com/datasets/kartik2112/fraud-detection
- Size: 1,852,394 transactions
- Period: January 2019 — December 2020
- Members: 1,000 unique cardholders

---

## Architecture
```
Raw CSV Data
    ↓
SQLite Database (SQL)
    ↓
Feature Engineering (Python + pandas)
    ↓
ML Model — XGBoost (scikit-learn)
    ↓
SHAP Explainability
    ↓
LLM Guidance (Groq — LLaMA 3)
    ↓
Streamlit Dashboard
```

---

## Feature Engineering

All features are computed per member per month from raw transactions.

| Feature | Formula | Risk Indicator |
|---|---|---|
| `total_spend` | SUM(amount) per member per month | Baseline |
| `discretionary_ratio` | discretionary_spend / total_spend | High = risk |
| `spending_volatility` | STD of monthly total_spend | High = unstable |
| `mom_spend_change` | % change vs prior month | High = risk |
| `credit_utilization` | Modelled from spend patterns | >70% = risk |
| `savings_rate` | 1 - discretionary_ratio - 0.35 | <5% = risk |
| `overdraft_frequency` | Proxy from transaction count x utilization | >3 = risk |

**Discretionary categories:** food_dining, entertainment, shopping_net, shopping_pos

**Essential categories:** grocery_pos, grocery_net, gas_transport, health_fitness

---

## Stress Label Definition

A member-month is labelled as financially stressed (1) if ANY
of the following conditions are met:
```python
stress = (
    (credit_utilization  > 0.70) |
    (savings_rate        < 0.05) |
    (overdraft_frequency > 3)    |
    (discretionary_ratio > 0.60)
)
```

**Stress rate in dataset:** ~18.5% of member-months

---

## Machine Learning Model

**Model:** XGBoost Classifier
**Train/Test Split:** 80% / 20% (stratified)
**Target:** stress_label (binary: 0 = stable, 1 = stressed)

**Features used:**
- total_spend
- discretionary_ratio
- spending_volatility
- mom_spend_change
- credit_utilization
- savings_rate
- overdraft_frequency

**Risk Score:** model.predict_proba()[:, 1] × 100
(converted to 0–100 scale)

**Risk Tiers:**
- Low: 0–30
- Medium: 31–60
- High: 61–100

---

## Explainability — SHAP

SHAP (SHapley Additive exPlanations) values are calculated
using TreeExplainer to identify which features contributed
most to each member's risk score.

Each feature receives a positive or negative impact score:
- Positive = increases risk
- Negative = decreases risk

This ensures every prediction is transparent and auditable —
a key requirement for internal audit applications.

---

## LLM Guidance Engine

**Provider:** Groq API (free tier)
**Model:** LLaMA 3.3 70B Versatile

The LLM receives:
- Member financial metrics
- Risk score and tier
- Top 3 SHAP risk drivers

It generates a 3-paragraph personalized wellness summary:
1. Strengths — what the member is doing well
2. Concerns — top risk areas with specific numbers
3. Action Steps — 3 concrete steps with dollar amounts

---

## Data Quality Checks

Six checks are run at data ingestion time:

| Check | Severity |
|---|---|
| Missing member_id | High |
| Missing amount | High |
| Negative amounts | Medium |
| Future dates | High |
| Duplicate transactions | High |
| Zero amount transactions | Low |

Results are logged to the `data_quality_log` table in SQLite.

---

## Assumptions & Limitations

1. **Credit utilization is simulated** — the dataset does not
   contain actual credit limit data. Utilization is modelled
   from spending patterns as a proxy.

2. **Savings rate is derived** — not directly observed.
   It is estimated as 1 - discretionary_ratio - 0.35.

3. **Rule-based stress labels** — the stress label is defined
   by business rules, not ground truth financial stress data.
   A real deployment would use actual member financial health
   outcomes to train the model.

4. **Synthetic fraud dataset** — the underlying data is a
   synthetic fraud detection dataset repurposed for financial
   wellness analysis. Real credit union data would produce
   different feature distributions.

5. **LLM guidance is informational only** — AI-generated
   guidance should be reviewed by a qualified financial
   advisor before being shared with members.