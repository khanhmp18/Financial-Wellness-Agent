import pandas as pd
import numpy as np
import sqlite3

DB_PATH = "data/financial_wellness.db"

def run_data_quality_checks(conn):
    print("Running data quality checks...")
    query = open("sql/data_quality_checks.sql").read()
    dq = pd.read_sql_query(query, conn)
    dq["check_date"] = pd.Timestamp.today().strftime("%Y-%m-%d")

    dq.to_sql("data_quality_log", conn,
              if_exists="replace", index=False)

    print("\nData Quality Report:")
    print(dq.to_string(index=False))
    return dq

def engineer_features(conn):
    print("\nRunning SQL feature queries...")
    query = open("sql/feature_queries.sql").read()
    df = pd.read_sql_query(query, conn)
    print(f"  Raw rows returned: {len(df):,}")
    print(f"  Unique members:    {df['member_id'].nunique():,}")
    print(f"  Months covered:    {df['month'].nunique()}")

    print("\nEngineering features...")

    # Discretionary ratio
    df["discretionary_ratio"] = (
        df["discretionary_spend"] /
        df["total_spend"].replace(0, np.nan)
    ).fillna(0).round(4)

    # Spending volatility (std dev per member)
    df["spending_volatility"] = (
        df.groupby("member_id")["total_spend"]
        .transform("std")
        .fillna(0)
        .round(4)
    )

    # Month over month spend change
    df = df.sort_values(["member_id", "month"])
    df["mom_spend_change"] = (
        df.groupby("member_id")["total_spend"]
        .pct_change()
        .fillna(0)
        .round(4)
    )

    # Simulate credit utilization
    np.random.seed(42)
    df["credit_utilization"] = (
        (df["discretionary_ratio"] * 0.5) +
        (df["mom_spend_change"].clip(0, 1) * 0.2) +
        np.random.uniform(0.05, 0.25, len(df))
    ).clip(0, 1).round(4)

    # Simulate savings rate
    df["savings_rate"] = (
        1 - df["discretionary_ratio"] - 0.35
    ).clip(0.01, 0.50).round(4)

    # Overdraft frequency proxy
    df["overdraft_frequency"] = (
        (df["transaction_count"] / 10) *
        (df["credit_utilization"] > 0.65).astype(int)
    ).round(0)

    # Stress label
    df["stress_score_raw"] = (
        (df["credit_utilization"]  > 0.50).astype(int) * 25 +
        (df["credit_utilization"]  > 0.70).astype(int) * 15 +
        (df["savings_rate"]        < 0.10).astype(int) * 20 +
        (df["savings_rate"]        < 0.05).astype(int) * 15 +
        (df["discretionary_ratio"] > 0.40).astype(int) * 15 +
        (df["discretionary_ratio"] > 0.60).astype(int) * 10 +
        (df["overdraft_frequency"] > 1).astype(int)    * 10 +
        (df["mom_spend_change"]    > 0.10).astype(int) * 5  +
        (df["spending_volatility"] > df["spending_volatility"].median()).astype(int) * 5
    )

    # Label stressed if raw score >= 30
    df["stress_label"] = (df["stress_score_raw"] >= 30).astype(int)

    print(f"\nFeature Summary:")
    print(f"  Avg credit utilization: {df['credit_utilization'].mean():.2%}")
    print(f"  Avg savings rate:       {df['savings_rate'].mean():.2%}")
    print(f"  Avg discretionary ratio:{df['discretionary_ratio'].mean():.2%}")
    print(f"  Stress rate:            {df['stress_label'].mean():.2%}")
    print(f"  Total records:          {len(df):,}")

    return df

def preview_features(df):
    print("\nSample of engineered features:")
    cols = [
        "member_id", "month", "total_spend",
        "credit_utilization", "savings_rate",
        "discretionary_ratio", "stress_label"
    ]
    print(df[cols].head(10).to_string(index=False))

    print("\nCategory spending breakdown:")
    print(f"  Total discretionary spend: ${df['discretionary_spend'].sum():,.2f}")
    print(f"  Total essential spend:     ${df['essential_spend'].sum():,.2f}")

def main():
    print("=" * 50)
    print("STEP 4 — FEATURE ENGINEERING")
    print("=" * 50)

    conn = sqlite3.connect(DB_PATH)

    # Run data quality checks first
    run_data_quality_checks(conn)

    # Engineer features
    df = engineer_features(conn)

    # Preview results
    preview_features(df)

    # Save to database
    print("\nSaving features to database...")
    df.to_sql("member_features", conn,
              if_exists="replace", index=False)

    # Verify save
    count = pd.read_sql(
        "SELECT COUNT(*) as rows FROM member_features", conn
    )
    print(f"Saved {count['rows'].values[0]:,} rows to member_features table")

    conn.close()
    print("\nStep 4 complete!")

if __name__ == "__main__":
    main()