from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
import sqlite3
import pandas as pd
import importlib.util

app = FastAPI(
    title="Financial Wellness API",
    description="AI-powered financial stress detection API",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

DB_PATH = "data/financial_wellness.db"

def load_explainer():
    spec = importlib.util.spec_from_file_location(
        "shap_explainer", "src/04_shap_explainer.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.explain_member

def load_guidance():
    spec = importlib.util.spec_from_file_location(
        "llm_guidance", "src/05_llm_guidance.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.generate_guidance

@app.get("/")
def root():
    return {
        "name":    "Financial Wellness API",
        "version": "1.0.0",
        "status":  "live"
    }

@app.get("/members")
def get_members(tier: str = None, limit: int = 2000):
    conn  = sqlite3.connect(DB_PATH)
    query = """
        SELECT member_id, risk_tier, risk_score
        FROM member_features
        GROUP BY member_id
        HAVING risk_score = MAX(risk_score)
    """
    if tier:
        query = f"""
            SELECT member_id, risk_tier, risk_score
            FROM member_features
            WHERE risk_tier = '{tier}'
            GROUP BY member_id
            HAVING risk_score = MAX(risk_score)
        """
    query += f" ORDER BY risk_score DESC LIMIT {limit}"
    df    = pd.read_sql(query, conn)
    conn.close()
    return df.to_dict(orient="records")

@app.get("/member/{member_id}")
def get_member(member_id: str, month: str = None):
    conn  = sqlite3.connect(DB_PATH)
    query = f"""
        SELECT * FROM member_features
        WHERE member_id = '{member_id}'
    """
    if month:
        query += f" AND month = '{month}'"
    query += " ORDER BY month DESC LIMIT 1"
    df    = pd.read_sql(query, conn)
    conn.close()
    if df.empty:
        return {"error": "Member not found"}
    return df.to_dict(orient="records")[0]

@app.get("/member/{member_id}/risk-score")
def get_risk_score(member_id: str, month: str = None):
    conn  = sqlite3.connect(DB_PATH)
    query = f"""
        SELECT member_id, month, risk_score, risk_tier,
               credit_utilization, savings_rate
        FROM member_features
        WHERE member_id = '{member_id}'
    """
    if month:
        query += f" AND month = '{month}'"
    query += " ORDER BY month DESC LIMIT 1"
    df    = pd.read_sql(query, conn)
    conn.close()
    if df.empty:
        return {"error": "Member not found"}
    return df.to_dict(orient="records")[0]

@app.get("/member/{member_id}/history")
def get_history(member_id: str):
    conn = sqlite3.connect(DB_PATH)
    df   = pd.read_sql(f"""
        SELECT month, total_spend, discretionary_spend,
               essential_spend, risk_score, risk_tier,
               credit_utilization, savings_rate
        FROM member_features
        WHERE member_id = '{member_id}'
        ORDER BY month DESC
    """, conn)
    conn.close()
    if df.empty:
        return []
    return df.to_dict(orient="records")

@app.get("/member/{member_id}/guidance")
def get_guidance(member_id: str, month: str = None):
    conn  = sqlite3.connect(DB_PATH)
    query = f"""
        SELECT member_id, month FROM member_features
        WHERE member_id = '{member_id}'
        ORDER BY month DESC LIMIT 1
    """
    df    = pd.read_sql(query, conn)
    conn.close()
    if df.empty:
        return {"error": "Member not found"}

    use_month         = month or str(df["month"].values[0])
    explain_member    = load_explainer()
    generate_guidance = load_guidance()
    result            = explain_member(member_id, use_month)
    guidance          = generate_guidance(result)

    return {
        "member_id":   member_id,
        "month":       use_month,
        "risk_score":  result["risk_score"],
        "risk_tier":   result["risk_tier"],
        "guidance":    guidance,
        "top_drivers": dict(
            list(result["explanation"].items())[:3]
        )
    }

@app.get("/portfolio/summary")
def get_portfolio_summary():
    conn = sqlite3.connect(DB_PATH)
    df   = pd.read_sql("SELECT * FROM member_features", conn)
    conn.close()
    return {
        "total_members":     int(df["member_id"].nunique()),
        "high_risk_count":   int((df["risk_tier"] == "High").sum()),
        "medium_risk_count": int((df["risk_tier"] == "Medium").sum()),
        "low_risk_count":    int((df["risk_tier"] == "Low").sum()),
        "avg_risk_score":    round(float(df["risk_score"].mean()), 1),
        "avg_credit_util":   round(float(df["credit_utilization"].mean()), 3)
    }

@app.get("/ui/dashboard", response_class=HTMLResponse)
def dashboard():
    return HTMLResponse(
        content=open("api/static/dashboard.html").read()
    )