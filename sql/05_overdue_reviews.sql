-- Most overdue periodic reviews within each risk tier (window function).
-- Last-review dates are synthetic, so this demonstrates the logic, not a finding.
SELECT risk_tier, query_name, last_review, review_due, days_until_due,
       RANK() OVER (PARTITION BY risk_tier ORDER BY days_until_due ASC) AS overdue_rank
FROM read_csv('data/processed/escalation.csv', header = true)
WHERE review_status = 'overdue'
QUALIFY overdue_rank <= 5
ORDER BY CASE risk_tier WHEN 'High' THEN 1 WHEN 'Medium' THEN 2 ELSE 3 END,
         overdue_rank, query_name;
