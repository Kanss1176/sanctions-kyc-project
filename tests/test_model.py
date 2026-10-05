import duckdb

con = duckdb.connect("data/processed/onboarding.duckdb", read_only=True)


def q(sql):
    return con.sql(sql).fetchone()[0]


def test_row_count_matches_sample():
    sample = duckdb.sql(
        "SELECT COUNT(*) FROM read_parquet('data/processed/entity_sample.parquet')"
    ).fetchone()[0]
    assert q("SELECT COUNT(*) FROM dim_entity") == sample


def test_lei_is_20_chars_and_unique():
    assert q("SELECT COUNT(*) FROM dim_entity WHERE LENGTH(lei) <> 20") == 0
    assert q("SELECT COUNT(*) - COUNT(DISTINCT lei) FROM dim_entity") == 0


def test_registration_status_vocabulary():
    allowed = ("ISSUED", "LAPSED", "RETIRED", "DUPLICATE", "ANNULLED",
               "PENDING_TRANSFER", "PENDING_ARCHIVAL")
    bad = q("SELECT COUNT(*) FROM dim_entity WHERE registration_status NOT IN " + str(allowed))
    assert bad == 0


def test_dates_parse():
    assert q("SELECT COUNT(*) FROM dim_entity WHERE initial_reg_ts IS NULL") == 0
    assert q("SELECT COUNT(*) FROM dim_entity WHERE next_renewal_ts IS NULL") == 0


def test_every_renewal_anomaly_is_logged():
    violations = q("SELECT COUNT(*) FROM dim_entity WHERE next_renewal_ts < initial_reg_ts")
    logged = q("SELECT COUNT(*) FROM dq_finding WHERE check_id = 'DQ01'")
    assert violations == logged


def test_unexpected_anomalies_are_zero():
    assert q("SELECT COUNT(*) FROM dq_finding WHERE check_id = 'DQ01' AND registration_status <> 'ANNULLED'") == 0


def test_every_country_in_dim_country():
    sql = (
        "SELECT COUNT(*) FROM dim_entity e "
        "LEFT JOIN dim_country c ON e.legal_country = c.country_code "
        "WHERE c.country_code IS NULL"
    )
    assert q(sql) == 0


def test_weights_reconstruct_population():
    total = q("SELECT SUM(sampling_weight) FROM dim_entity")
    assert round(total) == 1941854


def test_parent_table_covers_every_entity():
    assert q("SELECT COUNT(*) FROM fact_parent") == q("SELECT COUNT(*) FROM dim_entity")


def test_parent_flags_are_consistent():
    sql = (
        "SELECT COUNT(*) FROM fact_parent "
        "WHERE has_direct_parent = 0 AND has_ultimate_parent = 0 "
        "AND missing_parent_explained + missing_parent_unexplained <> 1"
    )
    assert q(sql) == 0