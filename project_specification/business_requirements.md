# Business Requirements (BRD)

- **BRD-01 (Data Collection & Cross-Market Ingestion):** Automated ingestion crossing Roles × Markets × Remote × Languages.
- **BRD-02 (Data Quality & Integrity):** Strict validation of raw records (schema, deduplication, null checks, quarantine logic).
- **BRD-03 (Taxonomy Alignment):** Normalization of job titles and skills into a standardized taxonomy framework.
- **BRD-04 (Market Intelligence):** Tracking metrics for skill frequency, geographic demand, salary ranges, and tech stacks.
- **BRD-05 (Candidate Skill Matcher):** Algorithmic scoring of candidate coverage against required job skills.
- **BRD-06 (Geographic & Language Prioritization):** The platform MUST prioritize remote opportunities according to geographic context and language accessibility (Tier 1: Lima/Argentina, Tier 2: Spanish LATAM, Tier 3: International Remote). International markets remain in scope but are modeled separately under a candidate accessibility framework.
- **BRD-07 (Decoupled BI Layer):** Storage of curated dimensional datasets ready for downstream consumption (`business-intelligence-ops`).