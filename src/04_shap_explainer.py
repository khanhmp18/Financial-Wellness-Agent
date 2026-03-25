import pandas as pd
import sqlite3
import pickle
import shap
import json
import numpy as np

DB_PATH    = "data/financial_wellness.db"
MODEL_PATH = "output/stress_model.pkl"

FEATURES = [
    "total_spend",
    "discretionary_ratio",
    "spending_volatility",
    "mom_spend_change",
    "credit_utilization",
    "savings_rate",
    "overdraft_frequency"
]

FEATURE_LABELS = {
    "total_spend":            "Total Monthly Spend",
    "discretionary_ratio":    "Discretionary Spending Ratio",
    "spending_volatility":    "Spending Volatility",
    "mom_spend_change":       "Month-over-Month Spend Change",
    "credit_utilization":     "Credit Utilization",
    "savings_rate":           "Savings Rate",
    "overdraft_frequency":    "Overdraft Frequency"
}

def load_model_and_data():
    conn = sqlite3.connect(DB_PATH)
    df   = pd.read_sql("SELECT * FROM member_features", conn)
    conn.close()

    with open(MODEL_PATH, "rb") as f:
        model = pickle.load(f)

    return model, df

def explain_member(member_id: str, month: str) -> dict:
    model, df = load_model_and_data()

    # Get this member's row
    row = df[
        (df["member_id"].astype(str) == str(member_id)) &
        (df["month"] == month)
    ]

    if row.empty:
        return {"error": f"No data found for member {member_id} in {month}"}

    X = row[FEATURES]

    # Calculate SHAP values
    explainer   = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(X)

    # Handle both binary and multi-output SHAP formats
    if isinstance(shap_values, list):
        sv = shap_values[1][0]   # class 1 = stressed
    else:
        sv = shap_values[0]

    # Build explanation dict
    explanation = {}
    for feat, val in zip(FEATURES, sv):
        label = FEATURE_LABELS[feat]
        explanation[label] = round(float(val) * 100, 2)

    # Sort by absolute impact — biggest drivers first
    explanation = dict(sorted(
        explanation.items(),
        key=lambda x: abs(x[1]),
        reverse=True
    ))

    metrics = row[FEATURES].to_dict(orient="records")[0]

    return {
        "member_id":   str(member_id),
        "month":       month,
        "risk_score":  round(float(row["risk_score"].values[0]), 1),
        "risk_tier":   str(row["risk_tier"].values[0]),
        "metrics":     metrics,
        "explanation": explanation
    }

def explain_portfolio_shap():
    """Calculate average SHAP importance across all members"""
    print("Calculating portfolio-wide SHAP values...")
    model, df = load_model_and_data()

    X = df[FEATURES]

    explainer   = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(X)

    if isinstance(shap_values, list):
        sv = np.abs(shap_values[1])
    else:
        sv = np.abs(shap_values)

    importance = pd.DataFrame({
        "feature": [FEATURE_LABELS[f] for f in FEATURES],
        "mean_shap_impact": sv.mean(axis=0).round(4)
    }).sort_values("mean_shap_impact", ascending=False)

    return importance

def main():
    print("=" * 50)
    print("STEP 6 — SHAP EXPLAINABILITY")
    print("=" * 50)

    model, df = load_model_and_data()
    print(f"Loaded {len(df):,} member records")

    # Portfolio-level SHAP
    print("\nPortfolio-Wide Feature Impact (SHAP):")
    importance = explain_portfolio_shap()
    for _, row in importance.iterrows():
        bar = "█" * int(row["mean_shap_impact"] * 500)
        print(f"  {row['feature']:<35} {bar} {row['mean_shap_impact']:.4f}")

    # Test individual member explanation
    print("\nTesting individual member explanation...")

    # Pick one high risk member to test
    high_risk = df[df["risk_tier"] == "High"].iloc[0]
    member_id = high_risk["member_id"]
    month     = high_risk["month"]

    print(f"\nExplaining member: {member_id} | month: {month}")
    result = explain_member(member_id, month)

    if "error" in result:
        print(f"Error: {result['error']}")
        return

    print(f"\nRisk Score: {result['risk_score']}/100 ({result['risk_tier']} Risk)")
    print("\nKey Metrics:")
    for feat, val in result["metrics"].items():
        label = FEATURE_LABELS.get(feat, feat)
        print(f"  {label:<35} {val:.4f}")

    print("\nTop Risk Drivers (SHAP):")
    for feat, impact in result["explanation"].items():
        direction = "↑ increases" if impact > 0 else "↓ decreases"
        bar = "█" * int(abs(impact) / 2)
        print(f"  {feat:<35} {direction} risk  {bar} ({impact:+.2f})")

    # Save shap importance to output
    importance.to_csv("output/shap_importance.csv", index=False)
    print("\nSHAP importance saved to output/shap_importance.csv")

    print("\nStep 6 complete!")

if __name__ == "__main__":
    main()