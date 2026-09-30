"""False-positive triage queue and alert-quality statistics.

Input : data/processed/escalation.csv
Output: data/processed/triage_queue.csv, docs/false_positive_summary.csv
Alert = name-match score >= 75. Bands: >=85 auto-escalate, 75-84 analyst review.
Ground truth comes from the labelled test set (expected_match).
"""
import pandas as pd

REVIEW, HIGH = 75, 85
TIER_RANK = {"High": 0, "Medium": 1, "Low": 2}


def main():
    df = pd.read_csv("data/processed/escalation.csv")
    df["alert"] = df.best_score >= REVIEW
    df["band"] = pd.cut(df.best_score, [-1, REVIEW - 0.01, HIGH - 0.01, 101],
                        labels=["clear", "analyst_review", "auto_escalate"])
    # a true match only counts if the CORRECT list entry was found
    df["true_alert"] = (df.expected_match == 1) & (df.correct_score >= REVIEW)
    df["false_alert"] = (df.expected_match == 0) & df.alert

    q = df[df.true_alert | df.false_alert].copy()
    q["tier_rank"] = q.risk_tier.map(TIER_RANK)
    q = q.sort_values(["tier_rank", "best_score"], ascending=[True, False])
    q.insert(0, "queue_rank", range(1, len(q) + 1))
    q["disposition"] = ""          # analyst fills: true match / false positive
    keep = ["queue_rank", "risk_tier", "band", "best_score", "query_name",
            "best_candidate", "country", "pep", "due_diligence",
            "category", "disposition"]
    q[keep].to_csv("data/processed/triage_queue.csv", index=False)

    rows = []
    for name, sub in [("all_alerts (>=75)", q),
                      ("auto_escalate (>=85)", q[q.band == "auto_escalate"]),
                      ("analyst_review (75-84)", q[q.band == "analyst_review"])]:
        tp, fp = int(sub.true_alert.sum()), int(sub.false_alert.sum())
        rows.append(dict(band=name, alerts=len(sub), true_alerts=tp,
                         false_positives=fp,
                         false_positive_share=round(fp / len(sub), 3)
                         if len(sub) else None))
    summ = pd.DataFrame(rows)
    summ.to_csv("docs/false_positive_summary.csv", index=False)

    print("\nAlert quality by band:\n", summ.to_string(index=False))
    print("\nFalse positives by category:\n",
          q[q.false_alert].groupby("category").size().to_string())
    print("\nQueue size by customer risk tier:\n",
          q.groupby("risk_tier").size().to_string())
    print("\nTop 10 of the queue:\n", q[keep].head(10)
          .drop(columns=["disposition"]).to_string(index=False))


if __name__ == "__main__":
    main()