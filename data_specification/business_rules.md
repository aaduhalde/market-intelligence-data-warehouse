# Business Rules

## BR-001 — Fact Table Grain

Each row in `fact_ofertas` represents one unique job posting detected by the ingestion pipeline.

The fact table must not contain multiple rows for the same logical job posting solely because the posting was discovered through different search queries or extraction runs.

Repeated observations of the same posting must be handled through deduplication and snapshot logic.

---

## BR-002 — Source Job Identifier

The source-provided job identifier is the preferred identifier for a posting when available.

The pipeline must preserve the original source identifier.

If the source does not provide a stable identifier, a deterministic fallback identifier may be generated from normalized attributes such as:

* Company
* Job title
* Location
* Source
* Publication information

The generated identifier must be reproducible.

---

## BR-003 — Job Title Preservation

The original job title received from the source must be preserved.

Normalization into the project role taxonomy must not overwrite the original title.

Example:

```text
Original title:
Financial Planning & Analysis Data Analyst - Remote Work

Normalized role:
Data Analyst
```

The original value remains auditable while the normalized role is used for analytical aggregation.

---

## BR-004 — Role Classification

Each valid posting should be assigned a normalized role according to `data_specification/taxonomy.md`.

Classification must use the configured role taxonomy:

* Primary
* Secondary
* Legacy Leverage

If no reliable role classification can be established, the posting must be classified as `Unclassified` rather than being assigned arbitrarily.

---

## BR-005 — Company Normalization

The original company name must be preserved during ingestion.

A normalized company representation may be generated for analytical purposes.

Minor textual differences such as:

* capitalization
* surrounding whitespace
* punctuation

must not create unnecessary duplicate company entities.

The normalization process must remain deterministic and auditable.

---

## BR-006 — Location Preservation and Normalization

The original location received from the source must be preserved in `ubicacion_raw`.

Normalized geographic attributes may include:

* City
* Country
* Geographic market tier

The normalized location must not overwrite the raw source value.

Examples:

```text
Raw:
Perú

Normalized:
Country = Peru
Market Tier = Priority 1
```

```text
Raw:
Huánuco

Normalized:
City = Huánuco
Country = Peru
Market Tier = Priority 1
```

---

## BR-007 — Geographic Market Classification

Each posting should be assigned to one of the geographic tiers defined in `data_specification/taxonomy.md`.

### Priority 1

* Lima / Peru
* Peru
* Argentina

### Priority 2

* Chile
* Colombia
* Mexico
* Uruguay
* Ecuador
* Costa Rica
* Panama

### Priority 3

* United States
* Canada
* United Kingdom
* Ireland
* Europe
* Global Remote

A posting may remain `Unclassified` if the available source information is insufficient.

---

## BR-008 — Remote Classification

Remote classification must be derived from available source evidence.

Signals may include:

* `Remote`
* `Fully Remote`
* `100% Remote`
* `Work from home`
* `Remote from LATAM`
* `Global Remote`

The pipeline should classify the posting into:

* Remote
* Hybrid
* Onsite
* Unspecified

The original source text must be retained to support auditability.

---

## BR-009 — Employment Type

Employment type should be extracted from the source when available.

Supported normalized values may include:

* Full Time
* Part Time
* Contract
* Internship
* Temporary
* Unspecified

The source value must be preserved whenever available.

---

## BR-010 — Publication Date

The source may provide relative publication information such as:

* Today
* Yesterday
* 3 days ago
* 1 week ago
* 1 month ago

Relative publication information must be converted into an estimated publication date only when the transformation is deterministic.

The original publication-age text must be preserved.

If the publication date cannot be reliably determined, `fecha_publicacion` must remain NULL.

The pipeline must not fabricate an exact publication date.

---

## BR-011 — Capture Date

`fecha_captura` represents the date on which the posting was ingested by the pipeline.

Capture date is determined from the pipeline ingestion timestamp and is independent from publication date.

Example:

```text
publication_date = 2026-09-25
capture_date     = 2026-09-29
```

A posting may therefore appear in multiple extraction snapshots.

---

## BR-012 — Duplicate Detection

A posting should be considered a duplicate when the same logical job can be identified through a stable source identifier.

When a stable source identifier is unavailable, the pipeline may use a deterministic composite key based on normalized:

* Company
* Job title
* Location
* Source
* Publication information

Duplicate detection must occur before loading the canonical fact table.

---

## BR-013 — Search-Result Deduplication & Primary Query Attribution

When the same logical posting (source_job_id) is discovered by multiple search queries during the same extraction snapshot, only one observation record is stored in fact_observacion_oferta.

The search_query field retains the primary search query according to the configured query-priority rules (e.g., specific role queries take priority over broader location-only queries). Complete query-to-observation mapping is outside the scope of the canonical fact table and may be implemented through a secondary bridge table (rel_observacion_busqueda) if required in future releases.

---

## BR-014 — Multi-Source Job Listings

The same job may appear through multiple job boards or aggregators.

A source-specific record may be retained during raw ingestion.

The canonical analytical layer should attempt to identify the underlying logical posting and avoid counting obvious duplicates as separate job opportunities.

When deduplication confidence is insufficient, the records should remain separate and be flagged accordingly rather than being incorrectly merged.

---

## BR-015 — Skill Extraction

Skills must be extracted primarily from the job description and normalized against `data_specification/taxonomy.md`.

The original job description must remain available for traceability.

Examples:

```text
SQL
Microsoft SQL Server
T-SQL
Power BI
Power Query
DAX
Python
Pandas
Oracle
PL/SQL
ETL
```

Equivalent terms may map to a canonical skill where explicitly defined by the taxonomy.

---

## BR-016 — Skill Relationship

A posting may contain zero, one, or many skills.

The many-to-many relationship between postings and skills must be represented through:

`rel_oferta_skill`

A posting must not contain duplicate relationships to the same normalized skill.

The composite key is:

```text
(oferta_id, skill_id)
```

---

## BR-017 — Skill Category

Each normalized skill must belong to a taxonomy category where classification is available.

Current categories include:

* Data Core
* BI
* Engineering
* Databases
* Automation

Unknown or newly detected skills must not be assigned to an arbitrary category.

They should be flagged for taxonomy review.

---

## BR-018 — Experience Requirement

Experience requirements should be extracted only when explicit evidence exists in the posting.

Examples:

```text
3+ years
5 years of experience
Senior-level experience
```

If no explicit experience requirement is available, the field must remain NULL.

The pipeline must distinguish between:

* Explicit requirement
* Inferred seniority
* Missing information

These concepts must not be conflated.

---

## BR-019 — Language Requirement

Language requirements must be detected from the job description.

Examples:

```text
English required
Advanced English
Fluent English
Spanish required
Bilingual
```

The absence of an explicit language requirement must not be interpreted as "no language requirement".

The normalized representation should therefore support:

* Spanish
* English
* Multiple Languages
* Not Specified

---

## BR-020 — Candidate Matching

Candidate matching compares normalized job requirements with the configured candidate profile.

The calculation should consider:

* Target role alignment
* Skill coverage
* Required skills
* Candidate skill profile

A match score must be reproducible from the configured rules and input data.

The original job data must remain independent from the candidate-specific score.

---

## BR-021 — Candidate Skill Gap

A skill is considered a candidate gap when:

1. The skill is required or frequently requested by relevant target jobs.
2. The skill is absent or below the configured candidate proficiency threshold.

Gap priority is determined using observed market demand according to `config/metrics.yaml`.

---

## BR-022 — Candidate Geographic Priority

Candidate matching must respect the geographic priorities defined in `data_specification/taxonomy.md`.

Priority order:

1. Local / Argentina
2. Spanish-speaking LATAM
3. International Remote

International opportunities remain eligible for analysis even when English accessibility is lower.

Geographic priority must influence candidate-fit analysis, not erase international market data.

---

## BR-023 — Language Accessibility

Spanish is treated as the primary language context.

English is treated as a secondary language with developing accessibility.

International postings requiring English must remain in the analytical dataset.

Language requirements may influence candidate-fit analysis but must not cause the underlying posting to be excluded.

---

## BR-024 — Raw Data Preservation

Raw API responses must be preserved before transformation.

The normalized warehouse must be reproducible from the available raw data and transformation rules.

Raw values must not be modified to make them conform to the analytical model.

---

## BR-025 — Data Quality

At minimum, the following validations must be applied before loading the analytical layer:

* Required identifier is not NULL
* Job title is not NULL or empty
* Source is identified
* Duplicate detection is executed
* Foreign-key relationships are valid
* Normalized role values belong to the defined taxonomy
* Normalized skills belong to the defined taxonomy
* Date values are valid when present

Records failing mandatory validation should be rejected or quarantined according to the data-quality rules.

---

## BR-026 — Salary

Salary analysis is outside the scope of the current project version.

The analytical model and KPIs must not depend on:

* Salary
* Salary range
* Currency
* Salary period
* Salary distribution
* Salary benchmarking

Salary-related information appearing in source descriptions may remain in raw data for traceability, but it is not part of the current analytical model.

---

## BR-027 — Industry

Industry is not a mandatory analytical dimension in the current version.

Because the current source does not consistently provide a structured industry field, the project must not present industry-level conclusions as if they were directly observed source attributes.

Future enrichment may introduce an industry taxonomy.

---

## BR-028 — Historical Trend Analysis

Trend analysis requires multiple extraction snapshots.

A single extraction represents a market snapshot and must not be interpreted as a historical trend.

Metrics such as:

* Skill growth
* Role growth
* Posting growth
* Emerging skills

require observations across multiple capture dates.

---

## BR-029 — Market Demand Metric

Skill or role demand is calculated as the proportion of relevant job postings containing the normalized role or skill.

Example:

```text
skill_demand_pct =
jobs_requiring_skill / total_relevant_jobs * 100
```

The denominator must be clearly defined for every analytical view.

---

## BR-030 — Analytical Traceability

Every normalized analytical record should remain traceable to:

* Source provider
* Source job identifier
* Raw record
* Extraction timestamp
* Search context when available
* Transformation / classification logic

The objective is to make every analytical result explainable from its originating data.
