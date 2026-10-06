# Client Onboarding Control Simulation

A simulated client onboarding operation built on real public GLEIF entity data. It covers a maker-checker workflow, SLA tracking, escalation rules, an Excel operations pack, versioned Word procedures and a test suite.

> **Simulated workflow on real GLEIF entity data. Not bank data.** Entity records are real and public (GLEIF Golden Copy, published 2026-10-04 16:00). Requests, errors, document events, staffing, SLAs and volumes are my assumptions.

## Headline results

| Result | Label | Value |
|---|---|---|
| Control-rule hits in the 5,000-entity sample (unweighted, over-represents lapsed and retired records) | Observed from GLEIF | @@HITS@@ |
| Baseline workflow, 6 makers and 3 checkers: @@REQ@@ requests, @@DONE@@ completed, @@OPEN@@ open | Simulated | Median turnaround @@MED@@ h, P90 @@P90@@ h, @@BREACH@@ SLA breaches, @@ESC@@ escalated requests |
| Excel pack figures agree with the DuckDB tables, and the SQL metrics are re-computed in Python | Derived | KPI_Summary check cell shows ALL OK; 50 automated tests pass |

In my simulation the escalation share follows my own severity and action assumptions, so it is not a typical rate.

## What is in the project

- **Rules R01 to R07:** registration and renewal status, entity status, country mismatch, missing parent, name score against public sanctions lists (potential match for review only), and FATF-listed country. Severity, action and SLA values are my assumptions. Catalogue: `rules/onboarding_rules.md`.
- **Workflow simulation:** four request types, a shared queue engine with FIFO and priority options (`config.yaml`), 20-seed scenario comparison.
- **Excel operations pack** (`excel/Citi_Onboarding_Ops_Pack.xlsx`): Daily_Queue with priority bands, Checker_Log with maker-checker validation, KPI_Summary checked against DuckDB, Lodgment_Log, Archive_Manifest, Reg_Watch change register and UAT_Results.
- **Word procedures** (`docs/procedures/`): signatory update, renewal-overdue rule (v1.0 and v1.1 with change record CR-001, a simulated change), escalation matrix (v1.0 and v1.1), and six sample client and internal replies.
- **Tests:** 50 pytest tests covering rules, model integrity, workflow invariants, scenarios and SQL metrics.
- **UAT:** 38 cases. 21 automated cases are linked to pytest and passed. 17 manual and document cases are written but not yet run.

Full write-up: [`docs/onboarding_platform.md`](docs/onboarding_platform.md).

## Limits

- Not bank data and not bank policy. Rule severity, SLAs and the 4-hour lodgment target are assumed values.
- GLEIF Level 2 shows accounting consolidation, not beneficial ownership. A missing parent is not proof that none exists.
- A name match against a sanctions list is a potential match for review only, not a finding. No company names are exported.
- Lodgment_Log rows 12 to 17 and Archive_Manifest rows 14 and 15 are deliberate test cases.
- On Checker_Log, a checker who is the same person as the maker is flagged ("CHECK: maker equals checker") but not blocked. Tested in Excel on 2026-10-06. Blocking it would need a stricter validation rule or procedure.

## Reproduce

Raw GLEIF and sanctions files are not committed (see `docs/01_provenance_register.md` and `data_pointers/`). After the sample and `data/processed/` exist, run in this order:

    python scripts/build_model.py
    python scripts/build_parents.py
    python scripts/build_screen.py
    python scripts/build_rules.py
    python scripts/build_workflow.py
    python scripts/build_clock.py
    python scripts/build_scenarios.py
    python scripts/build_seeds.py
    python -m pytest tests -q

---

