# Methodology

## 1. Ingestion (`src/ingest.py`)
OFAC (SDN and alias CSVs, no header row, nulls written `-0-`), the UN
consolidated list (legacy XML: individuals and entities with alias blocks) and
the EU consolidated list (namespaced XML, `nameAlias` elements) are parsed into
one canonical table with one row per name, primary or alias:
`source, source_id, name, name_type, alias_type, entity_type, country, program,
list_date, remarks, name_norm`. Total 74,133 rows (EU 30,759, OFAC 39,596,
UN 3,778). Output: CSV and SQLite.

## 2. Test set (`src/build_testset.py`, seed 42)
926 labelled names:
- **360 true matches**: 60 primary names per source and entity type, perturbed
  with one rule-based variant (reorder, drop character, swap adjacent
  characters, phonetic substitution, suffix abbreviation, case/punctuation).
- **180 near-misses**: a sanctioned name with one distinctive token replaced.
- **386 true negatives**: SEC EDGAR company names (200) and synthetic person
  names (186).
Any negative whose normalised name equals a real sanctioned name is dropped.

## 3. Matching (`src/match.py`)
Names are accent-stripped, upper-cased, punctuation-stripped, and legal
suffixes are canonicalised (LIMITED to LTD, and so on). For each query,
rapidfuzz `token_sort_ratio` retrieves the top 15 candidates; each is rescored:

    score = 0.5 * token_sort + 0.3 * Jaro-Winkler + 0.2 * Metaphone overlap

on a 0-100 scale. A true match counts as found only if the candidate is the
correct list entry (same source and ID). A negative counts as a false positive
if any candidate reaches the threshold. A threshold sweep from 50 to 100 gives
recall, precision and false-positive rate.

## 4. Thresholds
- 85 and above: high-confidence match, escalated automatically.
- 75 to 84: analyst review queue.
- Below 75: cleared.
Chosen because missing a real hit costs more than reviewing a false alarm.

## 5. Risk tiering (`src/risk_scoring.py`)
Points: match 85+ = 50, match 75-84 = 25, FATF call-for-action = 40, FATF
increased monitoring = 20, PEP = 25, legal entity = 10. Tier: High at 60 or
more, Medium at 25 or more, else Low. Override: a match of 85+ or a
call-for-action country is always High. Country and PEP are synthetic.

## 6. Escalation and review (`src/escalation.py`)
High tier or PEP means EDD (source of funds and wealth, senior sign-off,
enhanced monitoring); otherwise CDD. Review cycle: High 12 months, Medium 24,
Low 36. Reference date 30 Sep 2026.

## 7. Ownership resolution (`src/ubo.py`)
Ownership is a directed acyclic graph (owner to owned). An individual's
effective stake is the sum over every path of the product of stakes. Anyone at
25% or more is flagged.

## 8. Triage (`src/triage.py`)
Alerts (score 75 or more) are ranked by customer risk tier, then match score.
Each band reports true alerts, false positives and false-positive share.

## Reproducibility
Fixed seeds throughout (42, 7, 11, 5). Raw data is not committed; sources and
fetch dates are in `data_pointers/`. Run order: `ingest`, `build_testset`,
`match`, `risk_scoring`, `escalation`, `ubo`, `triage`.