-- KPI 08: ranked work queue of open requests (simulated).
-- Band 1 overdue, 2 severity-3 rule hit, 3 under 8 hours left, else 4. Hours left is calendar-hour approximation.
WITH sev AS (
  SELECT h.lei, MAX(r.severity) AS max_severity
  FROM fact_rule_hit h JOIN dim_rule r ON r.rule_id = h.rule_id
  GROUP BY h.lei
),
q AS (
  SELECT
    f.request_id, f.lei, f.request_type, f.due_ts,
    COALESCE(s.max_severity, 0) AS max_severity,
    date_diff('minute', (SELECT asof_ts FROM sim_clock), f.due_ts) / 60.0 AS hours_left
  FROM fact_request f LEFT JOIN sev s ON s.lei = f.lei
  WHERE f.status = 'Open'
)
SELECT
  request_id, lei, request_type, due_ts, max_severity,
  ROUND(hours_left, 1) AS hours_left,
  CASE WHEN hours_left < 0 THEN 1 WHEN max_severity >= 3 THEN 2
       WHEN hours_left < 8 THEN 3 ELSE 4 END AS priority_band,
  ROW_NUMBER() OVER (
    ORDER BY CASE WHEN hours_left < 0 THEN 1 WHEN max_severity >= 3 THEN 2
                  WHEN hours_left < 8 THEN 3 ELSE 4 END, hours_left, request_id
  ) AS queue_rank
FROM q
ORDER BY queue_rank
