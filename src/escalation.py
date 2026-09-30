"""CDD vs EDD escalation and periodic-review scheduling.

Input : data/processed/risk_scored.csv
Output: data/processed/escalation.csv, docs/escalation_summary.csv
Last-review dates are SYNTHETIC (seeded). Reference date is fixed for
reproducibility.
"""
import random

import pandas as pd

random.seed(11)
AS_OF = pd.Timestamp("2026-09-30")
REVIEW_MONTHS = {"High": 12, "Medium": 24, "Low": 36}

EVIDENCE = {
    "EDD": ("identity verification; beneficial ownership (25% threshold); "
            "source of funds; source of wealth; purpose of relationship; "
            "senior management sign-off; enhanced ongoing monitoring"),
    "CDD": ("identity verification; beneficial ownership (25% threshold); "
            "purpose and intended nature of relationship; "
            "standard ongoing monitoring"),
}


def decide(r):
    if r.risk_tier == "High" or r.pep:
        return "EDD"
    return "CDD"


def main():
    df = pd.read_csv("data/processed/risk_scored.csv")
    df["due_diligence"] = df.apply(decide, axis=1)
    df["required_evidence"] = df.due_diligence.map(EVIDENCE)
    df["name_match_review"] = ((df.best_score >= 75) & (df.best_score < 85))

    df["last_review"] = [AS_OF - pd.DateOffset(months=random.randint(0, 40))
                         for _ in range(len(df))]
    df["review_due"] = [lr + pd.DateOffset(months=REVIEW_MONTHS[t])
                        for lr, t in zip(df.last_review, df.risk_tier)]
    df["days_until_due"] = (df.review_due - AS_OF).dt.days
    df["review_status"] = pd.cut(df.days_until_due, [-10**6, -1, 30, 10**6],
                                 labels=["overdue", "due_30_days", "ok"])
    df.to_csv("data/processed/escalation.csv", index=False)

    summ = (df.groupby(["risk_tier", "due_diligence"]).size()
            .unstack(fill_value=0))
    overdue = (df.groupby(["risk_tier", "review_status"], observed=False).size()
               .unstack(fill_value=0))
    overdue.to_csv("docs/escalation_summary.csv")
    print("\nDue diligence by tier:\n", summ)
    print("\nReview status by tier:\n", overdue)
    print("\nAnalyst name-match review queue size:",
          int(df.name_match_review.sum()))


if __name__ == "__main__":
    main()