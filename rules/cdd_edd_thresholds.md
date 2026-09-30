# CDD / EDD Escalation Thresholds

## Screening bands
| Match score | Action |
|---|---|
| 85 and above | High-confidence match, escalated automatically |
| 75 to 84 | Analyst review queue |
| Below 75 | Cleared |

Rationale: missing a real hit costs more than reviewing a false alarm.

## Due diligence level
| Condition | Level |
|---|---|
| Tier is High, or PEP flag is set | **EDD** |
| Otherwise | **CDD** |

## CDD (standard) evidence
- Identify and verify the customer
- Identify the beneficial owner (ownership of 25% or more)
- Understand the purpose and nature of the relationship

## EDD (additional) evidence
- Source of funds and source of wealth
- Senior management sign-off
- Enhanced ongoing monitoring
- Full beneficial-ownership resolution to natural persons

## Beneficial ownership
Ownership is resolved through every path in the ownership graph. Any individual
whose effective stake is 25% or more is flagged. The 25% figure is a widely
used convention, not a FATF mandate (see `docs/regulatory_basis.md`).