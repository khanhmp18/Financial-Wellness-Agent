# AI Financial Wellness Copilot

A full-stack data analytics system that detects early financial stress signals in member transaction data and generates
personalized AI-powered financial guidance.

Built as a portfolio project targeting Vancity Credit Union's
Data Support Intern and Internal Audit Intern roles.

---

## Demo

![Dashboard Preview](docs/dashboard_preview.png)

---

## Architecture
```
Raw Transaction Data (1.8M rows)
        ↓
SQLite Database — SQL feature extraction
        ↓
Python + pandas — Feature engineering
        ↓
XGBoost — Financial stress prediction
        ↓
SHAP — Explainable AI risk drivers
        ↓
Groq LLaMA 3 — Personalized guidance
        ↓
Streamlit — Interactive dashboard
```

---

## Features

- **Risk Scoring** — 0–100 financial stress score per member
  per month using XGBoost
- **Explainable AI** — SHAP values identify top risk drivers
  for every prediction
- **AI Guidance** — LLM generates personalized 3-paragraph
  financial wellness narratives
- **Interactive Dashboard** — Filter by risk tier, select
  any member, view spend history and risk gauge
- **Data Quality Monitoring** — Automated checks at ingestion
  for nulls, duplicates, anomalies
- **SQL-driven** — All feature extraction done via SQL queries
  on a SQLite database

---

## Tech Stack

| Layer | Tool |
|---|---|
| Data Storage | SQLite |
| Data Processing | Python, pandas, NumPy |
| Machine Learning | XGBoost, scikit-learn |
| Explainability | SHAP |
| LLM Integration | Groq API (LLaMA 3.3 70B) |
| Dashboard | Streamlit, Plotly |
| Reporting | Excel (openpyxl) |

---

## Project Structure
```
financial-wellness-copilot/
├── data/
│   └── financial_wellness.db    SQLite database
├── sql/
│   ├── create_tables.sql        Schema definition
│   ├── feature_queries.sql      Feature extraction
│   └── data_quality_checks.sql  Quality monitoring
├── src/
│   ├── 01_load_to_db.py         Data ingestion
│   ├── 02_feature_engineering.py Feature engineering
│   ├── 03_model.py              ML model training
│   ├── 04_shap_explainer.py     SHAP explainability
│   ├── 05_llm_guidance.py       LLM guidance engine
│   └── export_for_powerbi.py    Data export
├── app/
│   └── dashboard.py             Streamlit dashboard
├── output/                      Generated reports
├── docs/
│   └── methodology.md           Full methodology docs
└── README.md
```

---

## Setup & Installation
```bash
# Clone the repo
git clone https://github.com/yourusername/financial-wellness-copilot
cd financial-wellness-copilot

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install pandas numpy scikit-learn xgboost shap \
    streamlit plotly groq openpyxl kaggle
```

---

## Running the Project
```bash
# Step 1 — Load data into SQLite
python src/01_load_to_db.py

# Step 2 — Engineer features
python src/02_feature_engineering.py

# Step 3 — Train ML model
python src/03_model.py

# Step 4 — Test SHAP explainer
python src/04_shap_explainer.py

# Step 5 — Test LLM guidance
python src/05_llm_guidance.py

# Step 6 — Launch dashboard
streamlit run app/dashboard.py
```

---

## Key Results

- **1,852,394** transactions processed
- **1,000** unique members scored
- **24,000** member-month feature records
- **~18.5%** financial stress rate detected
- **ROC-AUC: ~0.97** model performance

---

## Documentation

See [docs/methodology.md](docs/methodology.md) for full
documentation of features, model design, assumptions,
and limitations.

---

## Dataset

Credit Card Fraud Detection Dataset — Kaggle
kaggle.com/datasets/kartik2112/fraud-detection