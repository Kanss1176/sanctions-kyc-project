AS_OF = "2026-10-04 16:00:00"

RULES = {
    "R01": "e.registration_status NOT IN ('ISSUED','ANNULLED','DUPLICATE')",
    "R02": "e.registration_status = 'ISSUED' AND e.next_renewal_ts < TIMESTAMP '" + AS_OF + "'",
    "R03": "e.entity_status = 'INACTIVE'",
    "R04": "e.legal_country <> e.hq_country",
    "R05": "p.missing_parent_unexplained = 1",
}


def hit_query(rule_id):
    return (
        "SELECT '" + rule_id + "' AS rule_id, e.lei, e.registration_status "
        "FROM dim_entity e JOIN fact_parent p ON p.lei = e.lei WHERE " + RULES[rule_id]
    )
