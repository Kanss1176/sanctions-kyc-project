-- KPI 03: first-time-right and rework (completed only; simulated)
SELECT
  COUNT(*) AS completed,
  ROUND(AVG(first_time_right::INT), 4) AS first_time_right,
  SUM(rework_count) AS rework_loops,
  ROUND(AVG(rework_count), 4) AS rework_per_request
FROM fact_request
WHERE status = 'Completed'
