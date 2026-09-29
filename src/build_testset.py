"""Build the labelled test-entity set for the screening evaluation.

Categories (expected_match = 1 for true_match, 0 otherwise):
  true_match    real sanctioned name, perturbed with a realistic variant
  near_miss     sanctioned name with one distinctive token changed (a different party)
  true_negative SEC EDGAR company names + synthetic person names (clearly labelled)

Output: data_pointers/test_entities.csv (tracked in git on purpose; small and seeded).
"""
import json
import random
import re
import unicodedata
from pathlib import Path

import pandas as pd

random.seed(42)
ENT = Path("data/processed/entities.csv")
SEC = Path("data/raw/sec_company_tickers.json")
OUT = Path("data_pointers/test_entities.csv")

GIVEN = ["JAMES", "MARIA", "JOHN", "ANNA", "DAVID", "ELENA", "MICHAEL", "SARAH",
         "ROBERT", "LINDA", "DANIEL", "PRIYA", "CARLOS", "FATIMA", "WEI", "OLIVIA",
         "THOMAS", "AISHA", "PETER", "NINA", "LUCAS", "SOFIA", "HENRY", "MEERA",
         "PAUL", "IRENE", "ANDREW", "LAILA", "KEVIN", "HELEN"]
SURNAME = ["SMITH", "JOHNSON", "WILLIAMS", "BROWN", "JONES", "GARCIA", "MILLER",
           "DAVIS", "RODRIGUEZ", "MARTINEZ", "HERNANDEZ", "LOPEZ", "GONZALEZ",
           "WILSON", "ANDERSON", "TAYLOR", "MOORE", "JACKSON", "MARTIN", "LEE",
           "PEREZ", "THOMPSON", "WHITE", "HARRIS", "SANCHEZ", "CLARK", "RAMIREZ",
           "LEWIS", "ROBINSON", "WALKER", "YOUNG", "ALLEN", "KING", "WRIGHT",
           "SCOTT", "TORRES", "NGUYEN", "HILL", "FLORES", "PATEL"]
SWAP_WORDS = ["GLOBAL", "PACIFIC", "NORTHERN", "ALPHA", "SUMMIT", "HORIZON",
              "CENTRAL", "UNITED", "ATLANTIC", "PIONEER", "ROYAL", "EASTERN"]
STOP = {"LIMITED", "LTD", "COMPANY", "CO", "CORPORATION", "CORP", "INC", "LLC",
        "GROUP", "BANK", "TRADING", "OF", "THE", "AND", "JSC", "OOO", "AG", "GMBH"}
SUFFIX = {"LIMITED": "LTD", "COMPANY": "CO", "CORPORATION": "CORP",
          "INCORPORATED": "INC", "INTERNATIONAL": "INTL", "TRADING": "TRDG"}
PHON = [("PH", "F"), ("OU", "U"), ("KH", "H"), ("CK", "K"), ("Y", "I"),
        ("W", "V"), ("Z", "S"), ("C", "K"), ("SCH", "SH"), ("OO", "U")]


def norm(s):
    s = re.sub(r"[^\w\s]", " ", str(s).upper())
    return re.sub(r"\s+", " ", s).strip()


def strip_accents(s):
    return "".join(c for c in unicodedata.normalize("NFKD", s)
                   if not unicodedata.combining(c))


def latin_ratio(s):
    s = strip_accents(s)
    return sum(ord(c) < 128 for c in s) / max(len(s), 1)


def drop_char(s):
    if len(s) < 5:
        return s
    i = random.randrange(1, len(s) - 1)
    return s[:i] + s[i + 1:]


def swap_adjacent(s):
    if len(s) < 5:
        return s
    i = random.randrange(1, len(s) - 2)
    return s[:i] + s[i + 1] + s[i] + s[i + 2:]


def phonetic(s):
    u = s.upper()
    rules = PHON[:]
    random.shuffle(rules)
    for a, b in rules:
        if a in u:
            return u.replace(a, b, 1)
    return u


def reorder(s):
    if "," in s:
        last, first = s.split(",", 1)
        return f"{first.strip()} {last.strip()}"
    t = s.split()
    return " ".join([t[-1]] + t[:-1]) if len(t) > 1 else s


def suffix_abbrev(s):
    toks = s.split()
    out = [SUFFIX.get(t.upper().strip(".,"), t) for t in toks]
    return " ".join(out)


def case_punct(s):
    return strip_accents(norm(s)).lower()


VARIANTS = {
    "individual": {"reorder": reorder, "drop_char": drop_char,
                   "swap_adjacent": swap_adjacent, "phonetic": phonetic,
                   "case_punct": case_punct},
    "entity": {"suffix_abbrev": suffix_abbrev, "drop_char": drop_char,
               "swap_adjacent": swap_adjacent, "phonetic": phonetic,
               "case_punct": case_punct},
}


def make_variant(name, etype):
    options = list(VARIANTS[etype].items())
    random.shuffle(options)
    for vname, fn in options:
        v = fn(name)
        if norm(v) != norm(name):
            return v, vname
    return name, "exact"


def near_miss(name, etype):
    n = norm(reorder(name)) if etype == "individual" else norm(name)
    toks = n.split()
    if etype == "individual":
        if len(toks) < 2:
            return None
        new_given = random.choice([g for g in GIVEN if g != toks[0]])
        return " ".join([new_given] + toks[1:])
    if len(toks) < 3:
        return None
    cand = [i for i, t in enumerate(toks) if len(t) >= 4 and t not in STOP]
    if not cand:
        return None
    i = cand[0]
    toks[i] = random.choice([w for w in SWAP_WORDS if w != toks[i]])
    return " ".join(toks)


def main():
    df = pd.read_csv(ENT, low_memory=False)
    sanctioned = set(df["name_norm"].dropna())
    prim = df[(df.name_type == "primary") & df.entity_type.isin(["individual", "entity"])]
    prim = prim[prim.name.map(lambda s: 8 <= len(str(s)) <= 70 and latin_ratio(str(s)) > 0.9)]

    rows = []

    def add(query, match, cat, variant, orig=None, src=None, sid=None, etype=None):
        rows.append(dict(query_name=query, expected_match=match, category=cat,
                         variant_type=variant, original_name=orig,
                         source=src, source_id=sid, entity_type=etype))

    # true matches: 3 sources x 2 types x 60
    for (src, et), grp in prim.groupby(["source", "entity_type"]):
        pick = grp.sample(n=min(60, len(grp)), random_state=1)
        for r in pick.itertuples():
            q, v = make_variant(str(r.name), et)
            add(q, 1, "true_match", v, r.name, src, r.source_id, et)

    # near misses: 90 per type
    for et in ("individual", "entity"):
        pool = prim[prim.entity_type == et].sample(frac=1, random_state=2)
        made = 0
        for r in pool.itertuples():
            q = near_miss(str(r.name), et)
            if q and norm(q) not in sanctioned:
                add(q, 0, "near_miss", "token_changed", r.name, r.source, r.source_id, et)
                made += 1
            if made >= 90:
                break

    # true negatives: SEC companies
    sec = json.load(open(SEC, encoding="utf-8"))
    titles = list({v["title"] for v in sec.values()})
    random.shuffle(titles)
    kept = 0
    for t in titles:
        if norm(t) not in sanctioned:
            add(t, 0, "true_negative", "sec_edgar_company", None, "SEC", None, "entity")
            kept += 1
        if kept >= 200:
            break

    # true negatives: synthetic person names (disclosed as synthetic)
    kept = 0
    while kept < 200:
        q = f"{random.choice(GIVEN)} {random.choice(SURNAME)}"
        if norm(q) not in sanctioned:
            add(q, 0, "true_negative", "synthetic_person", None, "SYNTHETIC", None, "individual")
            kept += 1

    out = pd.DataFrame(rows).drop_duplicates(subset=["query_name", "category"])
    out.insert(0, "test_id", range(1, len(out) + 1))
    OUT.parent.mkdir(exist_ok=True)
    out.to_csv(OUT, index=False, encoding="utf-8")
    print(out.groupby(["category", "entity_type"]).size())
    print("\nVariant types:")
    print(out.groupby(["category", "variant_type"]).size())
    print(f"\nTotal test rows: {len(out)}  ->  {OUT}")
    print("\nSample:")
    print(out.sample(10, random_state=3)[["query_name", "category", "variant_type", "original_name"]].to_string())


if __name__ == "__main__":
    main()