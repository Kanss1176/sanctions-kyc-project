import datetime as dt
import heapq
import random

import pandas as pd

from src.workflow_sim import business_days


def serve(jobs, n_servers, policy):
    """jobs: list of (ready, duration, due). Returns (start, finish, server) per job."""
    order = sorted(range(len(jobs)), key=lambda i: (jobs[i][0], i))
    free = [0.0] * n_servers
    waiting, out, p = [], [None] * len(jobs), 0
    clock = 0.0
    while p < len(order) or waiting:
        s = min(range(n_servers), key=lambda k: free[k])
        t = max(free[s], clock)
        if not waiting and jobs[order[p]][0] > t:
            t = jobs[order[p]][0]
        clock = t
        while p < len(order) and jobs[order[p]][0] <= t:
            i = order[p]
            key = (jobs[i][2], jobs[i][0], i) if policy == "priority" else (jobs[i][0], i)
            heapq.heappush(waiting, (key, i))
            p += 1
        _, i = heapq.heappop(waiting)
        free[s] = t + jobs[i][1]
        out[i] = (t, free[s], s)
    return out


def run(cfg, leis, severe, policy, makers, checkers):
    rng = random.Random(cfg["seed"])
    dmin = cfg["workday_hours"] * 60
    start = dt.date.fromisoformat(cfg["window_start"])
    end = dt.date.fromisoformat(cfg["window_end"])
    days, window = business_days(start, end)
    asof = window * dmin
    types = cfg["request_types"]
    names = list(types)
    weights = [types[k]["share"] for k in names]
    lo, hi = cfg["escalation_delay_hours"]
    arrivals = sorted(rng.randrange(asof) for _ in range(cfg["requests"]))
    reqs = []
    for arr in arrivals:
        lei = rng.choice(leis)
        t = rng.choices(names, weights)[0]
        sp = types[t]
        reqs.append({
            "arr": arr, "type": t, "due": arr + sp["sla_hours"] * 60,
            "mwork": sp["maker_minutes"] * rng.uniform(0.7, 1.3),
            "cwork": sp["checker_minutes"] * rng.uniform(0.7, 1.3),
            "delay": rng.uniform(lo, hi) * 60 if lei in severe else 0.0,
            "error": rng.random() < cfg["error_rate"],
            "caught": rng.random() < cfg["checker_detection_rate"],
        })
    ms = serve([(r["arr"], r["mwork"], r["due"]) for r in reqs], makers, policy)
    cj = [(ms[i][1] + r["delay"], r["cwork"], r["due"]) for i, r in enumerate(reqs)]
    cs = serve(cj, checkers, policy)
    rows = []
    for i, r in enumerate(reqs):
        det = r["error"] and r["caught"]
        extra = (r["mwork"] * cfg["rework_factor"] + r["cwork"] * 0.7) if det else 0.0
        done = cs[i][1] + extra
        rows.append({
            "request_type": r["type"], "arr": r["arr"], "due": r["due"], "done": done,
            "completed": done <= asof, "tat_h": (done - r["arr"]) / 60,
            "breached": done > r["due"], "error": r["error"], "detected": det,
        })
    return pd.DataFrame(rows)
