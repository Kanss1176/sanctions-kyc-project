-- Entity resolution: normalised names that appear on more than one sanctions list
SELECT name_norm,
       COUNT(DISTINCT source) AS lists,
       string_agg(DISTINCT source, ', ') AS sources,
       COUNT(*) AS name_rows
FROM read_csv('data/processed/entities.csv', header = true, all_varchar = true)
GROUP BY name_norm
HAVING COUNT(DISTINCT source) > 1
ORDER BY lists DESC, name_rows DESC, name_norm
LIMIT 20;
