import duckdb

AS_OF = "2026-10-04 16:00:00"

RULES = {
    "R01": "e.registration_status NOT IN ('ISSUED','ANNULLED','DUPLICATE')",
    "R02": "e.registration_status = 'ISSUED' AND e.next_renewal_ts < TIMESTAMP '" + AS_OF + "'",
    "R03": "e.entity_status = 'INACTIVE'",
    "R04": "e.legal_country <> e.hq_country",
    "R05": "p.missing_parent_unexplained = 1",
}


def fires(rule_id, **kw):
    row = {
        "registration_status": "ISSUED",
        "next_renewal_ts": "2027-01-01 00:00:00",
        "entity_status": "ACTIVE",
        "legal_country": "US",
        "hq_country": "US",
        "missing_parent_unexplained": 0,
    }
    row.update(kw)
    con = duckdb.connect()
    con.sql(
        "CREATE TABLE e AS SELECT '" + row["registration_status"] + "' AS registration_status, "
        "TIMESTAMP '" + row["next_renewal_ts"] + "' AS next_renewal_ts, "
        "'" + row["entity_status"] + "' AS entity_status, "
        "'" + row["legal_country"] + "' AS legal_country, "
        "'" + row["hq_country"] + "' AS hq_country"
    )
    con.sql("CREATE TABLE p AS SELECT " + str(row["missing_parent_unexplained"]) + " AS missing_parent_unexplained")
    n = con.sql("SELECT COUNT(*) FROM e, p WHERE " + RULES[rule_id]).fetchone()[0]
    return n == 1


def test_r01():
    assert fires("R01", registration_status="LAPSED")
    assert not fires("R01")
    assert not fires("R01", registration_status="ANNULLED")


def test_r02():
    assert fires("R02", next_renewal_ts="2026-01-01 00:00:00")
    assert not fires("R02")
    assert not fires("R02", registration_status="LAPSED", next_renewal_ts="2026-01-01 00:00:00")


def test_r03():
    assert fires("R03", entity_status="INACTIVE")
    assert not fires("R03")


def test_r04():
    assert fires("R04", hq_country="GB")
    assert not fires("R04")


def test_r05():
    assert fires("R05", missing_parent_unexplained=1)
    assert not fires("R05")
