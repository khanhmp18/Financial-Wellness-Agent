-- Test 1: Top spending categories
SELECT 
    category,
    COUNT(*)            AS transaction_count,
    ROUND(SUM(amount), 2)  AS total_spend,
    ROUND(AVG(amount), 2)  AS avg_spend
FROM transactions
GROUP BY category
ORDER BY total_spend DESC;

-- Test 2: Monthly transaction volume
SELECT
    substr(trans_date, 1, 7)  AS month,
    COUNT(*)                   AS num_transactions,
    ROUND(SUM(amount), 2)      AS total_volume
FROM transactions
GROUP BY month
ORDER BY month;

-- Test 3: Top 10 members by spend
SELECT
    member_id,
    COUNT(*)                AS num_transactions,
    ROUND(SUM(amount), 2)   AS total_spend,
    SUM(is_fraud)           AS fraud_count
FROM transactions
GROUP BY member_id
ORDER BY total_spend DESC
LIMIT 10;