import glob

import duckdb
import pandas as pd

con = duckdb.connect("data/processed/onboarding.duckdb", read_only=True)


def sql(n):
    path = glob.glob("sql/metrics/" + n + "_*.sql")[0]
    return con.sql(open(path, encoding="utf-8").read()).df()


def req():
    return con.sql("SELECT * FROM fact_request").df()


def test_turnaround_matches_python():
    r = sql("01").iloc[0]
    d = req()
    d = d[d.status == "Completed"]
    assert r.completed == len(d)
    assert abs(r.median_tat_h - round(d.tat_hours.astype(float).median(), 2)) < 0.011
    assert abs(r.p90_tat_h - round(d.tat_hours.astype(float).quantile(0.9), 2)) < 0.011


def test_sla_breach_matches_python():
    s = sql("02")
    d = req()
    d = d[d.status == "Completed"]
    assert s.breached.sum() == int(d.sla_breached.astype(bool).sum())
    assert s.completed.sum() == len(d)


def test_first_time_right_matches_python():
    r = sql("03").iloc[0]
    d = req()
    d = d[d.status == "Completed"]
    assert abs(r.first_time_right - d.first_time_right.astype(bool).mean()) < 0.0001


def test_errors_found_equals_exception_table():
    n = con.sql("SELECT COUNT(*) FROM fact_exception").fetchone()[0]
    assert int(sql("04").errors_found.sum()) == n


def test_maker_error_rows_add_up():
    s = sql("05")
    assert int(s.completed.sum()) == int((req().status == "Completed").sum())


def test_escalation_matches_python():
    r = sql("06").iloc[0]
    assert r.escalated == int(req().escalated.astype(bool).sum())


def test_ageing_covers_every_open_request():
    n = int((req().status == "Open").sum())
    assert int(sql("07").open_requests.sum()) == n


def test_queue_is_complete_unique_and_ordered():
    q = sql("08")
    n = int((req().status == "Open").sum())
    assert len(q) == n
    assert q.request_id.is_unique
    assert list(q.queue_rank) == list(range(1, n + 1))
    assert list(q.priority_band) == sorted(q.priority_band)


def test_queue_bands_follow_the_rule():
    q = sql("08")
    assert (q[q.hours_left < 0].priority_band == 1).all()
    assert (q[(q.hours_left >= 0) & (q.max_severity >= 3)].priority_band == 2).all()
