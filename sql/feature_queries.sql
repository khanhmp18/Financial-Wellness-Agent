SELECT
    member_id,
    strftime('%Y-%m', trans_date)              AS month,
    SUM(amount)                                AS total_spend,
    COUNT(*)                                   AS transaction_count,
    AVG(amount)                                AS avg_transaction,
    SUM(CASE WHEN category IN (
        'food_dining','entertainment',
        'shopping_net','shopping_pos')
        THEN amount ELSE 0 END)                AS discretionary_spend,
    SUM(CASE WHEN category IN (
        'grocery_pos','grocery_net',
        'gas_transport','health_fitness')
        THEN amount ELSE 0 END)                AS essential_spend,
    SUM(is_fraud)                              AS fraud_count
FROM transactions
GROUP BY member_id, month
ORDER BY member_id, month;
