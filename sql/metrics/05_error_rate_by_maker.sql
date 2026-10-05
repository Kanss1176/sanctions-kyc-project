-- KPI 05: error rate by maker (completed only; simulated). Errors are those the checker caught.
SELECT
  maker_id,
  COUNT(*) AS completed,
  SUM(has_error::INT) AS errors_caught,
  ROUND(AVG(has_error::INT), 4) AS error_rate
FROM fact_request
WHERE status = 'Completed'
GROUP BY maker_id
ORDER BY maker_id
