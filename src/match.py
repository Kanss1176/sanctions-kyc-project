"""Fuzzy + phonetic screening of the test set against the sanctions table.

For each test query:
  1. rapidfuzz token_sort_ratio retrieves the top 15 candidate names
  2. each candidate is rescored with Jaro-Winkler and a Metaphone token overlap
  3. combined = 0.5*token_sort + 0.3*JaroWinkler + 0.2*phonetic  (0-100)

Outputs:
  data/processed/match_results.csv   per-query best scores (gitignored)
  docs/threshold_sweep.csv           precision / recall / FPR by threshold
"""
import re
import unicodedata
from pathlib import Path

import jellyfish
import pandas as pd
from rapidfuzz import fuzz, process

ENT = Path("data/processed/entities.csv")
TEST = Path("data_pointers/test_entities.csv")
OUT = Path("data/processed/match_results.csv")
SWEEP = Path("docs/threshold_sweep.csv")
W_TS, W_JW, W_PH = 0.5, 0.3, 0.2
TOP_K = 15


def prep(s):
    s = unicodedata.normalize("NFKD", str(s))
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = re.sub(r"[^\w\s]", " ", s.upper())
    return re.sub(r"\s+", " ", s).strip()


def metaphones(s):
    return {jellyfish.metaphone(t) for t in s.split() if t}


def phonetic_score(a, b):
    ma, mb = metaphones(a), metaphones(b)
    if not ma or not mb:
        return 0.0
    return len(ma & mb) / len(ma | mb)


def combined(q, cand, ts):
    qs = " ".join(sorted(q.split()))
    cs = " ".join(sorted(cand.split()))
    jw = jellyfish.jaro_winkler_similarity(qs, cs) * 100
    ph = phonetic_score(q, cand) * 100
    return W_TS * ts + W_JW * jw + W_PH * ph


def main():
    ent = pd.read_csv(ENT, dtype=str, low_memory=False)
    ent["m"] = ent["name"].map(prep)
    ent = ent[ent["m"] != ""].reset_index(drop=True)
    choices = ent["m"].tolist()
    src = ent["source"].tolist()
    sid = ent["source_id"].tolist()

    test = pd.read_csv(TEST, dtype=str)
    test["expected_match"] = test["expected_match"].astype(int)

    rows = []
    for i, t in enumerate(test.itertuples(), 1):
        q = prep(t.query_name)
        hits = process.extract(q, choices, scorer=fuzz.token_sort_ratio,
                               limit=TOP_K, score_cutoff=40)
        best, best_c, correct = 0.0, "", 0.0
        for cand, ts, idx in hits:
            s = combined(q, cand, ts)
            if s > best:
                best, best_c = s, cand
            if (t.category == "true_match" and src[idx] == t.source
                    and sid[idx] == t.source_id):
                correct = max(correct, s)
        rows.append(dict(test_id=t.test_id, query_name=t.query_name,
                         category=t.category, variant_type=t.variant_type,
                         expected_match=t.expected_match,
                         best_score=round(best, 1), best_candidate=best_c,
                         correct_score=round(correct, 1)))
        if i % 200 == 0:
            print(f"  scored {i}/{len(test)}")

    res = pd.DataFrame(rows)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    res.to_csv(OUT, index=False)

    pos = res[res.expected_match == 1]
    neg = res[res.expected_match == 0]
    sweep = []
    for th in range(50, 101, 5):
        tp = int((pos.correct_score >= th).sum())
        fp = int((neg.best_score >= th).sum())
        sweep.append(dict(threshold=th, true_pos=tp, false_pos=fp,
                          recall=round(tp / len(pos), 3),
                          precision=round(tp / (tp + fp), 3) if tp + fp else None,
                          false_positive_rate=round(fp / len(neg), 3)))
    sweep = pd.DataFrame(sweep)
    SWEEP.parent.mkdir(exist_ok=True)
    sweep.to_csv(SWEEP, index=False)

    print("\nThreshold sweep:")
    print(sweep.to_string(index=False))
    print("\nRecall at threshold 80 by variant type:")
    print(pos.assign(hit=pos.correct_score >= 80).groupby("variant_type").hit.mean().round(2))
    print("\nFalse positives at threshold 85 by category:")
    print(neg.assign(fp=neg.best_score >= 85).groupby("category").fp.sum())
    print("\nHighest-scoring negatives (review these by hand):")
    print(neg.sort_values("best_score", ascending=False).head(8)[
        ["query_name", "category", "best_score", "best_candidate"]].to_string(index=False))


if __name__ == "__main__":
    main()