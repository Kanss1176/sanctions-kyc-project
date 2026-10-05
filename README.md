# Sanctions & PEP Screening with Risk-Based Due Diligence

A simulation of a bank's KYC screening flow on public OFAC / UN / EU sanctions
lists: name matching, risk tiering, CDD/EDD escalation, beneficial-ownership
resolution and periodic review scheduling.

> **This is a simulation on public and synthetic data. It is not a compliance
> system and has no legal authority.**

> **Also in this repo: Client Onboarding Control Platform.** A simulated maker-checker onboarding workflow on public GLEIF data, with rules, SQL metrics and scenario analysis. All workflow results are simulated with assumed parameters. See [`docs/onboarding_platform.md`](docs/onboarding_platform.md).

Start with the write-up: [`docs/kyc_aml_program_note.md`](docs/kyc_aml_program_note.md)

## Headline results
Evaluated on 926 labelled names (360 true matches, 180 near-misses, 386 true negatives):

| Threshold | Recall | Precision | False-positive rate |
|---|---|---|---|
| 75 | 94.7% | 73.0% | 22.3% |
| 80 | 92.2% | 85.8% | 9.7% |
| 85 | 80.3% | 93.5% | 3.5% |

The near-miss set is a deliberate stress test, so these false-positive rates are
worse than a real customer base would give.

## What is real and what is synthetic
| Real, public | Synthetic (clearly labelled) |
|---|---|
| OFAC SDN list, UN consolidated list, EU consolidated list | Test-name variants and near-misses |
| FATF lists (19 June 2026) | Customer country, PEP flags, review dates |
| SEC EDGAR company names (true negatives) | 51 ownership structures |

## Repository layout
    data_pointers/   where the data comes from, plus the generated test set
    sql/             entity-resolution, ranking and review queries
    src/             ingest, build_testset, match, risk_scoring, escalation, ubo, triage
    rules/           risk scoring catalogue, CDD/EDD thresholds, review schedule, FATF lists
    docs/            program note, methodology, regulatory basis, limitations, outputs
    notebooks/       exploration
    dashboard/       reserved for the dashboard

## Reproduce
Raw lists are not committed. Download them as described in `data_pointers/`,
then run in this order:

    pip install pandas rapidfuzz jellyfish networkx duckdb
    python src/ingest.py
    python src/build_testset.py
    python src/match.py
    python src/risk_scoring.py
    python src/escalation.py
    python src/ubo.py
    python src/triage.py 
    python src/run_sql.py

Random seeds are fixed, so the test set and results are reproducible.

SQL analysis: `python src/run_sql.py` runs six DuckDB queries over the processed files and saves the results to `docs/sql_results/`.

## Limitations
See [`docs/limitations.md`](docs/limitations.md): synthetic customers and
ownership, a rule-generated test set with no hold-out, no transliteration
handling, name-only matching, and ownership based on percentage only.
## Client Onboarding Control Platform (branch `onboarding-platform`)

A separate project in this repo: GLEIF-based onboarding rules, a simulated maker-checker workflow and SQL metrics. See [`docs/onboarding_platform.md`](docs/onboarding_platform.md).
