# Prototype Requirements

**Prototype working name:** Banking Cyber-Resilience Assessment and Planning System (name still to be confirmed)
**Version:** 0.1 draft for student review, 14 November 2026

The prototype implements the framework in `02-framework-specification.md` using the catalogue in `03-control-catalogue.md` and the fictional data in `04-synthetic-environment-and-scenarios.md`. It is an academic proof of concept for one fictional bank and one user. Nothing has been built yet.

---

## 1. Architecture

| Layer | Responsibility | Technology |
|---|---|---|
| Interface | Pages, forms, charts. No business rules | Streamlit, Plotly |
| Logic | Effective grades, scoring, gates, gaps, priorities, Tool 2 decision, report content. Pure Python functions that take data and return data | Python, pandas where useful |
| Data access | Reading and writing records | SQLAlchemy 2 |
| Storage | One database file | SQLite |
| Reference data | Control catalogue and seed scenarios | Versioned JSON files |

The logic layer imports neither Streamlit nor SQLAlchemy, so it can be tested alone and reused later behind a different interface or database. SQLAlchemy is used so that a later move to PostgreSQL is a change of connection string, not a rewrite; no SQLite-only SQL is written.

**Checked on this machine:** Python 3.14.10; the stack resolves as Streamlit 1.67.0, pandas 3.1.1, Plotly 7.1.0, SQLAlchemy 2.1.8 and pytest 9.2.0. Versions will be pinned in `requirements.txt`.

### Proposed project structure

```
mit8212-cyber-resilience/
  app/                 Streamlit entry point and one file per page
  bcr/
    engine/            grades.py, scoring.py, gates.py, gaps.py, resumption.py, sensitivity.py
    data/              models.py, repository.py, seed.py
    reporting/         report.py (HTML and CSV)
    validation.py
  data/                control_library.json, seed/ (B0, SC1-SC5, demonstration profile)
  tests/               unit/, integration/, scenarios/
  tools/               build_catalogue.py
  docs/
  requirements.txt
  README.md
```

---

## 2. Data model

| Table | Main fields | Notes |
|---|---|---|
| organisation | name, is_fictional | One row |
| service | code, name, criticality, business_owner, technical_owner, mtd_hours, rto_hours, rpo_minutes, requirements_approved, approved_on | DR1, DR2 |
| service_dependency | service, depends_on_service | Used by G7 |
| asset | code, name, type, site, criticality, owner, is_third_party, provider | Component C1 |
| service_asset | service, asset, single_point_of_failure, tested_alternative, recovery_coordination_tested, note | DR3; used by G3 |
| threat_scenario | service, title, category, likelihood, impact, affects_recovery_environment, note | Component C2 |
| (controls) | Not a database table. Controls are read from the versioned catalogue file and are read-only in the application; each assessment stores the catalogue version it used | Component C3 |
| assessment | name, assessment_date, assessor, library_version, validity_days, status | One per assessment |
| assessment_item | assessment, service (empty for organisation-level controls), control, applicable, na_justification, grade, evidence_description, evidence_reference, evidence_date | Section 3 of the specification |
| exception | assessment, service, rule, gate, dependency or control, description, owner, treatment, compensating_control, approved_by, due_date, status, closure_evidence | DR10 |
| exercise | assessment, service, exercise_date, kind (exercise or incident), scenario | Tool 2 header |
| exercise_check | exercise, check number, result, evidence_reference | Tool 2 checks 1.1 to 6.1 |
| exercise_condition | exercise, text, owner, expiry_date | Conditions for conditional resumption |

Check 7.1 of Tool 2 ("decision recorded") is the output of the decision rule, so it is computed and not entered.

---

## 3. Functional requirements

Each requirement will have at least one test. The identifiers are used in the traceability matrix in Phase 5.

**Module 1: Asset and service register**

| ID | Requirement |
|---|---|
| FR-01 | Create, view and edit services with owners, criticality and recovery requirements |
| FR-02 | Create, view, edit and classify assets by type, site and criticality |
| FR-03 | Link services to assets and record the dependency attributes used by DR3 |
| FR-04 | Record which services depend on which other services, rejecting a service that depends on itself |
| FR-05 | Reject invalid input: empty names, criticality outside 1–5, negative times, RTO greater than the maximum tolerable downtime |

**Module 2: Control library**

| ID | Requirement |
|---|---|
| FR-06 | Load the catalogue file and refuse to start an assessment if it fails validation |
| FR-07 | Show each control with its question, expected evidence, basis, references and verification status, filterable by domain and basis |

**Module 3: Assessment**

| ID | Requirement |
|---|---|
| FR-08 | Create an assessment that records the catalogue version and the validity period |
| FR-09 | Record a grade, evidence description, evidence reference and evidence date for each control and service |
| FR-10 | Mark a control not applicable only with a written justification |
| FR-11 | Warn when a grade of 3 or 4 has no evidence reference or a grade of 4 has no test date |
| FR-12 | Record threat scenarios with likelihood, impact and the recovery-environment flag |

**Module 4: Scoring and rules engine**

| ID | Requirement |
|---|---|
| FR-13 | Compute effective grades by the rules in Section 3 of the specification |
| FR-14 | Compute domain, service and overall scores, coverage, demonstrated share and grade distribution |
| FR-15 | Evaluate gates G1–G7 and the readiness status of each service, including waivers |
| FR-16 | Recompute scores under weighting schemes A, B and C and show that readiness status does not change |
| FR-17 | Produce identical output for identical input |

**Module 5: Gap analysis**

| ID | Requirement |
|---|---|
| FR-18 | List every gap between effective and target grade, and every failed gate condition |

**Module 6: Remediation planning**

| ID | Requirement |
|---|---|
| FR-19 | Generate actions with type, tier and order by the rules in Section 7 of the specification |
| FR-20 | Maintain the exception register; refuse to close an exception without closure evidence; flag overdue exceptions |

**Module 7: Dashboard and reporting**

| ID | Requirement |
|---|---|
| FR-21 | Show overall and per-service scores, coverage, demonstrated share, readiness status and gate results |
| FR-22 | Show domain scores, grade distribution, risk distribution and the top remediation priorities |
| FR-23 | Show a Tool 1 view for each service: owners, dependencies, recovery requirements, controls and acceptance evidence |
| FR-24 | Record a Tool 2 checklist and compute the resumption decision |
| FR-25 | Export a self-contained HTML report and CSV files of gaps and actions |
| FR-26 | Print the assessment limitations and the "fictional data" notice on the dashboard and in every report |

**Seed data**

| ID | Requirement |
|---|---|
| FR-27 | Load the reference state B0, scenarios SC1–SC5 and the demonstration profile from files, and reset the database to any of them |

---

## 4. Non-functional requirements

| ID | Requirement |
|---|---|
| NFR-01 | Runs offline on one machine after installation; no external service is called |
| NFR-02 | Contains no real bank data, credentials, customer records or network addresses |
| NFR-03 | Business rules live only in the logic layer |
| NFR-04 | Setup and run steps are reproducible from the README on a clean machine |
| NFR-05 | Errors are shown to the user as plain messages; invalid input never reaches the database |
| NFR-06 | The report states the catalogue version, assessment date, validity period and weighting scheme used |

---

## 5. Out of scope for the seminar prototype

Login and user roles; more than one organisation; editing the catalogue inside the application; automated evidence collection; integration with Intune, Entra ID or any monitoring tool; historical trends; PostgreSQL deployment; PDF export; any use with real bank data.

---

## 6. Planned tests

| Level | What is tested |
|---|---|
| Unit | Effective-grade rules; each scoring formula against hand-calculated values on a small fixture; each gate; waiver and overdue logic; priority tiers and ordering; Tool 2 decision table; input validation |
| Integration | Database round trip; seed loading; report generation from a stored assessment |
| Scenario | B0 and SC1–SC5 against the expected results written in `04-synthetic-environment-and-scenarios.md` |
| Property | Same input gives same output; readiness status is unchanged across weighting schemes |

Results will be reported exactly as the test runner prints them, including any failures.
