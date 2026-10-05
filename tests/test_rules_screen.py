import json

import duckdb

from src.onboarding_rules import FATF_CODES, RULES


def fires(rule_id, best_score=0.0, legal="US", hq="US"):
    con = duckdb.connect()
    con.sql("CREATE TABLE e AS SELECT '" + legal + "' AS legal_country, '" + hq + "' AS hq_country")
    con.sql("CREATE TABLE s AS SELECT " + str(best_score) + " AS best_score")
    return con.sql("SELECT COUNT(*) FROM e, s WHERE " + RULES[rule_id]).fetchone()[0] == 1


def test_r06():
    assert fires("R06", best_score=85.0)
    assert fires("R06", best_score=80.0)
    assert not fires("R06", best_score=79.9)


def test_r07():
    assert fires("R07", legal="IR")
    assert fires("R07", hq="KP")
    assert fires("R07", legal="VG")
    assert not fires("R07")


def test_every_fatf_name_is_mapped():
    d = json.load(open("rules/fatf_lists.json", encoding="utf-8"))
    names = set(d["call_for_action"] + d["increased_monitoring"])
    assert len(FATF_CODES) == len(names)


def test_fact_screen_covers_every_entity():
    con = duckdb.connect("data/processed/onboarding.duckdb", read_only=True)
    assert con.sql("SELECT COUNT(*) FROM fact_screen").fetchone()[0] == con.sql("SELECT COUNT(*) FROM dim_entity").fetchone()[0]


def test_fact_screen_stores_no_names():
    con = duckdb.connect("data/processed/onboarding.duckdb", read_only=True)
    cols = [r[0] for r in con.sql("DESCRIBE fact_screen").fetchall()]
    assert cols == ["lei", "best_score", "list_source", "list_id"]
