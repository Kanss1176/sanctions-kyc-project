# GLEIF data dictionary (LEI-CDF v3.1)

Source: GLEIF Golden Copy, published 2026-10-04 16:00, downloaded 2026-10-05.
Fill rates are measured on the full Level 1 file (3,451,551 records).
Meanings are to be confirmed against GLEIF's LEI-CDF v3.1 documentation.

| Column | Meaning | Example | Fill | Onboarding use |
|---|---|---|---|---|
| LEI | 20-character entity identifier | 54930087XQTOUUCJYG17 | 100% | Key for the entity; length and uniqueness checks |
| Entity.LegalName | Registered legal name | Charlotte Bailey LLC | 100% | Name match against sanctions lists; form vs registry name check |
| Entity.LegalAddress.Country | Country of the legal address | US | 100% | Jurisdiction risk; country rules |
| Entity.HeadquartersAddress.Country | Country of the headquarters address | US | 100% | Legal vs headquarters country mismatch (R04) |
| Entity.EntityCategory | Type of entity (GENERAL, FUND, SOLE_PROPRIETOR, and others) | GENERAL | 100% | Different onboarding paths for funds and individuals |
| Entity.LegalForm.EntityLegalFormCode | Legal-form code | SDX0 | 100% | Check the legal form is consistent with the entity type |
| Entity.EntityStatus | ACTIVE or INACTIVE (null for some annulled and duplicate records) | ACTIVE | 100% | Entity-status check (R03) |
| Entity.SuccessorEntity.1.SuccessorLEI | LEI of the successor entity | 2549003SXAKXEC04PX64 | 1.01% | Entity replaced by another; follow the successor |
| Registration.InitialRegistrationDate | First registration date | 2016-01-28T02:27:00.000Z | 100% | Date-order checks |
| Registration.LastUpdateDate | Last update of the record | 2023-08-04T15:58:25.254Z | 100% | Staleness of the data |
| Registration.RegistrationStatus | ISSUED, LAPSED, RETIRED, and others | LAPSED | 100% | Registration check (R01) |
| Registration.NextRenewalDate | Date the registration is due for renewal | 2017-01-24T20:28:00.000Z | 100% | Overdue renewal check (R02) |
| Registration.ManagingLOU | LEI issuer managing the record | 5493001KJTIIGC8Y1R12 | 100% | Which issuer to contact about a lapsed record |

## Notes

- Dates are ISO 8601 timestamps in UTC with a Z suffix. Use the first 19 characters when casting.
- `Entity.AssociatedEntity.AssociatedLEI` is empty (0 rows) in this release and is not used.
- `Entity.EntitySubCategory` is filled in only 0.18% of rows and is not used.
- `Entity.LegalAddress.Region` is 70.5% filled and `RegistrationAuthorityEntityID` is 91.5% filled, so do not build mandatory rules on them.
- Example rows are taken from the 5,000-entity sample, not from a client.