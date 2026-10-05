import duckdb
import yaml

from src.scenarios import run, serve

CFG = yaml.safe_load(open("config.yaml", encoding="utf-8"))
LEIS = ["L%019d" % i for i in range(50)]


def small(policy):
    c = dict(CFG)
    c["requests"] = 300
    return run(c, LEIS, set(LEIS[:10]), policy, 4, 2)


def test_priority_serves_earliest_due_first():
    out = serve([(0, 10, 50), (0, 10, 5)], 1, "priority")
    assert out[1][0] == 0 and out[0][0] == 10


def test_fifo_serves_in_arrival_order():
    out = serve([(0, 10, 50), (1, 10, 5)], 1, "fifo")
    assert out[0][0] == 0 and out[1][0] == 10


def test_same_seed_gives_same_result():
    assert small("fifo").equals(small("fifo"))


def test_same_demand_across_policies():
    a, b = small("fifo"), small("priority")
    assert a["arr"].equals(b["arr"])
    assert int(a["error"].sum()) == int(b["error"].sum())


def test_no_completion_before_arrival():
    d = small("priority")
    assert (d["done"] >= d["arr"]).all()


def test_stored_scenarios_reconcile():
    con = duckdb.connect("data/processed/onboarding.duckdb", read_only=True)
    bad = con.sql(
        "SELECT COUNT(*) FROM scenario_results WHERE received <> completed + open_requests"
    ).fetchone()[0]
    all_rows = con.sql(
        "SELECT COUNT(*) FROM scenario_results WHERE request_type = 'ALL' AND received = " + str(CFG["requests"])
    ).fetchone()[0]
    assert bad == 0 and all_rows == len(CFG["scenarios"])


def test_serve_never_starts_a_job_before_it_is_ready():
    jobs = [(0, 100, 999), (1, 5, 999), (50, 5, 999), (60, 5, 999), (70, 5, 999)]
    out = serve(jobs, 2, "priority")
    assert all(out[i][0] >= jobs[i][0] for i in range(len(jobs)))


def test_seed_table_has_twenty_seeds_per_scenario():
    con = duckdb.connect("data/processed/onboarding.duckdb", read_only=True)
    bad = con.sql(
        "SELECT COUNT(*) FROM (SELECT scenario, COUNT(DISTINCT seed) AS n FROM scenario_seeds GROUP BY scenario) WHERE n <> 20"
    ).fetchone()[0]
    total = con.sql("SELECT COUNT(*) FROM scenario_seeds").fetchone()[0]
    assert bad == 0 and total == 60
