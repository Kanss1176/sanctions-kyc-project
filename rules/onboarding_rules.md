# Onboarding rule catalogue

Entity data is real (GLEIF Golden Copy published 2026-10-04 16:00). Rules R01 to R05 test that real data. The workflow, requests, errors, documents and signatories are simulated and are added in later steps.

**Severity, action and SLA are my assumptions. They are not Citi policy.**

As-of time for all date logic: 2026-10-04 16:00:00 (the GLEIF publish time).

## Implemented rules (R01 to R05)

| Rule | Check | Source | Severity (1-3) | Action | SLA (hours) |
|---|---|---|---|---|---|
| R01 | Registration status is not ISSUED (ANNULLED and DUPLICATE excluded) | Observed | 3 | Escalate | 48 |
| R02 | Status is ISSUED but the next renewal date has passed | Observed | 3 | Escalate | 48 |
| R03 | Entity status is INACTIVE | Observed | 2 | Fix | 72 |
| R04 | Legal-address country differs from headquarters country | Observed | 2 | Fix | 72 |
| R05 | No parent reported and no reporting exception on file | Observed | 2 | Fix | 72 |

The check logic lives in one place, `src/onboarding_rules.py`. The build script and the tests both import it, and a test
@'
# Onboarding rule catalogue

Entity data is real (GLEIF Golden Copy published 2026-10-04 16:00). Rules R01 to R05 test that real data. The workflow, requests, errors, documents and signatories are simulated and are added in later steps.

**Severity, action and SLA are my assumptions. They are not Citi policy.**

As-of time for all date logic: 2026-10-04 16:00:00 (the GLEIF publish time).

## Implemented rules (R01 to R05)

| Rule | Check | Source | Severity (1-3) | Action | SLA (hours) |
|---|---|---|---|---|---|
| R01 | Registration status is not ISSUED (ANNULLED and DUPLICATE excluded) | Observed | 3 | Escalate | 48 |
| R02 | Status is ISSUED but the next renewal date has passed | Observed | 3 | Escalate | 48 |
| R03 | Entity status is INACTIVE | Observed | 2 | Fix | 72 |
| R04 | Legal-address country differs from headquarters country | Observed | 2 | Fix | 72 |
| R05 | No parent reported and no reporting exception on file | Observed | 2 | Fix | 72 |

The check logic lives in one place, `src/onboarding_rules.py`. The build script and the tests both import it, and a test compares the built `fact_rule_hit` table with the live rule SQL.

## Notes and limits

- R01 and R02 overlap heavily in the raw data, because most LAPSED records also have a passed renewal date. R02 is defined as ISSUED-but-overdue so the two rules stay distinct.
- ANNULLED and DUPLICATE records are excluded from R01 and R02. One ANNULLED record has a renewal date before its initial registration; it is logged as DQ01, not deleted.
- R05 uses GLEIF Level 2 data, which records accounting consolidation, not beneficial ownership. Reporting is partial. A missing parent is not proof that none exists, and a reporting exception explains why a parent is not reported; it does not mean "pass".
- Hit counts in the sample are unweighted. The sample over-represents non-ISSUED records by design, so they are not GLEIF-wide rates. Use `sampling_weight` for population estimates.

## Planned rules (not implemented yet)

| Rule | Check | Source |
|---|---|---|
| R06 | Name matches a sanctions list at threshold 80. A potential match for review only, never a finding. | Own matcher |
| R07 | Country is on the FATF list in `rules/fatf_lists.json` (dated) | Own file |
| R08-R12 | Missing or expired document; signatory authority evidence missing; form name differs from registry name | Simulated |
