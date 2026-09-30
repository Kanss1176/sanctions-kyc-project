-- Escalation queue: CDD vs EDD volume by risk tier
SELECT risk_tier,
       due_diligence,
       COUNT(*) AS customers,
       SUM(CASE WHEN LOWER(CAST(pep AS VARCHAR)) = 'true' THEN 1 ELSE 0 END) AS pep_flagged,
       ROUND(AVG(risk_points), 1) AS avg_risk_points
FROM read_csv('data/processed/escalation.csv', header = true)
GROUP BY risk_tier, due_diligence
ORDER BY CASE risk_tier WHEN 'High' THEN 1 WHEN 'Medium' THEN 2 ELSE 3 END,
         due_diligence;
