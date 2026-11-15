# Phase 2 Research Blueprint

**Course:** MIT 8212 Seminar, Miva Open University
**Student:** Abiodun Emmanuel Awoyemi
**Status:** Draft for student review, 14 November 2026. Nothing here is final until you approve it.
**Decision already taken:** merge the existing paper's framework (DR1–DR10, stages S1–S7, Tools 1–2) with the software modules in the master prompt.

Items marked **[open]** need your decision. Items marked **[unverified]** must be checked against the publisher's own text before they are cited.

---

## 1. Title options [open]

The title is not changed until you agree and the lecturer approves.

| Option | Title | Case for | Case against |
|---|---|---|---|
| A | An Operational Framework and Prototype for Cyber-Resilient IT Infrastructure Planning in Nigerian Commercial Banks: A Design Science Study | Closest to the registered topic wording; removes "Conceptual"; names the method and the artefact | Does not name the three services |
| B | Design and Prototype Demonstration of an Operational Cyber-Resilience Planning and Assessment Framework for Payment, Core Banking and ATM Services in Nigerian Commercial Banks | Precise about scope; continues the existing paper's title | Long (24 words) |
| C | An Operational Framework for Cyber-Resilient IT Infrastructure Planning in Nigerian Commercial Banks | Smallest change to the provisional title | Hides the prototype, which is the main new evidence |

**Recommendation: Option A.** "Conceptual framework" in research methods usually means a diagram of constructs, which is what the lecturer cautioned against. "A Documentary Study" in the current title would be inaccurate once a prototype is built and tested.

**Working names [open]:** framework: *Service-Centred Cyber-Resilience Planning and Assessment Framework (SC-CRPAF)*. Prototype: the prompt's acronym BCRAPS reads badly aloud; *Bank Resilience Assessment and Planning System (BRAPS)* is one alternative.

---

## 2. Aim, objectives and research questions

**Aim.** To design, implement and evaluate an operational framework, with a working software prototype, for assessing and planning the cyber-resilient recovery of payment, core banking and ATM services in Nigerian commercial banks.

| No. | Objective | Research question | DSR stage | Prototype element | Evidence produced | Chapter |
|---|---|---|---|---|---|---|
| 1 | Analyse documented risks, infrastructure dependencies and continuity requirements for the three services | RQ1. What documented risks, dependencies and continuity requirements affect the three services? | Problem identification | None | Five documentary findings (existing) | 1, 2 |
| 2 | Compare CBN (2024), NIST CSF 2.0, ISO 22301, ISO/IEC 27001:2022, COBIT 2019 and NIST SP 800-34 | RQ2. What does each contribute to service-level resilience planning, where do they overlap, and what do they leave unspecified? | Objectives of a solution | Control library references | Comparison table and crosswalk | 2 |
| 3 | Design the framework: components, decision rules, procedure and assessment method | RQ3. What components, rules, procedures and scoring method should the framework contain? | Design | Framework specification | Specification with each rule's basis labelled | 3, 4 |
| 4 | Build a prototype that implements selected components | RQ4. Can the framework be implemented so that its rules are applied consistently by software? | Development | All seven modules | Running application and source code | 4 |
| 5 | Evaluate the prototype on synthetic scenarios | RQ5. Does the prototype behave as specified, and how sensitive are its conclusions to the weighting used? | Demonstration, evaluation | Test suite, scenarios | Actual test results and sensitivity analysis | 4 |
| 6 | Identify limitations and extensions | RQ6. What does the artefact not establish, and what further work is needed? | Communication | None | Limitations and extension plan | 5 |

The existing paper's RQ4 (templates and measures) is absorbed into RQ3, and its RQ5 (hypothetical illustration) becomes one of the five scenarios under the new RQ5.

---

## 3. Methodology

**Design.** Design Science Research (DSR) following the six activities of Peffers et al. (2007), with the documentary analysis already completed serving as the problem-identification stage.

**Why DSR fits.** The study's output is an artefact (a framework and its software instantiation) built to address an identified problem. Hevner et al. (2004) treat the building and evaluation of such an artefact as the research contribution. A survey or case study would describe current practice but would not produce the demonstrable framework the lecturer asked for.

**Evaluation strategy.** Venable et al. (2016) distinguish artificial from naturalistic evaluation and formative from summative. This study uses **artificial evaluation only**: tests and synthetic scenarios, with no real users or bank setting. That choice is forced by the lack of access to a bank, and the manuscript will say so. It supports claims about correctness and consistency, not about effectiveness in practice.

**Five things kept distinct in the write-up:**

| Term | Meaning in this study | Where reported |
|---|---|---|
| Research design | DSR with documentary problem analysis | Ch. 3 |
| Framework design | Deriving components, rules and scoring from findings and source frameworks | Ch. 3 (method), Ch. 4 (result) |
| Software implementation | Coding the prototype | Ch. 4 |
| Demonstration | Running five synthetic scenarios through the prototype | Ch. 4 |
| Evaluation | Tests and checks against criteria fixed in advance (section 6) | Ch. 4 |

---

## 4. Conceptual architecture

```
Inputs                    Processing rules                     Outputs
------                    ----------------                     -------
A  Asset and service  --> DR1-DR3: criticality, owners,    --> Critical services register,
   register               RTO/RPO present, dependencies        dependency register
B  Threat scenarios   --> Likelihood x impact (1-5 scales) --> Risk register per service
C  Control library +  --> Evidence grade 0-4 per control   --> Assessment record
   assessor entries
D  Scoring and rules  --> Weighted score (compensatory)    --> Score per domain and service;
   engine                 + DR gates (non-compensatory)        status: Ready / Not demonstrated
E  Gap and remediation -> Target minus current; priority   --> Gap list, action plan,
                          rule; DR10 exception register        exception register
F  Reporting          --> Fixed template                   --> Dashboard, exported report
                                                               with limitations stated
```

Feedback: outputs of E return to A–C at the next assessment (the existing paper's stage S7).

### 4.1 What each source framework contributes

| Source | Role in the framework | Level used | Verification status |
|---|---|---|---|
| CBN Risk-Based Cybersecurity Framework (2024) | Primary anchor: the binding minimum for Nigerian banks | Section references already cited in the paper | Paper states the text was re-checked online; I will re-read it in Phase 3 |
| NIST CSF 2.0 (CSWP 29) | Common taxonomy for the control library | Category IDs (public, free to cite) | Confirmed: 6 functions, 22 categories, 106 subcategories. Subcategory wording **[unverified]** |
| ISO 22301:2019 | Business impact analysis, recovery objectives, exercising | Clause numbers and titles only | Clause 8 structure **[unverified]** |
| ISO/IEC 27001:2022 | Annex A control references | Control numbers and titles only | 5.29, 5.30, 8.13, 8.14 confirmed from third-party summaries; 8.22 and others **[unverified]** |
| COBIT 2019 | Governance and accountability references | Objective IDs and names only | Confirmed: 40 objectives in five domains. Individual objective names (e.g. DSS04, APO12) **[unverified]** |
| NIST SP 800-34 Rev. 1 | RTO, RPO and contingency planning steps | Public, free to cite | Already cited in the paper |

**Rule for avoiding duplication.** Each control appears once in the library. It carries one primary anchor (the CBN requirement where one exists, otherwise a CSF category) and any number of secondary cross-references. Scores are computed once per control, so a requirement that appears in four frameworks is not counted four times.

**Copyright.** ISO and COBIT text is not reproduced. Only identifiers and short titles are cited, with assessment questions written in the researcher's own words. The paper already admits ISO was read at scope and summary level; the same limit will be stated for COBIT unless you have licensed copies **[open]**.

### 4.2 Ten control domains (preliminary; fixed in Phase 3)

Security governance; asset visibility; access management; network segmentation; infrastructure redundancy; backup and recovery; monitoring and detection; incident response; business continuity; third-party risk. Target: 25–30 controls in total, each with a question, expected evidence, mapping rationale and basis label (Reg, Std or Des, as in the existing paper).

---

## 5. Assessment model (preliminary)

This is the researcher's own method. It is **not** a NIST CSF Tier or an official maturity score.

**Evidence grade per control, per service**

| Grade | Meaning |
|---|---|
| 0 | Not implemented, or no information |
| 1 | Planned or partly implemented |
| 2 | Implemented by statement only; no evidence referenced |
| 3 | Implemented, with an evidence artefact referenced |
| 4 | Demonstrated by a test or exercise within a validity period, with the result recorded |

This scale turns the paper's Finding Four (documented recovery is not demonstrated recovery) into a scoring rule.

**Rules**

- **Missing evidence:** a control marked implemented without an evidence reference cannot score above 2.
- **Not applicable:** excluded from the denominator; a written justification is mandatory.
- **Not assessed:** scored 0 in the headline figure, and the share of controls assessed is reported beside it.
- **Aggregation:** weighted mean of controls within a domain, of domains within a service, and of services weighted by criticality.
- **Gates:** each decision rule that can be tested from recorded data becomes a pass/fail gate. A service is "Ready" only if every gate passes; otherwise it is "Not demonstrated". A high score never overrides a failed gate.
- **Gap priority:** (target grade − current grade) × control weight × service criticality, with failed gates listed first.
- **Sensitivity analysis:** scores and gap rankings are recomputed under three weighting schemes (equal weights, criticality-weighted, recovery-emphasis). Any change in ranking is reported.

---

## 6. Evaluation plan

Criteria and expected results are written down before the tests are run. Only results from tests actually executed will be reported.

| Criterion | Method | Measure | Pass condition |
|---|---|---|---|
| Functional correctness | pytest unit and integration tests | Tests passed / total; requirements with at least one test | All pass; every documented requirement covered |
| Assessment consistency | Same inputs run repeatedly | Identical scores and identical report content hash | No variation |
| Framework coverage | Traceability matrix: rule → function → test | Rules and components implemented / specified | Every rule marked implemented has a passing test; the rest are listed as not implemented |
| Scenario behaviour | Five synthetic scenarios, expected outcome stated first | Expected against actual gate results and status | Matches, or the mismatch is explained and fixed |
| Decision support | Automated check on the report | Share of gaps and actions that cite a control, evidence grade and rule | 100% |
| Sensitivity | Three weighting schemes | Changes in ranking | Reported; no pass mark |
| Usability | **[open]** see below | | |

**Usability [open].** A claim about usability needs real users. Two honest options: (a) an author walkthrough against a task list, reported as the author's own check and nothing more; or (b) a short task-based session with three to five colleagues, which you would have to run yourself and which may need the university's ethics clearance. I will not write up any user result that did not happen.

---

## 7. Literature search strategy

The existing paper states that no search log was kept. From this point every search is logged in `docs/search-log.md` (date, database, string, hits, items kept, reason).

- **Sources:** Google Scholar, Scopus or Web of Science if you have access **[open]**, AIS eLibrary, NIST CSRC, ISACA, ISO, BIS, CBN, NDPC, NIBSS.
- **Added topics:** COBIT 2019 in banking; integration or harmonisation of security frameworks; DSR evaluation; critiques of maturity scoring; Nigerian studies of business continuity in banks.
- **Inclusion:** identifiable author or institution, full publication details, method or authority stated, relevant to banking infrastructure resilience or to the method.
- **Verification:** each of the 29 existing references and every new one is opened at its source and checked for author, year, title, DOI and the claim it supports. Any I cannot confirm will be listed for you, not silently kept.
- **Sources added so far:** Hevner et al. (2004), *MIS Quarterly, 28*(1), 75–105 (DOI 10.2307/25148625, from one aggregator, **[unverified]**); Venable et al. (2016), *European Journal of Information Systems, 25*(1), 77–89, https://doi.org/10.1057/ejis.2014.36 (confirmed).

---

## 8. Chapter outline mapped to the rubric

Word shares follow the mark weights and will be converted to counts once the limit is known **[open]**.

| Chapter | Rubric criterion (marks) | Content | Share |
|---|---|---|---|
| 1 Introduction | Introduction and problem definition (15) | Background, Nigerian context, problem, aim, objectives and RQs, scope, terms | 15% |
| 2 Literature and industry review | Literature and industry review (20) | Concepts; Nigerian evidence; the six source frameworks compared; gaps; framework requirements | 22% |
| 3 Methodology and system design | Investigative approach (15) | DSR justification; procedure; requirements; architecture; scoring method; tools; evaluation plan; ethics | 17% |
| 4 Implementation, findings and evaluation | Findings and analysis (25) | Documentary findings (condensed); framework; prototype; scenarios; actual test results; sensitivity; discussion; limitations | 30% |
| 5 Conclusions and recommendations | Conclusions and recommendations (15) | Answers to RQs; contributions; recommendations; limitations; Master's extension | 16% |
| Throughout | Academic writing and integrity (10) | APA 7; verified references; design choices labelled as the author's | |

The existing paper's five findings stay, shortened, at the start of Chapter 4, because they justify the design. Much of its Section 4.8 moves into the framework specification and appendices.

---

## 9. Technical feasibility checked today

- Python 3.14.10 and git 2.56 are installed on this machine.
- A dry-run install resolved the whole stack for Python 3.14 without installing anything: Streamlit 1.67.0, pandas 3.1.1, Plotly 7.1.0, SQLAlchemy 2.1.8, pytest 9.2.0.
- Not yet done: creating a virtual environment, installing, or running anything.

---

## 10. Scope risks

1. **Word limit unknown.** The master prompt's outline has about 45 sections plus appendices. Without the limit, the plan may be far too long.
2. **Status of the existing paper.** If it has been submitted or graded, reuse needs the lecturer's approval.
3. **Six source frameworks.** Depth will be uneven: CBN and NIST can be read in full; ISO and COBIT only at identifier level without licensed copies.
4. **Scoring validity.** Weights and grades are design assumptions. The sensitivity analysis shows how much they matter but does not validate them.
5. **No external validation.** The evaluation shows the software does what the specification says. It does not show the framework improves recovery.

---

## 11. Decisions needed at this checkpoint

1. Title option (A, B or C), and which title is currently registered with the lecturer.
2. Framework and prototype names.
3. Usability evaluation: option (a) or (b).
4. Official brief, word limit, deadline, and status of the existing paper (still outstanding from Phase 1).
5. Whether you have licensed access to ISO 22301, ISO/IEC 27001:2022 or COBIT 2019.
