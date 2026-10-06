import duckdb

con = duckdb.connect("data/processed/onboarding.duckdb", read_only=True)
one = lambda s: con.sql(s).fetchone()[0]
n_req = one("SELECT COUNT(*) FROM fact_request")
n_done = one("SELECT COUNT(*) FROM fact_request WHERE status='Completed'")
n_open = one("SELECT COUNT(*) FROM fact_request WHERE status='Open'")
med = one("SELECT quantile_cont(tat_hours,0.5) FROM fact_request")
p90 = one("SELECT quantile_cont(tat_hours,0.9) FROM fact_request")
breach = one("SELECT COUNT(*) FROM fact_request WHERE sla_breached")
esc = one("SELECT COUNT(DISTINCT request_id) FROM fact_escalation")
hits = con.sql("SELECT rule_id, COUNT(*) FROM fact_rule_hit GROUP BY 1 ORDER BY 1").fetchall()
hit_txt = ", ".join("%s %s" % (r, f"{c:,}") for r, c in hits)

out = open("scripts/readme_template.md", encoding="utf-8").read()
vals = {"HITS": hit_txt, "REQ": f"{n_req:,}", "DONE": f"{n_done:,}", "OPEN": str(n_open),
        "MED": "%.2f" % med, "P90": "%.2f" % p90, "BREACH": str(breach), "ESC": f"{esc:,}"}
for k, v in vals.items():
    out = out.replace("@@" + k + "@@", v)

old = open("README.md", encoding="utf-8").read().split("\n")
keep, skip = [], False
for line in old:
    if line.startswith("## Client Onboarding Control Platform"):
        break
    if line.startswith("> **Also in this repo"):
        skip = True
    if skip:
        if line.strip() == "":
            skip = False
        continue
    keep.append(line)
if keep and keep[0].startswith("# "):
    keep[0] = "## Project 2: " + keep[0][2:]
open("README_new.md", "w", encoding="utf-8", newline="\n").write(out + "\n".join(keep).rstrip() + "\n")
print("README_new.md written. baseline:", n_req, n_done, n_open, "breaches:", breach, "escalated:", esc)
