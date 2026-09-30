# Data Pointers

Raw data is not committed to this repository. To reproduce, download each file
into `data/raw/` with the name shown.

| Source | Where to get it | Saved as | Fetched |
|---|---|---|---|
| OFAC SDN list and aliases | https://ofac.treasury.gov/sanctions-list-service (CSV) | `sdn.csv`, `alt.csv` | 29-30 Sep 2026 |
| UN Security Council consolidated list | https://main.un.org/securitycouncil/en/content/un-sc-consolidated-list (XML) | `un_consolidated.xml` | 29-30 Sep 2026 |
| EU consolidated financial sanctions list | EU Financial Sanctions Files (fsf) XML, version 1.1 | `eu_consolidated.xml` | 29-30 Sep 2026 |
| SEC EDGAR company list | https://www.sec.gov/files/company_tickers.json | `sec_company_tickers.json` | 30 Sep 2026 |
| FATF high-risk and monitored jurisdictions | FATF public statements, 19 June 2026 | `rules/fatf_lists.json` | 30 Sep 2026 |

Check each provider's current terms of use before reuse. Lists change often,
so results will differ on a later download.

## Generated file
`test_entities.csv` is the labelled test set built by `src/build_testset.py`
(seed 42). It contains public sanctioned names, perturbed variants, and
clearly labelled synthetic names.