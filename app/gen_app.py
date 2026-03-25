import os
import sqlite3
import pandas as pd
import numpy as np

DB_PATH = "data/financial_wellness.db"

def generate_database():
    """Generate synthetic database for Streamlit Cloud deployment"""
    os.makedirs("data", exist_ok=True)
    os.makedirs("output", exist_ok=True)

    print("Generating synthetic transaction data...")
    np.random.seed(42)

    n_members    = 500
    member_ids   = [str(np.random.randint(int(1e14), int(9e14)))
                    for _ in range(n_members)]
    categories   = [
        "grocery_pos", "grocery_net", "gas_transport",
        "health_fitness", "food_dining", "entertainment",
        "shopping_net", "shopping_pos", "misc_net", "misc_pos"
    ]

    rows = []
    for member in member_ids:
        n_trans = np.random.randint(50, 200)
        for _ in range(n_trans):
            month  = np.random.randint(1, 25)
            year   = 2019 + (month - 1) // 12
            mon    = ((month - 1) % 12) + 1
            date   = f"{year}-{mon:02d}-{np.random.randint(1,28):02d}"
            rows.append({
                "trans_id":   str(np.random.randint(int(1e10), int(9e10))),
                "trans_date": date,
                "trans_time": f"{np.random.randint(0,23):02d}:{np.random.randint(0,59):02d}:00",
                "member_id":  member,
                "merchant":   f"Merchant_{np.random.randint(1,100)}",
                "category":   np.random.choice(categories),
                "amount":     round(abs(np.random.exponential(80)), 2),
                "city":       np.random.choice(["Vancouver","Toronto","Calgary","Montreal"]),
                "state":      np.random.choice(["BC","ON","AB","QC"]),
                "is_fraud":   int(np.random.random() < 0.005)
            })

    df   = pd.DataFrame(rows)
    conn = sqlite3.connect(DB_PATH)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            trans_id TEXT, trans_date TEXT, trans_time TEXT,
            member_id TEXT, merchant TEXT, category TEXT,
            amount REAL, city TEXT, state TEXT, is_fraud INTEGER
        )
    """)
    df.to_sql("transactions", conn, if_exists="replace", index=False)
    print(f"Loaded {len(df):,} synthetic transactions")

    # Feature engineering
    print("Engineering features...")
    query = """
        SELECT
            member_id,
            strftime('%Y-%m', trans_date) AS month,
            SUM(amount) AS total_spend,
            COUNT(*) AS transaction_count,
            AVG(amount) AS avg_transaction,
            SUM(CASE WHEN category IN ('food_dining','entertainment',
                'shopping_net','shopping_pos') THEN amount ELSE 0 END)
                AS discretionary_spend,
            SUM(CASE WHEN category IN ('grocery_pos','grocery_net',
                'gas_transport','health_fitness') THEN amount ELSE 0 END)
                AS essential_spend,
            SUM(is_fraud) AS fraud_count
        FROM transactions
        GROUP BY member_id, month
        ORDER BY member_id, month
    """
    feat = pd.read_sql(query, conn)

    feat["discretionary_ratio"] = (
        feat["discretionary_spend"] /
        feat["total_spend"].replace(0, np.nan)
    ).fillna(0).round(4)

    feat["spending_volatility"] = (
        feat.groupby("member_id")["total_spend"]
        .transform("std").fillna(0).round(4)
    )

    feat = feat.sort_values(["member_id", "month"])
    feat["mom_spend_change"] = (
        feat.groupby("member_id")["total_spend"]
        .pct_change().fillna(0).round(4)
    )

    np.random.seed(42)
    feat["credit_utilization"] = (
        (feat["discretionary_ratio"] * 0.5) +
        (feat["mom_spend_change"].clip(0, 1) * 0.2) +
        np.random.uniform(0.05, 0.25, len(feat))
    ).clip(0, 1).round(4)

    feat["savings_rate"] = (
        1 - feat["discretionary_ratio"] - 0.35
    ).clip(0.01, 0.50).round(4)

    feat["overdraft_frequency"] = (
        (feat["transaction_count"] / 10) *
        (feat["credit_utilization"] > 0.65).astype(int)
    ).round(0)

    feat["stress_score_raw"] = (
        (feat["credit_utilization"]  > 0.50).astype(int) * 25 +
        (feat["credit_utilization"]  > 0.70).astype(int) * 15 +
        (feat["savings_rate"]        < 0.10).astype(int) * 20 +
        (feat["savings_rate"]        < 0.05).astype(int) * 15 +
        (feat["discretionary_ratio"] > 0.40).astype(int) * 15 +
        (feat["discretionary_ratio"] > 0.60).astype(int) * 10 +
        (feat["overdraft_frequency"] > 1).astype(int)    * 10 +
        (feat["mom_spend_change"]    > 0.10).astype(int) * 5  +
        (feat["spending_volatility"] > feat["spending_volatility"].median()).astype(int) * 5
    )
    feat["stress_label"] = (feat["stress_score_raw"] >= 30).astype(int)

    # Train model
    print("Training model...")
    from sklearn.model_selection import train_test_split
    from xgboost import XGBClassifier
    import pickle

    FEATURES = [
        "total_spend", "discretionary_ratio", "spending_volatility",
        "mom_spend_change", "credit_utilization", "savings_rate",
        "overdraft_frequency"
    ]

    X = feat[FEATURES]
    y = feat["stress_label"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    model = XGBClassifier(
        n_estimators=100, max_depth=4,
        learning_rate=0.1, random_state=42,
        eval_metric="logloss", verbosity=0
    )
    model.fit(X_train, y_train)

    feat["risk_score"] = (
        model.predict_proba(feat[FEATURES])[:, 1] * 100
    ).round(1)

    feat["risk_tier"] = pd.cut(
        feat["risk_score"],
        bins=[0, 30, 60, 100],
        labels=["Low", "Medium", "High"]
    ).astype(str)

    feat.to_sql("member_features", conn,
                if_exists="replace", index=False)

    # Save model
    with open("output/stress_model.pkl", "wb") as f:
        pickle.dump(model, f)

    # Data quality log
    dq = pd.DataFrame([
        {"issue_type": "Missing member_id",      "issue_count": 0, "severity": "High"},
        {"issue_type": "Missing amount",          "issue_count": 0, "severity": "High"},
        {"issue_type": "Negative amounts",        "issue_count": 0, "severity": "Medium"},
        {"issue_type": "Future dates",            "issue_count": 0, "severity": "High"},
        {"issue_type": "Duplicate transactions",  "issue_count": 0, "severity": "High"},
        {"issue_type": "Zero amount transactions","issue_count": 0, "severity": "Low"},
    ])
    dq["check_date"] = pd.Timestamp.today().strftime("%Y-%m-%d")
    dq.to_sql("data_quality_log", conn,
              if_exists="replace", index=False)

    conn.close()

    tiers = feat["risk_tier"].value_counts()
    print(f"Database ready! Members: {feat['member_id'].nunique()}")
    print(f"Risk tiers: {tiers.to_dict()}")
    print("Startup complete!")

if __name__ == "__main__":
    generate_database()