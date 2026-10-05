import duckdb
import yaml

from src.workflow_sim import simulate

CFG = yaml.safe_load(open("config.yaml", encoding="utf-8"))


def q(sql):
    con = duckdb.connect("data/processed/onboarding.duckdb", read_only=True)
    return con.sql(sql).fetchone()[0]


def run():
    c = dict(CFG)
    c["requests"] = 300
    leis = ["L%019d" % i for i in range(50)]
    return simulate(c, leis, set(leis[:10]))


def test_same_seed_gives_same_tables():
    assert run()["fact_request"].equals(run()["fact_request"])


def test_config_is_labelled_as_assumptions():
    assert "assumption" in open("config.yaml", encoding="utf-8").readline().lower()


def test_completed_plus_open_equals_received():
    total = q("SELECT COUNT(*) FROM fact_request")
    done = q("SELECT COUNT(*) FROM fact_request WHERE status = 'Completed'")
    open_ = q("SELECT COUNT(*) FROM fact_request WHERE status = 'Open'")
    assert total == CFG["requests"]
    assert done + open_ == total


def test_maker_is_never_the_checker():
    assert q("SELECT COUNT(*) FROM fact_request WHERE maker_id = checker_id") == 0
    assert q("SELECT COUNT(*) FROM fact_request WHERE maker_id NOT LIKE 'M%' OR checker_id NOT LIKE 'C%'") == 0


def test_every_request_points_to_a_real_entity():
    sql = "SELECT COUNT(*) FROM fact_request r LEFT JOIN dim_entity e ON e.lei = r.lei WHERE e.lei IS NULL"
    assert q(sql) == 0


def test_completion_is_not_before_receipt():
    assert q("SELECT COUNT(*) FROM fact_request WHERE completed_ts < received_ts") == 0
    assert q("SELECT COUNT(*) FROM fact_request WHERE tat_hours < 0") == 0


def test_requests_arrive_in_business_hours():
    sql = (
        "SELECT COUNT(*) FROM fact_request WHERE dayofweek(received_ts) NOT BETWEEN 1 AND 5 "
        "OR hour(received_ts) NOT BETWEEN 9 AND 17"
    )
    assert q(sql) == 0


def test_error_truth_is_kept_out_of_the_request_table():
    con = duckdb.connect("data/processed/onboarding.duckdb", read_only=True)
    cols = [r[0] for r in con.sql("DESCRIBE fact_request").fetchall()]
    assert "error_code" not in cols and "error_injected" not in cols


def test_injected_error_count_is_near_the_configured_rate():
    n = q("SELECT COUNT(*) FROM sim_error_truth")
    expected = CFG["requests"] * CFG["error_rate"]
    assert 0.6 * expected <= n <= 1.4 * expected


def test_every_logged_exception_exists_in_the_truth_table():
    sql = (
        "SELECT COUNT(*) FROM fact_exception x LEFT JOIN sim_error_truth t "
        "ON t.request_id = x.request_id AND t.detected_by_checker WHERE t.request_id IS NULL"
    )
    assert q(sql) == 0
