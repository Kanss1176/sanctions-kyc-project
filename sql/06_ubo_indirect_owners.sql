-- Beneficial owners at or above 25% who hold no direct stake in the target
SELECT COUNT(*) AS individuals,
       COUNT(*) FILTER (WHERE LOWER(CAST(ubo AS VARCHAR)) = 'true') AS ubos_25_pct_plus,
       COUNT(*) FILTER (WHERE LOWER(CAST(ubo AS VARCHAR)) = 'true'
                          AND COALESCE(direct_pct, 0) = 0) AS ubos_no_direct_stake
FROM read_csv('data/processed/ubo_results.csv', header = true);