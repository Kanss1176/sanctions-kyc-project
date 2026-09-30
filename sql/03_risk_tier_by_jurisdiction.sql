-- Risk-tier distribution by jurisdiction (conditional aggregation).
-- Country is a synthetic customer attribute in this simulation.
SELECT country,
       COUNT(*) AS customers,
       SUM(CASE WHEN risk_tier = 'High'   THEN 1 ELSE 0 END) AS high,
       SUM(CASE WHEN risk_tier = 'Medium' THEN 1 ELSE 0 END) AS medium,
       SUM(CASE WHEN risk_tier = 'Low'    THEN 1 ELSE 0 END) AS low,
       ROUND(100.0 * SUM(CASE WHEN risk_tier = 'High' THEN 1 ELSE 0 END) / COUNT(*), 1) AS pct_high
FROM read_csv('data/processed/risk_scored.csv', header = true)
GROUP BY country
HAVING COUNT(*) >= 5
ORDER BY pct_high DESC, customers DESC
LIMIT 15;
