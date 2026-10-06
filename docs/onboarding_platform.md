# Client Onboarding Control Platform

A portfolio project that screens a sample of public legal-entity records against onboarding rules, simulates a maker-checker onboarding workflow, and measures turnaround, SLA breaches and errors with SQL.

> **This is a simulation on public and synthetic data. It is not Citi data or policy, and it is not a compliance system.** Every workflow parameter (volumes, staffing, SLAs, error rates, handling times) is an assumption stated in `config.yaml`. Simulation outputs are not findings about real onboarding.

## 1. Data and sample

- **Source:** the public GLEIF legal-entity (LEI) golden copy.
- **Sample:** 5,000 entities across 12 countries, built with a stratified design that deliberately holds about 50% non-ISSUED records (41.4% in those countries overall). Rates below are therefore **sample rates, not GLEIF-wide rates**. Use `sampling_weight` for population estimates.
- **Model:** DuckDB database with `dim_entity`, `dim_country`, `dim_rule`, `fact_parent`, `fact_rule_hit` and the workflow tables.

## 2. Onboarding rules R01 to R07

Rule definitions, severity, action and SLA labels are in `rules/onboarding_rules.md`. Severity, action and SLA are assumptions. Rules with severity 3 or above (R01, R02, R06) drive escalation in the simulation.

Hits in the 5,000-entity sample:

| Rule | Hits | Share of sample |
|---|---|---|
| R01 status not ISSUED | 2,466 | 49.3% |
| R02 ISSUED but renewal overdue | 5 | 0.1% |
| R03 entity status INACTIVE | 959 | 19.2% |
| R04 legal vs HQ country differ | 120 | 2.4% |
| R05 no parent and no exception | 349 | 7.0% |
| R06 (see rules/onboarding_rules.md) | 47 | 0.9% |
| R07 (see rules/onboarding_rules.md) | 0 | 0.0% |

2,561 of 5,000 entities (51.2%) have at least one hit. R01 and R03 are inflated by the sample design (see section 1). R05 matches the parent table count (349), which serves as a cross-check.

## 3. Simulation design

All values below are assumptions, set in `config.yaml`.

- 2,000 requests over 21 business days (1 to 30 October 2026), Mon to Fri, 09:00 to 18:00, no holidays. Each request is linked to a real sampled LEI.
- Four request types: new account, signatory change, document refresh, data amendment, each with an assumed share, SLA (8 to 16 business hours) and handling times.
- Maker-checker flow with a shared waiting queue. FIFO is the default; the alternative policy is earliest-due-date-first ("priority").
- 6% injected error rate, 85% checker detection rate. Injected errors use codes R08 to R12 and are stored in `sim_error_truth`, kept separate from `fact_request`, so escaped errors can be measured.
- Entities with a severity 3 rule hit are escalated, with a 2 to 6 hour delay. Because the sample over-represents non-ISSUED records, about half of requests escalate. This is a simulation effect.
- Fixed random seed (20261001), so the same seed gives the same tables.

## 4. Baseline (6 makers, 3 checkers)

| Measure | Value |
|---|---|
| Requests, completed, open | 2,000, 1,980, 20 |
| Median turnaround | 1.9 business hours |
| P90 turnaround | 5.93 business hours |
| SLA breach rate (completed) | 0.0% |
| First-time-right | 94.6% |
| Injected errors, caught by checker | 125, 108 |

Notes:

- A 0.0% breach rate says the assumed workload leaves plenty of slack at 6/3. It is not a finding about onboarding.
- 108 of 125 caught is the configured 85% detection rate coming back out (observed 86.4%). It is not a measured control result.

## 5. Scenario results

Scenario runs use `src/scenarios.py`. Staffing is varied; demand is the same random draw per seed.

| Scenario (makers/checkers) | Mean SLA breach rate | Range across 20 seeds |
|---|---|---|
| FIFO 5/3 | 0.2% | 0.0% to 1.6% |
| FIFO 4/2 | 66.3% | 51.1% to 78.1% |
| Priority 4/2 | 61.6% | 42.6% to 76.9% |

- **Capacity matters far more than queue policy.** Moving from 5/3 to 4/2 takes breaches from about 0% to about 66% under these assumptions.
- **Priority scheduling helps a little.** At 4/2, earliest-due-date-first lowered the breach rate by about 4.7 points on average (largest reduction 9.1 points, smallest 0.8 points), and was better in 20 of 20 seeds. It did not prevent overload: about 270 requests stayed open on average.
- **Priority moves the delay around.** In one single-seed run at 4/2, data amendments (8-hour SLA) improved while new accounts (16-hour SLA) got worse. This was not checked across seeds.
- At 8/4, 6/3 and 5/3, breaches are at or near zero for both policies, so queue order does not matter there.
- Escaped errors are 18 of 108 in every scenario because the detection rate is configured. They carry no information about the policies.

## 6. Correction log

Two defects were found and fixed during the build. They are kept here on purpose.

1. **Scheduler bug in `serve()`.** A test (`test_no_completion_before_arrival`) failed. Some jobs were completing before they arrived because one server's idle-jump left the queue clock able to move backwards. Fixed by making the clock monotonic, with a new test (`test_serve_never_starts_a_job_before_it_is_ready`).
2. **Overloaded first workflow tables.** The first workflow generator (`src/workflow_sim.py`) gave an 87.6% SLA breach rate at 6/3 staffing. That was first read as under-staffing, and staffing was raised to 8/4 to compensate. That reading was wrong. With escalation delays set to zero the same generator gave a 0.0% breach rate at both 8/4 and 6/3, and the newer queue engine showed no overload at 6/3. The cause is consistent with that generator booking each checker in arrival order, so a delayed escalated request reserved a checker far ahead and blocked later work. The tables were rebuilt on the shared queue engine (`src/workflow_v2.py`), with baseline staffing reset to 6/3. The old `simulate` function is kept in the repo but is no longer used for the tables.
3. **Scenario baseline mismatch.** The scenario baseline first differed from the workflow baseline (1,977 vs 1,980 completed) because the two engines drew random numbers in a different order. I aligned the draw order and added a test that checks the baseline matches exactly.

## 7. Limitations

- All workflow parameters are assumptions. Results describe the simulated system, not any real team.
- Single baseline run plus 20-seed comparisons for three scenarios only. Other scenarios were run once (single seed).
- Rework adds delay to a request but does not occupy a maker or checker. Rework is not assigned to the same maker.
- No breaks, shifts or public holidays. Work-queue "hours left" is a calendar-hour approximation.
- Escalation rate is inflated by the sample design.
- The scenario tables (`src/scenarios.py`) and the workflow tables (`src/workflow_v2.py`) use the same queue logic and draw random numbers in the same order, so the baseline scenario matches the workflow tables exactly (1,980 completed, 20 open). A test checks this.

## 8. Reproduce

Order matters. `build_model.py` wipes the database, and the screen step takes about 15 minutes.

    python scripts/build_model.py
    python scripts/build_parents.py
    python scripts/build_screen.py
    python scripts/build_rules.py
    python scripts/build_workflow.py
    python scripts/build_clock.py
    python scripts/build_scenarios.py
    python scripts/build_seeds.py
    python -m pytest tests -q

Expected: 49 tests pass. SQL metrics are in `sql/metrics/` (one file per KPI), with tests that compare each against a Python recomputation.

## Known limitations
- The workbook does not block a checker who is the same person as the maker, but it flags it with "CHECK: maker equals checker" on Checker_Log (tested: maker M3 with checker M3 fires the flag, M3 with C1 does not). Blocking it outright would need a validation rule or procedure.

## Test data
- Lodgment_Log rows 12 to 17 and Archive_Manifest rows 14 and 15 are deliberate test cases (returned, rejected, pending, and two deliberate errors that fire the red flags). All maker IDs, checker IDs, dates and document types are simulated.

## Backup
- The workbook before the fill step is saved as OLD_before_fill_DO_NOT_EDIT.xlsx. Rerun fill_lodgment_archive.py from that file, not from the main file.