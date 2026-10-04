# Provenance register

## 1. Sources (GLEIF Golden Copy)

Source page: https://www.gleif.org/en/lei-data/gleif-golden-copy/download-the-golden-copy
Publish time: 2026-10-04 16:00. Downloaded: 2026-10-05.

| File | Format version | Page record count | SHA-256 | Size |
|---|---|---|---|---|
| 20261004-1600-gleif-goldencopy-lei2-golden-copy.csv.zip | LEI-CDF v3.1 | 3,451,551 | PASTE_HASH_FROM_LOG | PASTE_SIZE |
| 20261004-1600-gleif-goldencopy-rr-golden-copy.csv.zip | RR-CDF v2.1 | 489,935 | PASTE_HASH_FROM_LOG | PASTE_SIZE |
| 20261004-1600-gleif-goldencopy-repex-golden-copy.csv.zip | Reporting Exceptions v2.1 | 6,396,820 | PASTE_HASH_FROM_LOG | PASTE_SIZE |

Level 1 rows loaded: 3,451,551 (matches the page).
Relationship and reporting-exception rows loaded: to be added after the check.

## 2. As-of time

All "renewal date passed" logic uses 2026-10-04 16:00, the Golden Copy publish time.

## 3. Derived files (not committed, in data/processed)

- gleif_lei_slim.parquet: 22 columns, 3,451,551 rows, built by scripts/build_gleif_slim.py.
- entity_sample.parquet: 5,000 rows, built by scripts/build_sample.py.

## 4. Sampling rule (an assumption)

- Countries: IN, US, GB, DE, FR, NL, LU, CH, IE, CA, AU, KY. Chosen as large banking centres and fund domiciles. These are not claimed to be Citi's clients.
- Universe in those countries: 1,941,854 entities.
- Quotas: ISSUED 2,500 (population 1,138,793), LAPSED 1,500 (659,812), other non-active 1,000 (143,249).
- Selection: ordered by a hash of the LEI plus the seed "gleif-sample-2026-v1", so it is repeatable.
- Each row carries sampling_weight (population divided by sampled, per stratum).

## 5. Bias statement

The sample holds 50% non-ISSUED records against 41.4% in those 12 countries. Exception rates in the sample therefore do not represent GLEIF as a whole. Use sampling_weight to re-weight. Country-level rates are only approximate, because weights vary by status stratum, not by country.

## 6. Sanctions lists

| List | Version or download date | Records |
|---|---|---|
| OFAC | TO ADD | TO ADD |
| UN | TO ADD | TO ADD |
| EU | TO ADD | TO ADD |