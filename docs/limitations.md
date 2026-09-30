# Limitations

This is a simulation built on public sanctions lists and synthetic data. It is
not a compliance system, has no legal authority, and must not be used to make
real onboarding decisions.

## Data
- **Synthetic customers.** Country, PEP flag and last-review dates are randomly
  assigned (seeded). Tier and review-status distributions describe the test
  set, not a real customer base.
- **Synthetic ownership structures.** No public source has multi-layer ownership
  at this granularity. The 51 structures are generated (one hand-built example
  plus 50 random ones).
- **No real PEP list.** PEP status is a synthetic flag. A production system
  would use a licensed PEP data provider.
- **OFAC country is empty.** Country sits in a separate OFAC address file that
  was not ingested, so OFAC rows have no country.
- **Point-in-time lists.** All lists were fetched on 29-30 Sep 2026 and FATF
  lists are as of 19 June 2026. They change often.
- **UN format.** The UN list was read from its legacy XML layout.

## Test set
- **Rule-generated variants.** True matches are perturbed by fixed rules
  (reorder, dropped or swapped character, phonetic substitution, suffix
  abbreviation, case/punctuation). Real-world name variation is messier.
- **Near-misses are a stress test.** They change one distinctive word of a
  sanctioned name, so the false-positive rate is deliberately worse than a
  real customer base would give. Do not read the 27% false-positive share as a
  production figure.
- **Sample sizes.** 120 true-match rows per source, and only 16 abbreviated-suffix
  and 5 case/punctuation variants. Per-variant recall is indicative only.
- **No hold-out set.** Thresholds and the suffix-normalisation step were chosen
  by looking at the same test set they are evaluated on, so the results are
  optimistic. A proper evaluation would tune on one set and report on another.
- **Latin-script names only.** The test set keeps names that are more than 90%
  Latin characters, so transliteration and non-Latin scripts are not tested.

## Matching
- **Name-only matching.** No date of birth, nationality, address or identifier
  corroboration, which real analysts use to clear false alarms.
- **Generic words dominate.** Words such as LTD, GROUP, CORP and FINANCIAL, and
  common surnames, inflate scores. Rare-token weighting is not implemented.
- **No transliteration handling** (for example Arabic or Cyrillic romanisation
  variants) beyond what the fuzzy score absorbs.
- **Fixed score weights** (0.5 / 0.3 / 0.2) were chosen by judgement, not fitted.

## Risk scoring and escalation
- **Point weights are illustrative.** They are a documented rule catalogue, not
  a validated risk model.
- **FATF grey-list countries are not automatic EDD.** FATF states that
  increased-monitoring status does not by itself call for EDD, so they carry a
  moderate weight. Call-for-action countries force High.
- **Review scheduling** uses synthetic last-review dates. All synthetic customers
  share a single last-review date (2023-05-30), so the overdue counts and the
  overdue-review query (sql/05) demonstrate the logic only. Ranking within a tier
  is effectively a tie and is not a finding.

## Beneficial ownership
- **Ownership percentage only.** Control through voting rights, nominees, trusts
  or family relationships is not modelled.
- **No circular ownership.** Structures are acyclic by construction.
- **No senior-manager fallback** when nobody reaches 25%.
