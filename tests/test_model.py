import duckdb
import pytest

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


@pytest.mark.xfail(reason="Known source-data anomaly: 1 entity has renewal before registration. Logged as a finding.", strict=False)
def test_renewal_not_before_registration():
    assert q("SELECT COUNT(*) FROM dim_entity WHERE next_renewal_ts < initial_reg_ts") == 0


def test_every_country_in_dim_country():
    assert q("""SELECT COUNT(*) FROM dim_entity e
                LEFT JOIN dim_country c ON e.legal_country = c.country_code
                WHERE c.country_code IS NULL""") == 0


def test_weights_reconstruct_population():
    total = q("SELECT SUM(sampling_weight) FROM dim_entity")
    assert round(total) == 1941854