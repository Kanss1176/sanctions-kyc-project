-- Match-confidence ranking: highest-scoring non-matches (the false-alarm drivers)
SELECT category, query_name, best_candidate, best_score,
       RANK() OVER (PARTITION BY category ORDER BY best_score DESC) AS rank_in_category
FROM read_csv('data/processed/risk_scored.csv', header = true)
WHERE expected_match = 0
QUALIFY rank_in_category <= 5
ORDER BY category, rank_in_category, query_name;
