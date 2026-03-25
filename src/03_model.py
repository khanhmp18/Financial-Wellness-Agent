import pandas as pd
import numpy as np
import sqlite3
import pickle
import os
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import (classification_report, roc_auc_score, confusion_matrix)
from xgboost import XGBClassifier

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

def load_features():
    print("Loading features from database...")
    conn = sqlite3.connect(DB_PATH)
    df   = pd.read_sql("SELECT * FROM member_features", conn)
    conn.close()
    print(f"  Rows loaded:    {len(df):,}")
    print(f"  Stress rate:    {df['stress_label'].mean():.2%}")
    print(f"  Features shape: {df[FEATURES].shape}")
    return df

def train_model(df):
    X = df[FEATURES]
    y = df["stress_label"]

    # Train/test split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    print(f"\n  Train size: {len(X_train):,}")
    print(f"  Test size:  {len(X_test):,}")

    # Train XGBoost
    print("\nTraining XGBoost model...")
    model = XGBClassifier(
        n_estimators=200,
        max_depth=3,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        min_child_weight=5,
        random_state=42,
        eval_metric="logloss",
        verbosity=0
    )
    model.fit(X_train, y_train)

    # Evaluate
    y_pred = model.predict(X_test)
    y_prob = model.predict_proba(X_test)[:, 1]

    print("\n" + "="*50)
    print("MODEL PERFORMANCE")
    print("="*50)
    print(classification_report(y_test, y_pred,
          target_names=["Not Stressed", "Stressed"]))

    auc = roc_auc_score(y_test, y_prob)
    print(f"ROC-AUC Score: {auc:.3f}")

    cm = confusion_matrix(y_test, y_pred)
    print(f"\nConfusion Matrix:")
    print(f"  True Negatives:  {cm[0][0]:,}  (correctly identified not stressed)")
    print(f"  False Positives: {cm[0][1]:,}  (flagged as stressed but weren't)")
    print(f"  False Negatives: {cm[1][0]:,}  (missed stressed members)")
    print(f"  True Positives:  {cm[1][1]:,}  (correctly identified stressed)")

    # Feature importance
    print("\nFeature Importance:")
    importance = pd.DataFrame({
        "feature":   FEATURES,
        "importance": model.feature_importances_
    }).sort_values("importance", ascending=False)

    for _, row in importance.iterrows():
        bar = "█" * int(row["importance"] * 50)
        print(f"  {row['feature']:<28} {bar} {row['importance']:.3f}")

    return model, auc

def score_all_members(model, df, conn):
    print("\nScoring all members...")

    df["risk_score"] = (
        model.predict_proba(df[FEATURES])[:, 1] * 100
    ).round(1)

    df["risk_tier"] = pd.cut(
        df["risk_score"],
        bins=[0, 30, 60, 100],
        labels=["Low", "Medium", "High"]
    )

    print(f"\nRisk Tier Breakdown:")
    tier_counts = df["risk_tier"].value_counts()
    for tier, count in tier_counts.items():
        pct = count / len(df) * 100
        bar = "█" * int(pct / 2)
        print(f"  {tier:<8} {bar} {count:,} ({pct:.1f}%)")

    print(f"\nRisk Score Stats:")
    print(f"  Min:    {df['risk_score'].min():.1f}")
    print(f"  Max:    {df['risk_score'].max():.1f}")
    print(f"  Mean:   {df['risk_score'].mean():.1f}")
    print(f"  Median: {df['risk_score'].median():.1f}")

    # Save back to DB
    df.to_sql("member_features", conn,
              if_exists="replace", index=False)
    print("\nRisk scores saved to database.")
    return df

def main():
    print("=" * 50)
    print("STEP 5 — ML MODEL TRAINING")
    print("=" * 50)

    # Make sure output folder exists
    os.makedirs("output", exist_ok=True)

    # Load data
    df = load_features()

    # Train model
    model, auc = train_model(df)

    # Score all members
    conn = sqlite3.connect(DB_PATH)
    df   = score_all_members(model, df, conn)

    # Save model to disk
    with open(MODEL_PATH, "wb") as f:
        pickle.dump(model, f)
    print(f"\nModel saved to: {MODEL_PATH}")

    # Final verification
    sample = pd.read_sql("""
        SELECT member_id, month, risk_score, risk_tier
        FROM member_features
        ORDER BY risk_score DESC
        LIMIT 5
    """, conn)
    print("\nTop 5 Highest Risk Members:")
    print(sample.to_string(index=False))

    conn.close()
    print("\nStep 5 complete!")

if __name__ == "__main__":
    main()
