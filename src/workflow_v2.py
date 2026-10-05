import datetime as dt
import random

import pandas as pd

from src.scenarios import serve
from src.workflow_sim import ERRORS, business_days, dim_tables


def simulate_queue(cfg, leis, severe, policy="fifo"):
    rng = random.Random(cfg["seed"])
    hour = cfg["workday_start_hour"]
    dmin = cfg["workday_hours"] * 60
    start = dt.date.fromisoformat(cfg["window_start"])
    end = dt.date.fromisoformat(cfg["window_end"])
    days, window = business_days(start, end)
    asof = window * dmin

    def ts(w):
        d, m = divmod(int(round(w)), dmin)
        return dt.datetime.combine(days[d], dt.time(hour)) + dt.timedelta(minutes=m)

    def seen(w):
        return ts(w) if w <= asof else None

    types = cfg["request_types"]
    names = list(types)
    weights = [types[k]["share"] for k in names]
    makers = ["M%d" % (i + 1) for i in range(cfg["makers"])]
    checkers = ["C%d" % (i + 1) for i in range(cfg["checkers"])]
    codes = [e[0] for e in ERRORS]
    cw = [e[2] for e in ERRORS]
    lo, hi = cfg["escalation_delay_hours"]
    arrivals = sorted(rng.randrange(asof) for _ in range(cfg["requests"]))
    reqs = []
    for arr in arrivals:
        lei = rng.choice(leis)
        t = rng.choices(names, weights)[0]
        sp = types[t]
        error = rng.random() < cfg["error_rate"]
        reqs.append({
            "lei": lei, "type": t, "arr": arr, "due": arr + sp["sla_hours"] * 60,
            "mwork": sp["maker_minutes"] * rng.uniform(0.7, 1.3),
            "cwork": sp["checker_minutes"] * rng.uniform(0.7, 1.3),
            "delay": rng.uniform(lo, hi) * 60 if lei in severe else 0.0,
            "error": error,
            "code": rng.choices(codes, cw)[0] if error else None,
            "caught": bool(error and rng.random() < cfg["checker_detection_rate"]),
        })
    ms = serve([(r["arr"], r["mwork"], r["due"]) for r in reqs], len(makers), policy)
    cj = [(ms[i][1] + r["delay"], r["cwork"], r["due"]) for i, r in enumerate(reqs)]
    cs = serve(cj, len(checkers), policy)
    req, exc, esc, truth = [], [], [], []

    for i, r in enumerate(reqs):
        rid = "REQ%05d" % (i + 1)
        spec = types[r["type"]]
        m_done, c_done = ms[i][1], cs[i][1]
        extra = (r["mwork"] * cfg["rework_factor"] + r["cwork"] * 0.7) if r["caught"] else 0.0
        done = c_done + extra
        ok = done <= asof
        escalated = r["lei"] in severe
        req.append({
            "request_id": rid, "lei": r["lei"], "request_type": r["type"],
            "received_ts": ts(r["arr"]), "due_ts": ts(r["due"]),
            "maker_id": makers[ms[i][2]], "checker_id": checkers[cs[i][2]],
            "maker_done_ts": seen(m_done), "completed_ts": seen(done),
            "status": "Completed" if ok else "Open",
            "tat_hours": round((done - r["arr"]) / 60, 2) if ok else None,
            "sla_hours": spec["sla_hours"],
            "sla_breached": (done > r["due"]) if ok else None,
            "rework_count": int(r["caught"]) if ok else None,
            "first_time_right": (not r["caught"]) if ok else None,
            "has_error": r["caught"] if ok else None,
            "escalated": bool(escalated and m_done <= asof),
        })
        if r["caught"] and c_done <= asof:
            exc.append({"request_id": rid, "lei": r["lei"], "error_code": r["code"], "detected_ts": ts(c_done)})
        if escalated and m_done <= asof:
            esc.append({"request_id": rid, "lei": r["lei"], "escalated_ts": ts(m_done),
                        "resolved_ts": seen(m_done + r["delay"])})
        if r["error"]:
            truth.append({"request_id": rid, "error_code": r["code"], "detected_by_checker": r["caught"]})

    out = dim_tables(cfg, makers, checkers)
    fr = pd.DataFrame(req)
    fr["tat_hours"] = fr["tat_hours"].astype("Float64")
    fr["rework_count"] = fr["rework_count"].astype("Int64")
    for col in ["sla_breached", "first_time_right", "has_error"]:
        fr[col] = fr[col].astype("boolean")
    out["fact_request"] = fr
    out["fact_exception"] = pd.DataFrame(exc, columns=["request_id", "lei", "error_code", "detected_ts"])
    out["fact_escalation"] = pd.DataFrame(esc, columns=["request_id", "lei", "escalated_ts", "resolved_ts"])
    out["sim_error_truth"] = pd.DataFrame(truth, columns=["request_id", "error_code", "detected_by_checker"])
    return out
