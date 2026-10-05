import datetime as dt
import random

import pandas as pd

ERRORS = [
    ("R08", "Required document missing", 0.30),
    ("R09", "Document expired", 0.20),
    ("R10", "Signatory authority evidence missing", 0.20),
    ("R11", "Form name differs from registry name", 0.20),
    ("R12", "Data entry error", 0.10),
]


def business_days(start, end, extra=60):
    days, d = [], start
    while d <= end:
        if d.weekday() < 5:
            days.append(d)
        d += dt.timedelta(days=1)
    window = len(days)
    n = 0
    while n < extra:
        if d.weekday() < 5:
            days.append(d)
            n += 1
        d += dt.timedelta(days=1)
    return days, window


def dim_tables(cfg, makers, checkers):
    types = cfg["request_types"]
    proc = [(m, "maker") for m in makers] + [(c, "checker") for c in checkers]
    rt = [(k, v["share"], v["sla_hours"], v["maker_minutes"], v["checker_minutes"], "assumption") for k, v in types.items()]
    return {
        "dim_processor": pd.DataFrame(proc, columns=["processor_id", "role"]),
        "dim_request_type": pd.DataFrame(
            rt, columns=["request_type", "share", "sla_business_hours", "maker_minutes", "checker_minutes", "source"]
        ),
        "dim_error_type": pd.DataFrame(
            [(c, d, w, "simulated") for c, d, w in ERRORS],
            columns=["error_code", "description", "weight", "source"],
        ),
    }


def simulate(cfg, leis, severe):
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
    mfree = {m: 0 for m in makers}
    cfree = {c: 0 for c in checkers}
    codes = [e[0] for e in ERRORS]
    cw = [e[2] for e in ERRORS]
    lo, hi = cfg["escalation_delay_hours"]
    arrivals = sorted(rng.randrange(asof) for _ in range(cfg["requests"]))
    req, exc, esc, truth = [], [], [], []

    for i, arr in enumerate(arrivals, 1):
        rid = "REQ%05d" % i
        lei = rng.choice(leis)
        t = rng.choices(names, weights)[0]
        spec = types[t]
        due = arr + spec["sla_hours"] * 60
        m = min(makers, key=lambda x: mfree[x])
        work = spec["maker_minutes"] * rng.uniform(0.7, 1.3)
        m_done = max(arr, mfree[m]) + work
        mfree[m] = m_done
        escalated = lei in severe
        ready = m_done + (rng.uniform(lo, hi) * 60 if escalated else 0)
        c = min(checkers, key=lambda x: cfree[x])
        done = max(ready, cfree[c]) + spec["checker_minutes"] * rng.uniform(0.7, 1.3)
        cfree[c] = done
        error = rng.random() < cfg["error_rate"]
        code = rng.choices(codes, cw)[0] if error else None
        detected = error and rng.random() < cfg["checker_detection_rate"]
        det_at = None
        if detected:
            det_at = done
            d2 = max(done, mfree[m]) + work * cfg["rework_factor"]
            mfree[m] = d2
            c2 = min(checkers, key=lambda x: cfree[x])
            done = max(d2, cfree[c2]) + spec["checker_minutes"] * 0.7
            cfree[c2] = done
        ok = done <= asof
        req.append({
            "request_id": rid, "lei": lei, "request_type": t,
            "received_ts": ts(arr), "due_ts": ts(due),
            "maker_id": m, "checker_id": c,
            "maker_done_ts": seen(m_done), "completed_ts": seen(done),
            "status": "Completed" if ok else "Open",
            "tat_hours": round((done - arr) / 60, 2) if ok else None,
            "sla_hours": spec["sla_hours"],
            "sla_breached": (done > due) if ok else None,
            "rework_count": int(detected) if ok else None,
            "first_time_right": (not detected) if ok else None,
            "has_error": bool(detected) if ok else None,
            "escalated": bool(escalated and m_done <= asof),
        })
        if detected and det_at <= asof:
            exc.append({"request_id": rid, "lei": lei, "error_code": code, "detected_ts": ts(det_at)})
        if escalated and m_done <= asof:
            esc.append({"request_id": rid, "lei": lei, "escalated_ts": ts(m_done), "resolved_ts": seen(ready)})
        if error:
            truth.append({"request_id": rid, "error_code": code, "detected_by_checker": bool(detected)})

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
