import xml.etree.ElementTree as ET
from openpyxl import load_workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.formatting.rule import CellIsRule
from openpyxl.worksheet.datavalidation import DataValidation

OUT = "excel/Citi_Onboarding_Ops_Pack.xlsx"
FOOTER = "Simulated workflow on real GLEIF entity data. Not Citi data."

root = ET.parse("docs/pytest_results.xml").getroot()
suite = next(root.iter("testsuite"))
run_date = suite.attrib.get("timestamp", "")[:10]
res = {}
for tc in root.iter("testcase"):
    f = tc.attrib["classname"].split(".")[-1]
    bad = any(c.tag in ("failure", "error", "skipped") for c in tc)
    res[(f, tc.attrib["name"])] = "Fail" if bad else "Pass"

P = [
 ("test_metrics", "test_turnaround_matches_python", "Turnaround KPI", "fact_request, SQL metric vs Python recomputation", "Median and P90 turnaround agree"),
 ("test_metrics", "test_sla_breach_matches_python", "SLA breach KPI", "Same data, SQL vs Python", "Breach count agrees"),
 ("test_metrics", "test_first_time_right_matches_python", "First-time-right KPI", "Same data, SQL vs Python", "First-time-right count agrees"),
 ("test_metrics", "test_errors_found_equals_exception_table", "Errors found", "Metric vs fact_exception", "Counts equal"),
 ("test_metrics", "test_escalation_matches_python", "Escalation KPI", "Metric vs fact_escalation", "Escalated count agrees"),
 ("test_metrics", "test_ageing_covers_every_open_request", "Ageing buckets", "20 open requests", "Every open request sits in one bucket"),
 ("test_metrics", "test_queue_is_complete_unique_and_ordered", "Daily queue", "Open requests", "Queue is complete, no duplicates, correctly ordered"),
 ("test_metrics", "test_queue_bands_follow_the_rule", "Priority bands", "Hours left per request", "Band follows the P0 to P3 rule"),
 ("test_rules", "test_r01", "R01 registration not ISSUED", "LAPSED fires; ISSUED and ANNULLED do not", "Fires only when expected"),
 ("test_rules", "test_r02", "R02 renewal overdue", "ISSUED with renewal date passed", "Fires only for ISSUED and overdue"),
 ("test_rules", "test_r03", "R03 entity INACTIVE", "INACTIVE vs ACTIVE", "Fires only for INACTIVE"),
 ("test_rules", "test_r04", "R04 country mismatch", "Legal GB vs HQ US", "Fires only when countries differ"),
 ("test_rules", "test_r05", "R05 parent unexplained", "Flag 1 vs 0", "Fires only when flag is 1"),
 ("test_rules", "test_dim_rule_matches_shared_rules", "Rule catalogue", "dim_rule vs rule definitions in code", "Catalogue matches code"),
 ("test_rules_screen", "test_r06", "R06 name score 80 or above", "Score above and below threshold", "Fires only at or above 80"),
 ("test_rules_screen", "test_r07", "R07 FATF country", "IR, KP, VG fire; a non-listed country does not", "Fires only for listed countries"),
 ("test_workflow", "test_maker_is_never_the_checker", "Maker-checker separation", "All simulated requests", "No request has maker equal to checker"),
 ("test_workflow", "test_completed_plus_open_equals_received", "Reconciliation", "2,000 requests", "Completed + open = received"),
 ("test_workflow", "test_completion_is_not_before_receipt", "Timestamps", "All completed requests", "No completion before receipt"),
 ("test_scenarios", "test_stored_scenarios_reconcile", "Scenario totals", "scenario_results", "Every scenario: completed + open = received"),
 ("test_scenarios", "test_baseline_scenario_reproduces_the_workflow_tables", "Baseline scenario", "fifo_6_3 vs workflow tables", "Same numbers as the workflow tables"),
]
M = [
 ("Maker-checker: checker equals maker", "Checker_Log row 2 (maker M3): type M3 in checker_id", "Excel rejects with the Maker-checker rule message"),
 ("Maker-checker: valid checker", "Same row: type C1", "Accepted"),
 ("Maker-checker: checker ID must start with C", "Same row: type M2", "Rejected"),
 ("Daily_Queue size", "Open Daily_Queue", "20 open requests listed"),
 ("Daily_Queue bands", "Count the priority_band column", "8 rows P2 and 12 rows P3 at the simulation clock"),
 ("Daily_Queue overdue format", "Look for red cells in hours_left", "None red, because no request is overdue"),
 ("Daily_Queue action_status drop-down", "Click a cell in action_status", "Drop-down with Not started, In progress, Waiting on client, Done"),
 ("KPI_Summary overall check", "Open KPI_Summary cell B2", "Shows ALL OK"),
 ("KPI_Summary band total", "Find Total in bands row", "Shows 20 and OK"),
 ("Lodgment_Log red flag", "Find the row lodged without a complete check", "Row is flagged red"),
 ("Archive_Manifest red flag", "Find the row archived while incomplete", "Row is flagged red"),
 ("Lodgment_Log test rows", "Check rows 12 to 17 are labelled deliberate test cases", "Label present"),
 ("Reg_Watch change record", "Open Reg_Watch, find CR-001", "R02 SLA changed from 48 h to 24 h, labelled simulated"),
]
D = [
 ("Follow SOP-R02-01 v1.1", "An ISSUED entity with a passed renewal date (R02)", "Reader reaches: escalate, 24 h SLA"),
 ("Follow SOP-ESC-01 v1.1", "R03 entity INACTIVE", "Reader reaches: fix, 72 h SLA"),
 ("Follow SOP-ESC-01 v1.1", "R06 name score 80 or above", "Escalate, 24 h; described as potential match for review only; never mentioned to client"),
 ("Follow SOP-ESC-01 v1.1", "R07 FATF-listed country", "Escalate, 48 h"),
]

wb = load_workbook(OUT)
if "UAT_Results" in wb.sheetnames:
    del wb["UAT_Results"]
u = wb.create_sheet("UAT_Results")
heads = ["ID", "scenario", "input", "expected", "actual", "pass_fail", "tester", "date", "type"]
u.append(heads)
for c in u[1]:
    c.font = Font(bold=True)
n = 0
for f, name, sc, inp, exp in P:
    r = res[(f, name)]
    n += 1
    u.append(["UAT%02d" % n, sc, inp, exp, "%s: %s" % (f, name), r, "pytest (automated)", run_date, "Automated"])
for sc, inp, exp in M:
    n += 1
    u.append(["UAT%02d" % n, sc, inp, exp, None, None, None, None, "Manual Excel"])
for sc, inp, exp in D:
    n += 1
    u.append(["UAT%02d" % n, sc, inp, exp, None, None, None, None, "Document"])
last = u.max_row
dv = DataValidation(type="list", formula1='"Pass,Fail"', allow_blank=True)
u.add_data_validation(dv)
dv.add("F2:F%d" % last)
for rg_val, color in (("Pass", "C6EFCE"), ("Fail", "FF9999")):
    u.conditional_formatting.add("F2:F%d" % last, CellIsRule(operator="equal", formula=['"%s"' % rg_val], fill=PatternFill("solid", bgColor=color)))
for c, w in zip("ABCDEFGHI", (9, 36, 46, 48, 46, 11, 20, 12, 14)):
    u.column_dimensions[c].width = w
for row in u.iter_rows(min_row=2, max_row=last):
    for cell in row:
        cell.alignment = Alignment(wrap_text=True, vertical="top")
u["K1"], u["L1"] = "Total cases", "=COUNTA(A2:A%d)" % last
u["K2"], u["L2"] = "Pass", '=COUNTIF(F2:F%d,"Pass")' % last
u["K3"], u["L3"] = "Fail", '=COUNTIF(F2:F%d,"Fail")' % last
u["K4"], u["L4"] = "Not yet run", "=L1-L2-L3"
u["K6"] = "pytest results from docs/pytest_results.xml, run date " + run_date
u["K7"] = "Manual and document cases: fill actual, pass_fail, tester and date when you run them."
u.column_dimensions["K"].width = 16
u.freeze_panes = "A2"
u.oddFooter.center.text = FOOTER
wb.save(OUT)
print("UAT_Results built:", last - 1, "cases;", len(P), "automated,", len(M), "manual,", len(D), "document")
