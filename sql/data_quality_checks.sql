SELECT 'Missing member_id' AS issue_type,
       COUNT(*)             AS issue_count,
       'High'               AS severity
FROM transactions
WHERE member_id IS NULL

UNION ALL

SELECT 'Missing amount',
       COUNT(*), 'High'
FROM transactions
WHERE amount IS NULL

UNION ALL

SELECT 'Negative amounts',
       COUNT(*), 'Medium'
FROM transactions
WHERE amount < 0

UNION ALL

SELECT 'Future dates',
       COUNT(*), 'High'
FROM transactions
WHERE trans_date > DATE('now')

UNION ALL

SELECT 'Duplicate transactions',
       COUNT(*), 'High'
FROM (
    SELECT trans_id
    FROM transactions
    GROUP BY trans_id
    HAVING COUNT(*) > 1
)

UNION ALL

SELECT 'Zero amount transactions',
       COUNT(*), 'Low'
FROM transactions
WHERE amount = 0;
