-- KPI 02: SLA breach rate by request type (completed only; simulated)
SELECT
  request_type,
  COUNT(*) AS completed,
  SUM(sla_breached::INT) AS breached,
  ROUND(AVG(sla_breached::INT), 4) AS breach_rate
FROM fact_request
WHERE status = 'Completed'
GROUP BY request_type
ORDER BY request_type
