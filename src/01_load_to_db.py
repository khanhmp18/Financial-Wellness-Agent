import pandas as pd
import sqlite3
import os

# Config
DB_PATH   = "data/financial_wellness.db"
CSV_TRAIN = "data/fraudTrain.csv"
CSV_TEST  = "data/fraudTest.csv"

def create_tables(conn):
    """Create tables from SQL schema file"""
    print("Creating tables...")
    with open("sql/create_tables.sql", "r") as f:
        sql = f.read()
    # Execute each statement separately
    for statement in sql.split(";"):
        statement = statement.strip()
        if statement:
            conn.execute(statement)
    conn.commit()
    print("Tables created.")

def load_data():
    # Load CSVs
    print("Loading fraudTrain.csv...")
    train = pd.read_csv(CSV_TRAIN)
    print(f"  Train rows: {len(train):,}")

    print("Loading fraudTest.csv...")
    test = pd.read_csv(CSV_TEST)
    print(f"  Test rows:  {len(test):,}")

    # Combine both files
    df = pd.concat([train, test], ignore_index=True)
    print(f"  Total rows: {len(df):,}")

    # ── Clean & rename columns ──────────────────────────────────
    print("\nCleaning data...")

    # Parse datetime
    df["trans_date_trans_time"] = pd.to_datetime(
        df["trans_date_trans_time"]
    )
    df["trans_date"] = df["trans_date_trans_time"].dt.strftime(
        "%Y-%m-%d"
    )
    df["trans_time"] = df["trans_date_trans_time"].dt.strftime(
        "%H:%M:%S"
    )

    # Select and rename columns to match our schema
    df_clean = df[[
        "trans_num",
        "trans_date",
        "trans_time",
        "cc_num",
        "merchant",
        "category",
        "amt",
        "city",
        "state",
        "is_fraud"
    ]].rename(columns={
        "trans_num": "trans_id",
        "cc_num":    "member_id",
        "amt":       "amount"
    })

    # Convert member_id to string
    df_clean["member_id"] = df_clean["member_id"].astype(str)

    print(f"  Cleaned shape: {df_clean.shape}")
    print(f"  Fraud rate:    {df_clean['is_fraud'].mean():.2%}")
    print(f"  Unique members:{df_clean['member_id'].nunique():,}")
    print(f"  Date range:    {df_clean['trans_date'].min()} "
          f"to {df_clean['trans_date'].max()}")

    # Load into SQLite
    print("\nConnecting to SQLite database...")
    conn = sqlite3.connect(DB_PATH)

    # Create tables
    create_tables(conn)

    # Load transactions
    print("Loading transactions into database...")
    df_clean.to_sql(
        "transactions",
        conn,
        if_exists="replace",
        index=False,
        chunksize=10000   # load in chunks to avoid memory issues
    )

    # Verify the load
    print("\nVerifying load...")
    count = pd.read_sql(
        "SELECT COUNT(*) as total FROM transactions", conn
    )
    sample = pd.read_sql(
        "SELECT * FROM transactions LIMIT 3", conn
    )

    print(f"  Rows in DB: {count['total'].values[0]:,}")
    print(f"\nSample rows:")
    print(sample.to_string())

    # Run a quick SQL sanity check
    print("\nRunning SQL sanity checks...")

    checks = pd.read_sql("""
        SELECT 
            COUNT(*) as total_transactions,
            COUNT(DISTINCT member_id) as unique_members,
            SUM(is_fraud) as total_fraud,
            ROUND(AVG(amount), 2) as avg_amount,
            MIN(trans_date) as earliest_date,
            MAX(trans_date) as latest_date
        FROM transactions
    """, conn)

    print(checks.to_string())

    conn.close()
    print(f"\n✅ Done! Database saved to: {DB_PATH}")

if __name__ == "__main__":
    load_data()