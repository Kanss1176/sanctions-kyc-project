import json
import os

AS_OF = "2026-10-04 16:00:00"
SCREEN_THRESHOLD = 80

_NAME_TO_ISO = {
    "IRAN": "IR", "NORTH KOREA": "KP", "MYANMAR": "MM",
    "ANGOLA": "AO", "BOLIVIA": "BO", "BOSNIA AND HERZEGOVINA": "BA", "BULGARIA": "BG",
    "CAMEROON": "CM", "COTE D'IVOIRE": "CI", "DEMOCRATIC REPUBLIC OF THE CONGO": "CD",
    "HAITI": "HT", "IRAQ": "IQ", "KENYA": "KE", "KUWAIT": "KW", "LAO PDR": "LA",
    "LEBANON": "LB", "MONACO": "MC", "NEPAL": "NP", "PAPUA NEW GUINEA": "PG",
    "SOUTH SUDAN": "SS", "SYRIA": "SY", "VENEZUELA": "VE", "VIETNAM": "VN",
    "VIRGIN ISLANDS (UK)": "VG", "YEMEN": "YE",
}


def _load_fatf():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    with open(os.path.join(root, "rules", "fatf_lists.json"), encoding="utf-8") as f:
        d = json.load(f)
    names = d["call_for_action"] + d["increased_monitoring"]
    return sorted({_NAME_TO_ISO[n] for n in names})


FATF_CODES = _load_fatf()
_IN = ",".join("'" + c + "'" for c in FATF_CODES)

RULES = {
    "R01": "e.registration_status NOT IN ('ISSUED','ANNULLED','DUPLICATE')",
    "R02": "e.registration_status = 'ISSUED' AND e.next_renewal_ts < TIMESTAMP '" + AS_OF + "'",
    "R03": "e.entity_status = 'INACTIVE'",
    "R04": "e.legal_country <> e.hq_country",
    "R05": "p.missing_parent_unexplained = 1",
    "R06": "s.best_score >= " + str(SCREEN_THRESHOLD),
    "R07": "(e.legal_country IN (" + _IN + ") OR e.hq_country IN (" + _IN + "))",
}

FROM_SQL = (
    "dim_entity e JOIN fact_parent p ON p.lei = e.lei "
    "LEFT JOIN fact_screen s ON s.lei = e.lei"
)


def hit_query(rule_id):
    return (
        "SELECT '" + rule_id + "' AS rule_id, e.lei, e.registration_status "
        "FROM " + FROM_SQL + " WHERE " + RULES[rule_id]
    )
