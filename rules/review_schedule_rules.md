# Periodic Review Schedule Rules

| Tier | Review cycle |
|---|---|
| High | 12 months |
| Medium | 24 months |
| Low | 36 months |

## Logic
- Next review date = last review date + cycle for the customer's tier.
- Days until due = next review date minus the reference date.
- A record is **overdue** when days until due is negative.
- Reference date used in this simulation: 30 Sep 2026.

## Notes
- Regulators expect frequency to follow risk but do not prescribe these exact
  intervals. They are a common industry convention used here as an assumption.
- Last-review dates are synthetic, so overdue counts demonstrate the logic and
  are not a finding.