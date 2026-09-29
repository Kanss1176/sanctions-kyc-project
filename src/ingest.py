"""Ingest OFAC, UN and EU sanctions lists into one canonical entity table.

Output: data/processed/entities.csv and data/processed/sanctions.db (table: entities)
One row per name (primary names and aliases each get a row).
"""
import sqlite3
import xml.etree.ElementTree as ET
from pathlib import Path

import pandas as pd

RAW = Path("data/raw")
OUT = Path("data/processed")
OUT.mkdir(parents=True, exist_ok=True)

COLS = ["source", "source_id", "name", "name_type", "alias_type",
        "entity_type", "country", "program", "list_date", "remarks"]


def local(tag):
    """Strip an XML namespace: '{ns}name' -> 'name'."""
    return tag.split("}")[-1]


def clean(x):
    if x is None:
        return None
    x = str(x).strip()
    return None if x in ("", "-0-") else x


def child_text(elem, name):
    for c in elem:
        if local(c.tag) == name:
            return clean(c.text)
    return None


def child_values(elem, name):
    """Text of <name><VALUE>..</VALUE></name> children, as a list."""
    out = []
    for c in elem:
        if local(c.tag) == name:
            for v in c:
                if local(v.tag) == "VALUE" and clean(v.text):
                    out.append(clean(v.text))
    return out


# ---------------------------------------------------------------- OFAC
def load_ofac():
    sdn = pd.read_csv(
        RAW / "sdn.csv", header=None, dtype=str, encoding="latin-1",
        names=["ent_num", "name", "sdn_type", "program", "title", "call_sign",
               "vess_type", "tonnage", "grt", "vess_flag", "vess_owner", "remarks"],
    ).apply(lambda s: s.str.strip())
    sdn = sdn.replace("-0-", pd.NA)
    sdn["sdn_type"] = sdn["sdn_type"].fillna("entity").str.lower()

    alt = pd.read_csv(
        RAW / "alt.csv", header=None, dtype=str, encoding="latin-1",
        names=["ent_num", "alt_num", "alt_type", "name", "remarks"],
    ).apply(lambda s: s.str.strip())
    alt = alt.replace("-0-", pd.NA)

    meta = sdn.set_index("ent_num")[["sdn_type", "program"]]

    primary = pd.DataFrame({
        "source": "OFAC", "source_id": sdn["ent_num"], "name": sdn["name"],
        "name_type": "primary", "alias_type": pd.NA,
        "entity_type": sdn["sdn_type"], "country": pd.NA,
        "program": sdn["program"], "list_date": pd.NA, "remarks": sdn["remarks"],
    })
    aliases = alt.join(meta, on="ent_num")
    aliases = pd.DataFrame({
        "source": "OFAC", "source_id": aliases["ent_num"], "name": aliases["name"],
        "name_type": "alias", "alias_type": aliases["alt_type"],
        "entity_type": aliases["sdn_type"], "country": pd.NA,
        "program": aliases["program"], "list_date": pd.NA,
        "remarks": aliases["remarks"],
    })
    return pd.concat([primary, aliases], ignore_index=True)


# ---------------------------------------------------------------- UN
def load_un():
    root = ET.parse(RAW / "un_consolidated.xml").getroot()
    rows = []
    for section, etype in (("INDIVIDUALS", "individual"), ("ENTITIES", "entity")):
        sec = next((c for c in root if local(c.tag) == section), None)
        if sec is None:
            continue
        for rec in sec:
            sid = child_text(rec, "DATAID")
            parts = [child_text(rec, k) for k in
                     ("FIRST_NAME", "SECOND_NAME", "THIRD_NAME", "FOURTH_NAME")]
            name = " ".join(p for p in parts if p)
            program = child_text(rec, "UN_LIST_TYPE")
            listed = child_text(rec, "LISTED_ON")
            remarks = child_text(rec, "COMMENTS1")
            countries = child_values(rec, "NATIONALITY")
            if not countries:
                for c in rec.iter():
                    if local(c.tag) == "COUNTRY" and clean(c.text):
                        countries.append(clean(c.text))
            country = countries[0] if countries else None
            base = dict(source="UN", source_id=sid, entity_type=etype,
                        country=country, program=program, list_date=listed,
                        remarks=remarks)
            rows.append({**base, "name": name, "name_type": "primary",
                         "alias_type": None})
            for a in rec:
                if local(a.tag) in ("INDIVIDUAL_ALIAS", "ENTITY_ALIAS"):
                    an = child_text(a, "ALIAS_NAME")
                    if an:
                        rows.append({**base, "name": an, "name_type": "alias",
                                     "alias_type": child_text(a, "QUALITY")})
    return pd.DataFrame(rows)


# ---------------------------------------------------------------- EU
def load_eu():
    root = ET.parse(RAW / "eu_consolidated.xml").getroot()
    type_map = {"person": "individual", "enterprise": "entity"}
    rows = []
    for ent in root:
        if local(ent.tag) != "sanctionEntity":
            continue
        sid = ent.get("euReferenceNumber") or ent.get("logicalId")
        remarks = None
        program = list_date = country = None
        etype = "other"
        aliases = []
        for c in ent.iter():
            t = local(c.tag)
            if t == "remark" and remarks is None:
                remarks = clean(c.text)
            elif t == "regulation" and program is None:
                program = clean(c.get("programme")) or clean(c.get("numberTitle"))
                list_date = clean(c.get("entryIntoForceDate")) or clean(
                    c.get("publicationDate"))
            elif t == "subjectType":
                etype = type_map.get(c.get("code"), c.get("code") or "other")
            elif t in ("citizenship", "address") and country is None:
                country = clean(c.get("countryDescription"))
            elif t == "nameAlias":
                whole = clean(c.get("wholeName"))
                if not whole:
                    whole = " ".join(p for p in (
                        clean(c.get("firstName")), clean(c.get("middleName")),
                        clean(c.get("lastName"))) if p)
                if whole:
                    aliases.append(whole)
        seen = set()
        for i, n in enumerate(aliases):
            if n in seen:
                continue
            seen.add(n)
            rows.append(dict(source="EU", source_id=sid, name=n,
                             name_type="primary" if i == 0 else "alias",
                             alias_type=None, entity_type=etype,
                             country=country, program=program,
                             list_date=list_date, remarks=remarks))
    return pd.DataFrame(rows)


def main():
    frames = {"OFAC": load_ofac(), "UN": load_un(), "EU": load_eu()}
    df = pd.concat(frames.values(), ignore_index=True)[COLS]
    df["name"] = df["name"].astype("string").str.strip()
    df = df[df["name"].notna() & (df["name"] != "")]
    df["name_norm"] = (df["name"].str.upper()
                       .str.replace(r"[^\w\s]", " ", regex=True)
                       .str.replace(r"\s+", " ", regex=True).str.strip())
    df.insert(0, "entity_key", range(1, len(df) + 1))

    df.to_csv(OUT / "entities.csv", index=False, encoding="utf-8")
    with sqlite3.connect(OUT / "sanctions.db") as con:
        df.to_sql("entities", con, if_exists="replace", index=False)

    print("\nRows per source and name type:")
    print(df.groupby(["source", "name_type"]).size().unstack(fill_value=0))
    print("\nEntity types per source:")
    print(df.groupby(["source", "entity_type"]).size())
    print("\nMissing values (%):")
    print((df[COLS].isna().mean() * 100).round(1))
    print("\nSaved data/processed/entities.csv and sanctions.db")


if __name__ == "__main__":
    main()
    