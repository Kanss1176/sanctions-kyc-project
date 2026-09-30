"""Risk-tier assignment: weighted rule catalogue -> Low / Medium / High.

Inputs : data/processed/match_results.csv, data_pointers/test_entities.csv,
         rules/fatf_lists.json
Outputs: data/processed/risk_scored.csv, docs/risk_tier_summary.csv
Customer country and PEP flag are SYNTHETIC (seeded); the test set has none.
"""
import json
import random
from pathlib import Path

import pandas as pd

random.seed(7)
FATF = json.load(open("rules/fatf_lists.json", encoding="utf-8"))
BLACK = set(FATF["call_for_action"])
GREY = {c for c in FATF["increased_monitoring"] if "PASTE" not in c}
if not GREY:
    print("WARNING: grey list empty - fill rules/fatf_lists.json first")

LOW_RISK = ["UNITED STATES", "UNITED KINGDOM", "GERMANY", "FRANCE", "INDIA",
            "SINGAPORE", "CANADA", "AUSTRALIA", "JAPAN", "NETHERLANDS"]
POINTS = {"match_high": 50, "match_review": 25, "black": 40, "grey": 20,
          "pep": 25, "entity": 10}
HIGH_MATCH, REVIEW_MATCH = 85, 75


def synth_country():
    r = random.random()
    if r < 0.06:
        return random.choice(sorted(BLACK))
    if r < 0.22 and GREY:
        return random.choice(sorted(GREY))
    return random.choice(LOW_RISK)


def score_row(r):
    pts, why = 0, []
    if r.best_score >= HIGH_MATCH:
        pts += POINTS["match_high"]
        why.append("R1 match>=85")
    elif r.best_score >= REVIEW_MATCH:
        pts += POINTS["match_review"]
        why.append("R2 match 75-84")
    if r.country in BLACK:
        pts += POINTS["black"]
        why.append("R3 FATF call-for-action")
    elif r.country in GREY:
        pts += POINTS["grey"]
        why.append("R4 FATF increased monitoring")
    if r.pep:
        pts += POINTS["pep"]
        why.append("R5 PEP")
    if r.entity_type == "entity":
        pts += POINTS["entity"]
        why.append("R6 legal entity")
    tier = "High" if pts >= 60 else "Medium" if pts >= 25 else "Low"
    if r.best_score >= HIGH_MATCH or r.country in BLACK:
        tier = "High"
        why.append("OVERRIDE->High")
    return pd.Series(dict(risk_points=pts, risk_tier=tier,
                          rules_fired="; ".join(why)))


def main():
    m = pd.read_csv("data/processed/match_results.csv")
    t = pd.read_csv("data_pointers/test_entities.csv")[["test_id", "entity_type"]]
    df = m.merge(t, on="test_id")
    df["country"] = [synth_country() for _ in range(len(df))]
    df["pep"] = [(et == "individual" and random.random() < 0.05)
                 for et in df.entity_type]
    df = pd.concat([df, df.apply(score_row, axis=1)], axis=1)
    df.to_csv("data/processed/risk_scored.csv", index=False)

    summ = df.groupby(["risk_tier", "category"]).size().unstack(fill_value=0)
    Path("docs").mkdir(exist_ok=True)
    summ.to_csv("docs/risk_tier_summary.csv")
    print("\nTier x category:\n", summ)
    print("\nTier share:\n", df.risk_tier.value_counts(normalize=True).round(3))
    print("\nTop rules fired:\n", df.rules_fired.str.split("; ").explode()
          .value_counts().head(10))


if __name__ == "__main__":
    main()