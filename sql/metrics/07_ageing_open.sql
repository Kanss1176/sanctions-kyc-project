-- KPI 07: ageing of open requests, in calendar hours since receipt (approximation)
WITH o AS (
  SELECT date_diff('minute', received_ts, (SELECT asof_ts FROM sim_clock)) / 60.0 AS age_h
  FROM fact_request WHERE status = 'Open'
)
SELECT
  CASE WHEN age_h < 4 THEN '0-4h' WHEN age_h < 8 THEN '4-8h'
       WHEN age_h < 24 THEN '8-24h' ELSE '24h+' END AS age_bucket,
  COUNT(*) AS open_requests
FROM o
GROUP BY 1
ORDER BY MIN(age_h)
