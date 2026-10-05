-- KPI 01: turnaround (completed requests only; business hours; simulated)
SELECT
  COUNT(*) AS completed,
  ROUND(MEDIAN(tat_hours), 2) AS median_tat_h,
  ROUND(quantile_cont(tat_hours, 0.9), 2) AS p90_tat_h
FROM fact_request
WHERE status = 'Completed'
