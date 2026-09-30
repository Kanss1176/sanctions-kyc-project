# Regulatory Basis

This maps each rule in the simulation to the standard it reflects. The FATF
Recommendations and Wolfsberg materials are cited by name; check current
wording before quoting them. This is a study project, not legal advice.

## Mapping
| Project component | Standard | What it reflects |
|---|---|---|
| Name screening against OFAC / UN / EU lists | FATF R.6 (terrorism-related targeted financial sanctions), R.7 (proliferation financing) | Institutions must not deal with designated persons and entities |
| Risk tiers and weighted rules | FATF R.1 (risk-based approach) | Measures are proportionate to the risk identified |
| CDD baseline (identity, ownership, purpose of relationship) | FATF R.10 (customer due diligence) | Identify and verify the customer and beneficial owner, understand the relationship |
| EDD escalation (source of funds and wealth, senior sign-off) | FATF R.10 (higher-risk situations), R.12 (PEPs) | More evidence where risk is higher |
| PEP flag forces EDD | FATF R.12; Wolfsberg PEP guidance | PEPs receive enhanced measures, including senior approval |
| Jurisdiction points | FATF R.19 (higher-risk countries); FATF statements of 19 June 2026 | See below |
| Ownership graph, 25% flag | FATF R.10, R.24 (legal persons), R.25 (legal arrangements) | Identify natural persons who ultimately own or control |
| Periodic review cycle | FATF R.10 (ongoing due diligence) | Keep customer information current, frequency by risk |

## Jurisdiction rules
- **Call for action** (Iran, DPRK, Myanmar): FATF calls for enhanced due
  diligence, and countermeasures for Iran and DPRK. The simulation forces High
  tier and EDD.
- **Increased monitoring** ("grey list", 22 jurisdictions): FATF states it does
  not call for EDD on these jurisdictions solely because of listing, and
  encourages a risk-based approach. The simulation gives them a moderate
  score, not an automatic escalation.

## The 25% threshold
FATF requires identifying beneficial owners but does not set a percentage;
each country chooses. 25% is a widely used benchmark (for example in the US
FinCEN customer due diligence rule and in EU anti-money-laundering rules).
The simulation uses 25% as a convention and does not claim FATF mandates it.
Real programs also identify people who control through means other than
ownership; this simulation does not.

## Review frequency
Regulators expect review frequency to follow risk but do not prescribe
12 / 24 / 36 months. Those intervals are a common industry convention used
here as an assumption.

## Wolfsberg Group
The rule catalogue follows Wolfsberg principles on a risk-based approach,
PEP treatment and ownership transparency. Point weights are this project's own
judgement and are not taken from any Wolfsberg document.