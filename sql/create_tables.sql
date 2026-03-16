-- Main transactions table
CREATE TABLE IF NOT EXISTS transactions (
    trans_id        TEXT PRIMARY KEY,
    trans_date      TEXT,
    trans_time      TEXT,
    member_id       TEXT,
    merchant        TEXT,
    category        TEXT,
    amount          REAL,
    city            TEXT,
    state           TEXT,
    is_fraud        INTEGER
);

-- Data quality log table
CREATE TABLE IF NOT EXISTS data_quality_log (
    check_date      TEXT,
    issue_type      TEXT,
    issue_count     INTEGER,
    severity        TEXT
);

-- Member features table (populated later by Python)
CREATE TABLE IF NOT EXISTS member_features (
    member_id                   TEXT,
    month                       TEXT,
    total_spend                 REAL,
    transaction_count           INTEGER,
    avg_transaction             REAL,
    discretionary_spend         REAL,
    essential_spend             REAL,
    fraud_count                 INTEGER,
    discretionary_ratio         REAL,
    spending_volatility         REAL,
    mom_spend_change            REAL,
    credit_utilization          REAL,
    savings_rate                REAL,
    overdraft_frequency         REAL,
    stress_label                INTEGER,
    risk_score                  REAL,
    risk_tier                   TEXT
);