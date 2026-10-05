-- KPI 04: errors found by the checker, by request type and error code (simulated)
SELECT
  r.request_type,
  x.error_code,
  COUNT(*) AS errors_found
FROM fact_exception x
JOIN fact_request r ON r.request_id = x.request_id
GROUP BY r.request_type, x.error_code
ORDER BY r.request_type, x.error_code
