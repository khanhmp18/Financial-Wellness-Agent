import importlib.util
import sqlite3
import pandas as pd
from groq import Groq
import os

# Load shap_explainer directly by file path
spec = importlib.util.spec_from_file_location(
    "shap_explainer", "src/04_shap_explainer.py"
)
shap_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(shap_mod)
explain_member = shap_mod.explain_member

API_KEY = os.environ.get("GROQ_API_KEY", "your_groq_api_key_here")
DB_PATH = "data/financial_wellness.db"

FEATURE_LABELS = {
    "total_spend":         "Total Monthly Spend",
    "discretionary_ratio": "Discretionary Spending Ratio",
    "spending_volatility":  "Spending Volatility",
    "mom_spend_change":    "Month-over-Month Spend Change",
    "credit_utilization":  "Credit Utilization",
    "savings_rate":        "Savings Rate",
    "overdraft_frequency": "Overdraft Frequency"
}

def format_metrics(metrics):
    lines = []
    for key, val in metrics.items():
        label = FEATURE_LABELS.get(key, key)
        if key in ["discretionary_ratio", "credit_utilization",
                   "savings_rate", "mom_spend_change"]:
            lines.append(f"  - {label}: {val:.1%}")
        elif key == "total_spend":
            lines.append(f"  - {label}: ${val:,.2f}")
        else:
            lines.append(f"  - {label}: {val:.1f}")
    return "\n".join(lines)


def format_shap_drivers(explanation):
    lines = []
    for feat, impact in list(explanation.items())[:3]:
        direction = "increasing" if impact > 0 else "decreasing"
        lines.append(
            f"  - {feat} is {direction} risk "
            f"(impact: {impact:+.1f} pts)"
        )
    return "\n".join(lines)


def generate_guidance(explanation):
    client       = Groq(api_key=API_KEY)
    metrics_text = format_metrics(explanation["metrics"])
    drivers_text = format_shap_drivers(explanation["explanation"])
    score        = explanation["risk_score"]
    tier         = explanation["risk_tier"]

    prompt = (
        "You are a friendly financial wellness advisor "
        "at Vancity Credit Union in Vancouver BC.\n\n"
        "A member has this financial profile:\n\n"
        "FINANCIAL METRICS:\n"
        f"{metrics_text}\n\n"
        f"RISK SCORE: {score}/100 ({tier} Risk)\n\n"
        "TOP RISK DRIVERS:\n"
        f"{drivers_text}\n\n"
        "Write a personalized wellness summary in exactly 3 paragraphs:\n"
        "Paragraph 1 - STRENGTHS: What they are doing well, be specific.\n"
        "Paragraph 2 - CONCERNS: Top 1-2 risk areas with actual numbers.\n"
        "Paragraph 3 - ACTION STEPS: 3 concrete steps with dollar amounts "
        "and timeframes.\n"
        "Tone: warm, encouraging. Use you/your. Around 200 words."
    )

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        max_tokens=600,
        messages=[
            {"role": "system",
             "content": "You are a helpful financial wellness advisor."},
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message.content


def test_single_member():
    print("Finding a high-risk member to test...")
    conn = sqlite3.connect(DB_PATH)
    row  = pd.read_sql(
    "SELECT member_id, month FROM member_features "
    "ORDER BY RANDOM() LIMIT 1",
    conn
    )
    conn.close()

    if row.empty:
        print("No high-risk members found.")
        return

    member_id = str(row["member_id"].values[0])
    month     = str(row["month"].values[0])
    print(f"Testing: {member_id} | {month}")

    result = explain_member(member_id, month)
    if "error" in result:
        print(f"Error: {result['error']}")
        return

    print(f"Risk Score: {result['risk_score']}/100 ({result['risk_tier']})")
    print("Calling Groq API (free)...")

    guidance = generate_guidance(result)

    print("\nAI FINANCIAL WELLNESS GUIDANCE:")
    print("=" * 50)
    print(guidance)
    print("=" * 50)
    return result, guidance


def batch_generate(limit=3):
    print(f"\nGenerating guidance for top {limit} high-risk members...")
    conn = sqlite3.connect(DB_PATH)
    high_risk = pd.read_sql(
    f"SELECT member_id, month, risk_score, risk_tier FROM member_features "
    f"ORDER BY risk_score DESC LIMIT {limit}",
    conn
)
    conn.close()

    results = []
    for i, row in high_risk.iterrows():
        member_id = str(row["member_id"])
        month     = str(row["month"])
        score     = row["risk_score"]
        print(f"\n[{i+1}/{limit}] {member_id[:8]}... "
              f"| {month} | Score: {score:.1f}")
        try:
            explanation = explain_member(member_id, month)
            if "error" not in explanation:
                guidance = generate_guidance(explanation)
                results.append({
                    "member_id":  member_id,
                    "month":      month,
                    "risk_score": score,
                    "guidance":   guidance
                })
                print(f"  Done. Preview: {guidance[:80]}...")
        except Exception as e:
            print(f"  Error: {e}")

    if results:
        pd.DataFrame(results).to_csv(
            "output/guidance_samples.csv", index=False
        )
        print(f"\nSaved {len(results)} samples to "
              f"output/guidance_samples.csv")

    return results


def main():
    print("=" * 50)
    print("STEP 7 - LLM GUIDANCE ENGINE (Groq - Free)")
    print("=" * 50)

    if API_KEY == "your_groq_api_key_here":
        print("\nERROR: Add your Groq API key first!")
        print("Open src/05_llm_guidance.py and replace")
        print("'your_groq_api_key_here' with your actual key")
        print("\nGet your FREE key at: console.groq.com")
        return

    test_single_member()
    batch_generate(limit=3)
    print("\nStep 7 complete!")


if __name__ == "__main__":
    main()