# KYC/AML Screening Program Note

**Simulation on public sanctions data and synthetic test cases. Not a compliance
system and carries no legal authority.**

## Purpose
Before onboarding or continuing to serve a customer, a bank must confirm the
customer is not sanctioned or politically exposed, and set the depth of due
diligence in proportion to risk. This project simulates that flow end to end:
name screening, risk tiering, CDD/EDD escalation, beneficial-ownership
resolution and periodic review.

## Data
| Source | Use |
|---|---|
| OFAC SDN list and aliases | sanctions names (39,596 name rows) |
| UN Security Council consolidated list | sanctions names (3,778 name rows) |
| EU consolidated sanctions list | sanctions names (30,759 name rows) |
| FATF lists, 19 June 2026 | jurisdiction risk (3 call-for-action, 22 increased monitoring) |
| SEC EDGAR company list | true-negative test entities |
| Synthetic | test names, customer country/PEP flags, ownership structures, review dates |

All lists were fetched on 29-30 Sep 2026. Total canonical table: 74,133 name rows.

## How it works
1. **Ingest** the three lists into one canonical entity table (primary names and aliases).
2. **Match** each customer name with rapidfuzz token-sort, Jaro-Winkler and a
   Metaphone overlap, combined 0.5 / 0.3 / 0.2 on a 0-100 scale. Legal suffixes
   are normalised before scoring.
3. **Band** the score: 85 and above is escalated automatically; 75 to 84 goes
   to an analyst; below 75 is cleared.
4. **Tier** each customer Low / Medium / High with a weighted rule catalogue
   (match confidence, FATF jurisdiction, PEP flag, legal entity).
5. **Escalate:** High tier or PEP means EDD; otherwise CDD.
6. **Resolve ownership** by graph traversal, flagging anyone at 25% or more.
7. **Schedule reviews:** High 12 months, Medium 24, Low 36.

## Results (926 labelled test names: 360 true matches, 180 near-misses, 386 true negatives)
| Threshold | Recall | Precision | False-positive rate |
|---|---|---|---|
| 75 | 94.7% | 73.0% | 22.3% |
| 80 | 92.2% | 85.8% | 9.7% |
| 85 | 80.3% | 93.5% | 3.5% |

| Alert band | Alerts | True | False positives | False-positive share |
|---|---|---|---|---|
| 85 and above | 309 | 289 | 20 | 6.5% |
| 75 to 84 | 158 | 52 | 106 | 67.1% |

- Lowering the review threshold from 85 to 75 recovers 14 more points of recall
  at the cost of 158 extra analyst reviews, about a third of which are genuine.
- Of 360 true matches, 296 land in High tier, 50 in Medium, 14 in Low.
- Recall at threshold 80 by source: OFAC 95.0%, EU 90.8%, UN 90.8% (120 test rows each).
- Ownership: across 51 synthetic structures, 81 of 232 individuals cross 25%,
  and 24 of those 81 hold no direct stake in the target company. A direct-holder
  check alone would miss them.

## Findings
- False alarms come from **generic words** (LTD, GROUP, CORP, FINANCIAL) and
  **shared common surnames**, not from unrelated names. A character-level score
  cannot tell a generic-word match from a distinctive-word match.
- A legal-suffix normalisation step lifted recall on abbreviated suffixes from
  38% to 100% (at threshold 80).
- Tier is not the same as match score: a clean name in a call-for-action
  jurisdiction is still High.

## Limitations
See `limitations.md`. In short: synthetic customers and ownership, a
rule-generated test set with no hold-out, no transliteration or script
handling, no date-of-birth or country corroboration, no control-based ownership.