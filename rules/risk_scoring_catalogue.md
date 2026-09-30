# Risk Scoring Catalogue

Illustrative rule catalogue for a simulation. The weights are this project's
own judgement, not a validated model. Country and PEP inputs are synthetic.

## Point rules
| ID | Rule | Points | Basis |
|---|---|---|---|
| R1 | Sanctions match score 85 or above | 50 | FATF R.6/R.7 |
| R2 | Sanctions match score 75 to 84 | 25 | FATF R.6/R.7 |
| R3 | Jurisdiction on FATF call-for-action list | 40 | FATF R.19 |
| R4 | Jurisdiction on FATF increased-monitoring list | 20 | FATF R.19 |
| R5 | PEP flag | 25 | FATF R.12 |
| R6 | Customer is a legal entity | 10 | FATF R.10, R.24 |

R1 and R2 are mutually exclusive, as are R3 and R4. Only the higher applies.

## Tier bands
| Total points | Tier |
|---|---|
| 60 or more | High |
| 25 to 59 | Medium |
| Below 25 | Low |

## Overrides
- A match score of 85 or above forces **High**.
- A call-for-action jurisdiction forces **High**.

## Notes
- FATF increased-monitoring status does not by itself call for EDD, so R4 is a
  moderate score and not an override.
- Jurisdiction lists are stored in `rules/fatf_lists.json` (FATF statements of
  19 June 2026).