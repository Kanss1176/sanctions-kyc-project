-- KPI 06: escalation rate (simulated; driven by the sample's severity-3 rule hits)
SELECT
  COUNT(*) AS requests,
  SUM(escalated::INT) AS escalated,
  ROUND(AVG(escalated::INT), 4) AS escalation_rate
FROM fact_request
