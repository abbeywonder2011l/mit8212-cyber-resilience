# Control Catalogue

> Generated from `data/control_library.json` by `tools/build_catalogue.py`. Edit the JSON file, not this file.

**Library version:** 0.1-draft (2026-11-14)

Researcher-developed assessment catalogue for an academic prototype. It is not an official control set of the CBN, NIST, ISO or ISACA. Questions, evidence lists, weights and targets are the researcher's own wording and design choices.

## Summary

- Controls: **30** in 10 domains (3 assessed once for the organisation, 27 assessed for each service).
- Gate conditions: **10** controls. Weight 2: **12** controls. Target grade 4 (demonstrated by test): **6** controls.
- Basis: Des = 4, Reg = 15, Reg+Des = 5, Reg+Std+Des = 1, Std = 2, Std+Des = 3.
- Controls with no CBN requirement identified in the text read: ACC-03, RED-03, BCP-01, BCP-04.

| Domain | Controls |
|---|---:|
| GOV Security governance | 3 |
| AST Asset visibility | 3 |
| ACC Access management | 4 |
| NET Network segmentation | 2 |
| RED Infrastructure redundancy | 3 |
| BKP Backup and recovery | 3 |
| MON Monitoring and detection | 2 |
| INC Incident response | 3 |
| BCP Business continuity | 4 |
| TPR Third-party risk management | 3 |

**Basis codes:** Reg = Applies an identified CBN (2024) requirement; Std = Applies published standards or guidance; Des = Proposed by this study; no reviewed source specifies it.

**Reference status:** unmarked = read in the primary text on 2026-11-14; [S] = confirmed from secondary sources only; check against the publisher's text before citing; [U] = from the researcher's knowledge; not yet verified.

## Mapping overview

| ID | Control | Basis | Wt | Target | Gate | CBN (2024) | CSF 2.0 | ISO 27001 | ISO 22301 | COBIT 2019 |
|---|---|---|---:|---:|---|---|---|---|---|---|
| GOV-01 | Board and CISO accountability for cyber resilience | Reg | 1 | 3 |  | 1.1; 1.3; 1.4 | GV.RR-01; GV.RR-02 | A.5.2 [S] | 5 [S] | EDM03 [U]; APO13 [S] |
| GOV-02 | Board-approved risk appetite and acceptance criteria | Reg | 1 | 3 |  | 2.1.4; 1.1(xii); 1.5.1(v) | GV.RM-02; ID.RA-06 |  |  | APO12 [S] |
| GOV-03 | Reporting of recovery exercise results and open exceptions | Reg+Des | 1 | 3 |  | 1.1(viii); 5.0(i)-(ii); App III 3(b)-(c) | GV.OV-03; ID.IM-02 |  | 9 [S] | MEA01 [U] |
| AST-01 | Inventory of assets supporting the service | Reg | 1 | 3 |  | App II 1.1(a)-(b) | ID.AM-01; ID.AM-02 | A.5.9 [S] |  | BAI09 [S] |
| AST-02 | Criticality classification of the service and its assets | Reg | 1 | 3 |  | App I; App II 1.1(c) | ID.AM-05; GV.OC-04 |  | 8.2 [S] | BAI09 [S] |
| AST-03 | Dependency map for the service | Reg+Des | 1 | 3 |  | App II 1.1(i)-(k); App II 1.4(a)-(c) | ID.AM-03; ID.AM-04; GV.OC-05 |  | 8.2 [S] | BAI09 [S] |
| ACC-01 | Multi-factor authentication on critical systems | Reg | 1 | 3 |  | App III 1.1(d)-(e) | PR.AA-03 | A.8.5 [S] |  | DSS05 [S] |
| ACC-02 | Privileged and service accounts recorded and reviewed | Reg | 2 | 3 | G4 | App II 1.5; App III 1.1(b); App III 1.2 | PR.AA-05 | A.8.2 [S]; A.5.18 [S] |  | DSS05 [S] |
| ACC-03 | Recovery administration separated from production | Des | 2 | 3 | G4 | none identified | PR.AA-05; PR.IR-01 | A.8.2 [S] |  | DSS05 [S] |
| ACC-04 | Vendor access approved, limited, time-bound and monitored | Reg | 2 | 3 | G4 | App III 1.3(a)-(b) | PR.AA-05; DE.CM-06 | A.5.19 [S]; A.8.2 [S] |  | DSS05 [S]; APO10 [S] |
| NET-01 | Network segmentation around the service | Std | 1 | 3 |  | App II 1.1(i)-(k) | PR.IR-01 | A.8.22 [S]; A.8.20 [S] |  | DSS05 [S] |
| NET-02 | Segmentation tested in both directions | Des | 1 | 4 |  | 2.2(iii) | PR.IR-01; ID.IM-02 | A.8.22 [S] |  | DSS05 [S] |
| RED-01 | Alternative capacity for critical components | Std+Des | 1 | 3 |  | 3.7 | PR.IR-03; PR.IR-04 | A.8.14 [S] | 8.3 [U] | BAI04 [U]; DSS04 [S] |
| RED-02 | Fail-over demonstrated by test | Std | 1 | 4 |  | 2.3(vii) | PR.IR-03; ID.IM-02 | A.5.30 [S] | 8.5 [S] | DSS04 [S] |
| RED-03 | Alternative is independent of the compromise | Des | 1 | 3 |  | none identified | PR.IR-03 | A.8.14 [S] |  | DSS04 [S] |
| BKP-01 | Protected backup copy | Reg+Std+Des | 2 | 3 | G5 | App III 1.6(g) | PR.DS-11 | A.8.13 [S] |  | DSS04 [S] |
| BKP-02 | Restoration tested within the validity period | Reg | 2 | 4 | G5 | App III 1.6(g); App III 3(i) | PR.DS-11 | A.8.13 [S] | 8.5 [S] | DSS04 [S] |
| BKP-03 | Clean recovery point identified | Std+Des | 2 | 3 | G5 | App III 4(b) | RC.RP-03 | A.8.13 [S] |  | DSS04 [S] |
| MON-01 | Logging on systems supporting the service | Reg | 1 | 3 |  | App III 2.1(g); App III 1.2 | PR.PS-04 | A.8.15 [S] |  | DSS05 [S] |
| MON-02 | Continuous monitoring covers production and recovery | Reg+Des | 1 | 3 |  | 3.3; App III 2.1(a); App III 2.1(d); App III 2.1(e) | DE.CM-01; DE.CM-09 | A.8.16 [S] |  | DSS05 [S] |
| INC-01 | Incident response plan with criteria for moving to recovery | Reg | 2 | 3 |  | App III 3(a); App III 4(b) | ID.IM-04; RS.MA-01; RS.MA-05 | A.5.24 [S]; A.5.26 [S] |  | DSS02 [U] |
| INC-02 | Notification workflow documented | Reg+Des | 2 | 3 | G6 | 5.0(v) | RS.CO-02 | A.5.24 [S] | 8.4 [S] | DSS02 [U] |
| INC-03 | Incident response exercised | Reg | 1 | 4 |  | App III 3(b)-(c); 3.7; 6.0(ii) | ID.IM-02 | A.5.24 [S] | 8.5 [S] | DSS02 [U] |
| BCP-01 | Approved recovery requirements from business impact analysis | Std+Des | 2 | 3 | G2 | none identified | GV.OC-04; ID.RA-04 | A.5.30 [S] | 8.2 [S] | DSS04 [S] |
| BCP-02 | Service recovery plan documented | Reg | 2 | 3 | G6 | App III 4(a); 1.1.2 | RC.RP-01; ID.IM-04 | A.5.29 [S]; A.5.30 [S] | 8.4 [S] | DSS04 [S] |
| BCP-03 | Service-level restoration exercise completed | Reg+Des | 2 | 4 | G6 | App III 3(b)-(c); 2.3(vii); 3.7 | ID.IM-02; RC.RP-05 | A.5.30 [S] | 8.5 [S]; 8.6 [S] | DSS04 [S] |
| BCP-04 | Transaction reconciliation as a condition of resumption | Des | 2 | 3 |  | none identified | RC.RP-05; RC.RP-06 |  |  | DSS06 [U] |
| TPR-01 | Register of providers and connections for the service | Reg | 1 | 3 |  | App II 1.4(a)-(c); 2.3(i) | GV.SC-04; ID.AM-04 | A.5.19 [S] |  | APO10 [S] |
| TPR-02 | Provider contracts and periodic assessment | Reg | 1 | 3 |  | 2.3(iii)-(v) | GV.SC-05; GV.SC-07 | A.5.20 [S]; A.5.22 [S] |  | APO10 [S] |
| TPR-03 | Recovery coordination tested with critical providers | Reg | 1 | 4 |  | 2.3(vii) | GV.SC-08; ID.IM-02 | A.5.22 [S] | 8.5 [S] | APO10 [S]; DSS04 [S] |

## Control details

### GOV: Security governance

#### GOV-01 Board and CISO accountability for cyber resilience

- **Assessed:** once for the organisation. **Basis:** Reg. **Weight:** 1. **Target grade:** 3. **Decision rules:** none. **Gate:** none.
- **Assessment question:** Has the Board assigned responsibility for the cybersecurity and resilience programme, and is a CISO in post with the reporting line the CBN requires?
- **Expected evidence:** Board or committee terms of reference; CISO appointment and reporting line; Approved cybersecurity strategy or policy.
- **CBN (2024):** 1.1; 1.3; 1.4
- **NIST CSF 2.0:** GV.RR-01; GV.RR-02
- **ISO/IEC 27001:2022 Annex A:** A.5.2 [S]
- **ISO 22301:2019:** 5 [S]
- **COBIT 2019:** EDM03 [U]; APO13 [S]
- **Mapping rationale:** All sources place accountability with leadership. The CBN text is the most specific for Nigerian banks, so it is the primary anchor.
- **Remediation guidance:** Confirm Board-level ownership of the programme and a CISO appointment that meets the CBN requirements.

#### GOV-02 Board-approved risk appetite and acceptance criteria

- **Assessed:** once for the organisation. **Basis:** Reg. **Weight:** 1. **Target grade:** 3. **Decision rules:** DR3, DR10. **Gate:** none.
- **Assessment question:** Are risk appetite and risk acceptance criteria approved by the Board and used when a resilience gap is accepted instead of fixed?
- **Expected evidence:** Risk appetite statement; Board-approved acceptance criteria; Example of an acceptance decision recorded against the criteria.
- **CBN (2024):** 2.1.4; 1.1(xii); 1.5.1(v)
- **NIST CSF 2.0:** GV.RM-02; ID.RA-06
- **COBIT 2019:** APO12 [S]
- **Mapping rationale:** Decision rules DR3 and DR10 allow a gap to be accepted only under approved criteria, so the criteria must exist first.
- **Remediation guidance:** Obtain Board approval of acceptance criteria and apply them to every recorded exception.

#### GOV-03 Reporting of recovery exercise results and open exceptions

- **Assessed:** once for the organisation. **Basis:** Reg+Des. **Weight:** 1. **Target grade:** 3. **Decision rules:** DR6, DR10. **Gate:** none.
- **Assessment question:** Do senior management and the Board receive the results of recovery exercises and the list of open resilience exceptions?
- **Expected evidence:** Board or committee report showing exercise outcomes; Exception register extract presented to management.
- **CBN (2024):** 1.1(viii); 5.0(i)-(ii); App III 3(b)-(c)
- **NIST CSF 2.0:** GV.OV-03; ID.IM-02
- **ISO 22301:2019:** 9 [S]
- **COBIT 2019:** MEA01 [U]
- **Mapping rationale:** The CBN requires drill outcomes to reach senior management and quarterly Board reports. Reporting open exceptions alongside them is this study's addition.
- **Remediation guidance:** Add exercise outcomes and open exceptions to the regular management and Board reports.

### AST: Asset visibility

#### AST-01 Inventory of assets supporting the service

- **Assessed:** for each service. **Basis:** Reg. **Weight:** 1. **Target grade:** 3. **Decision rules:** DR1. **Gate:** none.
- **Assessment question:** Is there a current inventory of the assets that deliver this service, each with a named owner?
- **Expected evidence:** Asset inventory extract for the service; Owner recorded against each asset.
- **CBN (2024):** App II 1.1(a)-(b)
- **NIST CSF 2.0:** ID.AM-01; ID.AM-02
- **ISO/IEC 27001:2022 Annex A:** A.5.9 [S]
- **COBIT 2019:** BAI09 [S]
- **Mapping rationale:** Every source requires an asset inventory. Tying it to a service is what makes it usable for recovery planning.
- **Remediation guidance:** Complete the asset inventory for the service and assign an owner to each asset.

#### AST-02 Criticality classification of the service and its assets

- **Assessed:** for each service. **Basis:** Reg. **Weight:** 1. **Target grade:** 3. **Decision rules:** DR1. **Gate:** none.
- **Assessment question:** Has the service been classified for criticality, with its critical assets identified?
- **Expected evidence:** Critical services register entry; Criticality rating and the reason for it.
- **CBN (2024):** App I; App II 1.1(c)
- **NIST CSF 2.0:** ID.AM-05; GV.OC-04
- **ISO 22301:2019:** 8.2 [S]
- **COBIT 2019:** BAI09 [S]
- **NIST SP 800-34 Rev. 1:** Step 2 [U]
- **Mapping rationale:** The CBN definition of critical systems supplies the test in DR1. CSF ID.AM-05 states the same outcome.
- **Remediation guidance:** Classify the service and its assets using the DR1 criterion and record the result.

#### AST-03 Dependency map for the service

- **Assessed:** for each service. **Basis:** Reg+Des. **Weight:** 1. **Target grade:** 3. **Decision rules:** DR3. **Gate:** none.
- **Assessment question:** Are the shared components, network connections and third-party connections this service depends on mapped and reviewed?
- **Expected evidence:** Dependency register or service map; Network topology diagram; Catalogue of third-party connections with date of last review.
- **CBN (2024):** App II 1.1(i)-(k); App II 1.4(a)-(c)
- **NIST CSF 2.0:** ID.AM-03; ID.AM-04; GV.OC-05
- **ISO 22301:2019:** 8.2 [S]
- **COBIT 2019:** BAI09 [S]
- **Mapping rationale:** The CBN requires a topology diagram and a catalogue of third-party connections. Organising them per service is this study's addition (Finding Two).
- **Remediation guidance:** Map every shared and external dependency of the service and review the map after significant change.

### ACC: Access management

#### ACC-01 Multi-factor authentication on critical systems

- **Assessed:** for each service. **Basis:** Reg. **Weight:** 1. **Target grade:** 3. **Decision rules:** none. **Gate:** none.
- **Assessment question:** Do the critical systems of this service require multi-factor authentication?
- **Expected evidence:** Authentication configuration record; List of systems covered and any exclusions.
- **CBN (2024):** App III 1.1(d)-(e)
- **NIST CSF 2.0:** PR.AA-03
- **ISO/IEC 27001:2022 Annex A:** A.8.5 [S]
- **COBIT 2019:** DSS05 [S]
- **Mapping rationale:** A direct CBN requirement for critical systems, matched by CSF and ISO.
- **Remediation guidance:** Enforce multi-factor authentication on every critical system of the service.

#### ACC-02 Privileged and service accounts recorded and reviewed

- **Assessed:** for each service. **Basis:** Reg. **Weight:** 2. **Target grade:** 3. **Decision rules:** DR4. **Gate:** G4.
- **Assessment question:** Are privileged and service accounts with access to the production or recovery environment of this service recorded in an access control matrix and reviewed?
- **Expected evidence:** Access control matrix extract; Record of the latest review and the changes made.
- **CBN (2024):** App II 1.5; App III 1.1(b); App III 1.2
- **NIST CSF 2.0:** PR.AA-05
- **ISO/IEC 27001:2022 Annex A:** A.8.2 [S]; A.5.18 [S]
- **COBIT 2019:** DSS05 [S]
- **Mapping rationale:** Condition (a) of DR4. The CBN access control matrix is the primary anchor.
- **Remediation guidance:** Record all privileged and service accounts for the service in the access control matrix and review them.

#### ACC-03 Recovery administration separated from production

- **Assessed:** for each service. **Basis:** Des. **Weight:** 2. **Target grade:** 3. **Decision rules:** DR4. **Gate:** G4.
- **Assessment question:** Is the recovery environment administered with credentials and tools that are not shared with production?
- **Expected evidence:** List of recovery administration accounts and tools; Check showing production credentials do not work in the recovery environment; Any recorded exception with its compensating control.
- **CBN (2024):** none identified
- **NIST CSF 2.0:** PR.AA-05; PR.IR-01
- **ISO/IEC 27001:2022 Annex A:** A.8.2 [S]
- **COBIT 2019:** DSS05 [S]
- **Mapping rationale:** Condition (b) of DR4, from Findings Three and Five. No CBN requirement was identified in the text read; CSF PR.AA-05 covers separation of duties in general terms only.
- **Remediation guidance:** Give the recovery environment its own administrative credentials and tools, or record an exception with a compensating control.

#### ACC-04 Vendor access approved, limited, time-bound and monitored

- **Assessed:** for each service. **Basis:** Reg. **Weight:** 2. **Target grade:** 3. **Decision rules:** DR4. **Gate:** G4.
- **Assessment question:** Is vendor access to the systems of this service approved, limited in scope and duration, monitored and revoked after use?
- **Expected evidence:** Vendor access approvals; Session or access logs; Evidence of revocation after the task.
- **CBN (2024):** App III 1.3(a)-(b)
- **NIST CSF 2.0:** PR.AA-05; DE.CM-06
- **ISO/IEC 27001:2022 Annex A:** A.5.19 [S]; A.8.2 [S]
- **COBIT 2019:** DSS05 [S]; APO10 [S]
- **Mapping rationale:** Condition (c) of DR4. A direct CBN requirement.
- **Remediation guidance:** Put vendor access under approval, scope and time limits, monitoring and revocation.

### NET: Network segmentation

#### NET-01 Network segmentation around the service

- **Assessed:** for each service. **Basis:** Std. **Weight:** 1. **Target grade:** 3. **Decision rules:** none. **Gate:** none.
- **Assessment question:** Are the production, recovery, user and third-party network zones of this service separated, with only documented connections allowed between them?
- **Expected evidence:** Network zone design; Firewall or access rule review; List of approved connections between zones.
- **CBN (2024):** App II 1.1(i)-(k)
- **NIST CSF 2.0:** PR.IR-01
- **ISO/IEC 27001:2022 Annex A:** A.8.22 [S]; A.8.20 [S]
- **COBIT 2019:** DSS05 [S]
- **Mapping rationale:** Segmentation is recommended by CISA et al. (2023) and ISO. The CBN text read requires a topology diagram and connection catalogue but states no explicit segmentation requirement, so the basis is Std, not Reg.
- **Remediation guidance:** Separate the service's network zones and allow only documented connections between them.

#### NET-02 Segmentation tested in both directions

- **Assessed:** for each service. **Basis:** Des. **Weight:** 1. **Target grade:** 4. **Decision rules:** none. **Gate:** none.
- **Assessment question:** Has a test shown both that an unauthorised path into the service is blocked and that normal transactions still pass?
- **Expected evidence:** Test script and result for the blocked path; Test result for the normal transaction; Date of test.
- **CBN (2024):** 2.2(iii)
- **NIST CSF 2.0:** PR.IR-01; ID.IM-02
- **ISO/IEC 27001:2022 Annex A:** A.8.22 [S]
- **COBIT 2019:** DSS05 [S]
- **Mapping rationale:** From Finding Five: a restriction that blocks legitimate transactions is also a failure. The paired test is this study's proposal; the CBN penetration test requirement is related but not equivalent.
- **Remediation guidance:** Run and record a paired test: blocked unauthorised access and an unaffected normal transaction.

### RED: Infrastructure redundancy

#### RED-01 Alternative capacity for critical components

- **Assessed:** for each service. **Basis:** Std+Des. **Weight:** 1. **Target grade:** 3. **Decision rules:** DR3. **Gate:** none.
- **Assessment question:** Does each critical component of this service have an alternative, so that no single point of failure is left untreated?
- **Expected evidence:** Architecture record showing alternatives; List of single points of failure and their treatment.
- **CBN (2024):** 3.7
- **NIST CSF 2.0:** PR.IR-03; PR.IR-04
- **ISO/IEC 27001:2022 Annex A:** A.8.14 [S]
- **ISO 22301:2019:** 8.3 [U]
- **COBIT 2019:** BAI04 [U]; DSS04 [S]
- **NIST SP 800-34 Rev. 1:** Step 4 [U]
- **Mapping rationale:** ISO and CSF address redundancy directly. The CBN text read addresses single points of failure in the industry, not inside a bank, so it is a related reference only.
- **Remediation guidance:** Provide an alternative for each critical component or record the treatment of the single point of failure.

#### RED-02 Fail-over demonstrated by test

- **Assessed:** for each service. **Basis:** Std. **Weight:** 1. **Target grade:** 4. **Decision rules:** none. **Gate:** none.
- **Assessment question:** Has fail-over to the alternative been tested successfully within the validity period?
- **Expected evidence:** Fail-over test report with date and result; Comparison of achieved time against the approved RTO.
- **CBN (2024):** 2.3(vii)
- **NIST CSF 2.0:** PR.IR-03; ID.IM-02
- **ISO/IEC 27001:2022 Annex A:** A.5.30 [S]
- **ISO 22301:2019:** 8.5 [S]
- **COBIT 2019:** DSS04 [S]
- **NIST SP 800-34 Rev. 1:** Step 6 [U]
- **Mapping rationale:** Finding Four: an alternative that has not been exercised is unproven.
- **Remediation guidance:** Test fail-over and record the result against the approved recovery time objective.

#### RED-03 Alternative is independent of the compromise

- **Assessed:** for each service. **Basis:** Des. **Weight:** 1. **Target grade:** 3. **Decision rules:** none. **Gate:** none.
- **Assessment question:** Would the alternative remain trustworthy if the primary were compromised, for example by unwanted changes replicating or by a shared administrative element?
- **Expected evidence:** Analysis of what the primary and the alternative share; Replication design showing how corrupted data is prevented from propagating unchecked.
- **CBN (2024):** none identified
- **NIST CSF 2.0:** PR.IR-03
- **ISO/IEC 27001:2022 Annex A:** A.8.14 [S]
- **COBIT 2019:** DSS04 [S]
- **Mapping rationale:** Finding Three, drawing on Ross et al. (2021). No reviewed source states it as a testable requirement.
- **Remediation guidance:** Identify what the primary and the alternative share and remove or control each shared element.

### BKP: Backup and recovery

#### BKP-01 Protected backup copy

- **Assessed:** for each service. **Basis:** Reg+Std+Des. **Weight:** 2. **Target grade:** 3. **Decision rules:** DR5. **Gate:** G5.
- **Assessment question:** Is a backup of this service's data held in a copy that production administrators cannot alter or delete?
- **Expected evidence:** Backup architecture record; Access list for the protected copy; Configuration showing offline or immutable storage.
- **CBN (2024):** App III 1.6(g)
- **NIST CSF 2.0:** PR.DS-11
- **ISO/IEC 27001:2022 Annex A:** A.8.13 [S]
- **COBIT 2019:** DSS04 [S]
- **NIST SP 800-34 Rev. 1:** Step 4 [U]
- **Mapping rationale:** Condition (a) of DR5. The CBN requires secure backup storage; CISA et al. (2023) recommend offline copies; protection from production administrators is this study's criterion.
- **Remediation guidance:** Hold a backup copy that production administrators cannot alter or delete.

#### BKP-02 Restoration tested within the validity period

- **Assessed:** for each service. **Basis:** Reg. **Weight:** 2. **Target grade:** 4. **Decision rules:** DR5. **Gate:** G5.
- **Assessment question:** Has restoration of this service's data from backup been tested successfully within the validity period?
- **Expected evidence:** Restoration test report with date and result; Data set restored and time taken.
- **CBN (2024):** App III 1.6(g); App III 3(i)
- **NIST CSF 2.0:** PR.DS-11
- **ISO/IEC 27001:2022 Annex A:** A.8.13 [S]
- **ISO 22301:2019:** 8.5 [S]
- **COBIT 2019:** DSS04 [S]
- **NIST SP 800-34 Rev. 1:** Step 6 [U]
- **Mapping rationale:** Condition (b) of DR5. A direct CBN requirement; the validity period is set by the bank.
- **Remediation guidance:** Run a restoration test for the service's data and record the date and result.

#### BKP-03 Clean recovery point identified

- **Assessed:** for each service. **Basis:** Std+Des. **Weight:** 2. **Target grade:** 3. **Decision rules:** DR5, DR7. **Gate:** G5.
- **Assessment question:** Is the recovery point checked for integrity and for indicators of compromise, and is the clean recovery point identified and recorded?
- **Expected evidence:** Integrity check record; Scan result for indicators of compromise; Record naming the clean recovery point.
- **CBN (2024):** App III 4(b)
- **NIST CSF 2.0:** RC.RP-03
- **ISO/IEC 27001:2022 Annex A:** A.8.13 [S]
- **COBIT 2019:** DSS04 [S]
- **Mapping rationale:** Condition (c) of DR5. CSF RC.RP-03 states the outcome; the CBN verify-before-restore requirement concerns the threat, not the data, so it is related only.
- **Remediation guidance:** Check recovery points for integrity and compromise and record which one is clean.

### MON: Monitoring and detection

#### MON-01 Logging on systems supporting the service

- **Assessed:** for each service. **Basis:** Reg. **Weight:** 1. **Target grade:** 3. **Decision rules:** none. **Gate:** none.
- **Assessment question:** Is logging enabled on the systems of this service, including the activity of privileged users?
- **Expected evidence:** Logging configuration record; Sample of privileged activity logs; Log retention setting.
- **CBN (2024):** App III 2.1(g); App III 1.2
- **NIST CSF 2.0:** PR.PS-04
- **ISO/IEC 27001:2022 Annex A:** A.8.15 [S]
- **COBIT 2019:** DSS05 [S]
- **Mapping rationale:** A direct CBN requirement, matched by CSF and ISO.
- **Remediation guidance:** Enable logging, including privileged activity, on every system of the service.

#### MON-02 Continuous monitoring covers production and recovery

- **Assessed:** for each service. **Basis:** Reg+Des. **Weight:** 1. **Target grade:** 3. **Decision rules:** none. **Gate:** none.
- **Assessment question:** Does continuous monitoring through a security operations centre cover this service's systems in both the production and the recovery environment?
- **Expected evidence:** Monitoring coverage list; Sample alerts for the service; Evidence that recovery-environment sources are onboarded.
- **CBN (2024):** 3.3; App III 2.1(a); App III 2.1(d); App III 2.1(e)
- **NIST CSF 2.0:** DE.CM-01; DE.CM-09
- **ISO/IEC 27001:2022 Annex A:** A.8.16 [S]
- **COBIT 2019:** DSS05 [S]
- **Mapping rationale:** The CBN requires 24x7 monitoring through a SOC. Asking explicitly about the recovery environment is this study's addition.
- **Remediation guidance:** Extend monitoring coverage to every system of the service, including the recovery environment.

### INC: Incident response

#### INC-01 Incident response plan with criteria for moving to recovery

- **Assessed:** for each service. **Basis:** Reg. **Weight:** 2. **Target grade:** 3. **Decision rules:** DR6, DR7. **Gate:** none.
- **Assessment question:** Does an incident response plan or playbook cover this service and state that threats must be verified as addressed before systems, data or access are restored?
- **Expected evidence:** Incident response plan or playbook for the service; The section stating the criteria for moving to recovery.
- **CBN (2024):** App III 3(a); App III 4(b)
- **NIST CSF 2.0:** ID.IM-04; RS.MA-01; RS.MA-05
- **ISO/IEC 27001:2022 Annex A:** A.5.24 [S]; A.5.26 [S]
- **COBIT 2019:** DSS02 [U]
- **Mapping rationale:** A direct CBN requirement and the documentary basis of DR7.
- **Remediation guidance:** Write or update the playbook for the service and include the verify-before-restore criteria.

#### INC-02 Notification workflow documented

- **Assessed:** for each service. **Basis:** Reg+Des. **Weight:** 2. **Target grade:** 3. **Decision rules:** DR6. **Gate:** G6.
- **Assessment question:** Is there a documented workflow for the external notifications an incident affecting this service may require, with triggers, recipients and time limits?
- **Expected evidence:** Notification workflow; Named role responsible for each notification; Contact details and templates.
- **CBN (2024):** 5.0(v)
- **NIST CSF 2.0:** RS.CO-02
- **ISO/IEC 27001:2022 Annex A:** A.5.24 [S]
- **ISO 22301:2019:** 8.4 [S]
- **COBIT 2019:** DSS02 [U]
- **Mapping rationale:** The CBN 24-hour duty is read from the framework text. The data protection and national CERT duties are taken from Table 1.1 of the paper and were not re-read here. Combining them into one workflow is this study's proposal.
- **Remediation guidance:** Document the notification workflow with triggers, recipients, time limits and owners.

#### INC-03 Incident response exercised

- **Assessed:** for each service. **Basis:** Reg. **Weight:** 1. **Target grade:** 4. **Decision rules:** none. **Gate:** none.
- **Assessment question:** Has incident response for this service been exercised by a drill or tabletop within the validity period, with the outcome reported to senior management?
- **Expected evidence:** Exercise report with date; Record of the report to senior management; Changes made to the plan afterwards.
- **CBN (2024):** App III 3(b)-(c); 3.7; 6.0(ii)
- **NIST CSF 2.0:** ID.IM-02
- **ISO/IEC 27001:2022 Annex A:** A.5.24 [S]
- **ISO 22301:2019:** 8.5 [S]
- **COBIT 2019:** DSS02 [U]
- **NIST SP 800-34 Rev. 1:** Step 6 [U]
- **Mapping rationale:** A direct CBN requirement.
- **Remediation guidance:** Run a drill or tabletop exercise for the service and report the outcome to senior management.

### BCP: Business continuity

#### BCP-01 Approved recovery requirements from business impact analysis

- **Assessed:** for each service. **Basis:** Std+Des. **Weight:** 2. **Target grade:** 3. **Decision rules:** DR2. **Gate:** G2.
- **Assessment question:** Are the maximum tolerable downtime, RTO and RPO for this service derived from a business impact analysis and approved in writing by the business owner and the risk function?
- **Expected evidence:** Business impact analysis for the service; Written approval of the recovery requirements; Date of last review.
- **CBN (2024):** none identified
- **NIST CSF 2.0:** GV.OC-04; ID.RA-04
- **ISO/IEC 27001:2022 Annex A:** A.5.30 [S]
- **ISO 22301:2019:** 8.2 [S]
- **COBIT 2019:** DSS04 [S]
- **NIST SP 800-34 Rev. 1:** Step 2 [U]
- **Mapping rationale:** DR2. The CBN text read does not mention recovery time or recovery point objectives, so the basis is NIST SP 800-34 and ISO 22301; the approval roles are this study's proposal.
- **Remediation guidance:** Complete the business impact analysis and obtain written approval of the recovery requirements.

#### BCP-02 Service recovery plan documented

- **Assessed:** for each service. **Basis:** Reg. **Weight:** 2. **Target grade:** 3. **Decision rules:** DR6. **Gate:** G6.
- **Assessment question:** Is there a documented recovery plan for this service, including coordination with its providers?
- **Expected evidence:** Service recovery plan; Provider contact and coordination steps; Date of last update.
- **CBN (2024):** App III 4(a); 1.1.2
- **NIST CSF 2.0:** RC.RP-01; ID.IM-04
- **ISO/IEC 27001:2022 Annex A:** A.5.29 [S]; A.5.30 [S]
- **ISO 22301:2019:** 8.4 [S]
- **COBIT 2019:** DSS04 [S]
- **NIST SP 800-34 Rev. 1:** Step 5 [U]
- **Mapping rationale:** A direct CBN requirement and a condition of DR6.
- **Remediation guidance:** Document the recovery plan for the service, including provider coordination.

#### BCP-03 Service-level restoration exercise completed

- **Assessed:** for each service. **Basis:** Reg+Des. **Weight:** 2. **Target grade:** 4. **Decision rules:** DR6. **Gate:** G6.
- **Assessment question:** Has a restoration exercise for the whole service, not only its systems, been completed within the validity period and its outcome reported to senior management?
- **Expected evidence:** Exercise report with date, scope and result; Record of the report to senior management; Completed resumption checklist (Tool 2) if used.
- **CBN (2024):** App III 3(b)-(c); 2.3(vii); 3.7
- **NIST CSF 2.0:** ID.IM-02; RC.RP-05
- **ISO/IEC 27001:2022 Annex A:** A.5.30 [S]
- **ISO 22301:2019:** 8.5 [S]; 8.6 [S]
- **COBIT 2019:** DSS04 [S]
- **NIST SP 800-34 Rev. 1:** Step 6 [U]
- **Mapping rationale:** A condition of DR6. The CBN requires drills and recovery testing; requiring the exercise at the level of the whole service is this study's criterion (Finding Four).
- **Remediation guidance:** Run a restoration exercise for the whole service and report the outcome.

#### BCP-04 Transaction reconciliation as a condition of resumption

- **Assessed:** for each service. **Basis:** Des. **Weight:** 2. **Target grade:** 3. **Decision rules:** DR8, DR9. **Gate:** none.
- **Assessment question:** Is there a defined procedure to reconcile this service's transactions after restoration, and is its completion a condition of resuming the service?
- **Expected evidence:** Reconciliation procedure for the service; Named approvers for resumption; Tolerance for unresolved differences.
- **CBN (2024):** none identified
- **NIST CSF 2.0:** RC.RP-05; RC.RP-06
- **COBIT 2019:** DSS06 [U]
- **Mapping rationale:** DR8 and DR9, from Finding Four. No reviewed source specifies service-level reconciliation checks. CSF RC.RP-05 covers the integrity of restored assets in general terms.
- **Remediation guidance:** Define the reconciliation procedure and make its completion a condition of resumption.

### TPR: Third-party risk management

#### TPR-01 Register of providers and connections for the service

- **Assessed:** for each service. **Basis:** Reg. **Weight:** 1. **Target grade:** 3. **Decision rules:** DR3. **Gate:** none.
- **Assessment question:** Is there a current record of the third-party providers and connections this service relies on, with their criticality?
- **Expected evidence:** Provider register extract; Criticality of each provider; Date of last review.
- **CBN (2024):** App II 1.4(a)-(c); 2.3(i)
- **NIST CSF 2.0:** GV.SC-04; ID.AM-04
- **ISO/IEC 27001:2022 Annex A:** A.5.19 [S]
- **COBIT 2019:** APO10 [S]
- **Mapping rationale:** A direct CBN requirement, matched by CSF GV.SC-04.
- **Remediation guidance:** Record every provider and connection the service relies on and rate its criticality.

#### TPR-02 Provider contracts and periodic assessment

- **Assessed:** for each service. **Basis:** Reg. **Weight:** 1. **Target grade:** 3. **Decision rules:** none. **Gate:** none.
- **Assessment question:** Do contracts with this service's critical providers include security and recovery obligations and a right to audit, and are the providers assessed periodically?
- **Expected evidence:** Contract or service agreement clauses; Latest provider assessment or audit report.
- **CBN (2024):** 2.3(iii)-(v)
- **NIST CSF 2.0:** GV.SC-05; GV.SC-07
- **ISO/IEC 27001:2022 Annex A:** A.5.20 [S]; A.5.22 [S]
- **COBIT 2019:** APO10 [S]
- **Mapping rationale:** A direct CBN requirement, matched by CSF and ISO.
- **Remediation guidance:** Add security, recovery and audit clauses to provider contracts and assess providers periodically.

#### TPR-03 Recovery coordination tested with critical providers

- **Assessed:** for each service. **Basis:** Reg. **Weight:** 1. **Target grade:** 4. **Decision rules:** DR3, DR6. **Gate:** none.
- **Assessment question:** Has recovery been tested jointly with this service's critical providers within the validity period?
- **Expected evidence:** Joint exercise report with date and result; Provider participation record; Follow-up actions.
- **CBN (2024):** 2.3(vii)
- **NIST CSF 2.0:** GV.SC-08; ID.IM-02
- **ISO/IEC 27001:2022 Annex A:** A.5.22 [S]
- **ISO 22301:2019:** 8.5 [S]
- **COBIT 2019:** APO10 [S]; DSS04 [S]
- **NIST SP 800-34 Rev. 1:** Step 6 [U]
- **Mapping rationale:** A direct CBN requirement. It also feeds the DR3 test for an unresolved provider dependency.
- **Remediation guidance:** Run a joint recovery test with each critical provider and record the result.

## Reference register

Only references used by at least one control are listed. CBN entries are the researcher's paraphrases. NIST CSF entries are quoted from the published text, which NIST makes freely available. ISO and COBIT entries give short titles only.

### CBN (2024)

| Reference | Text | Status |
|---|---|---|
| 1.1 | Board oversight of and responsibility for the cybersecurity programme | P |
| 1.1(viii) | Quarterly reports to the Board on the status of the cybersecurity programme | P |
| 1.1(xii) | Cybersecurity risk appetite defined in the enterprise risk management framework | P |
| 1.1.2 | Minimum contents of the cybersecurity programme, including incident response planning and a data backup and recovery plan | P |
| 1.3 | Responsibilities of the Chief Information Security Officer | P |
| 1.4 | Requirements for appointing the CISO, including the reporting line | P |
| 1.5.1(v) | Steering committee recommends the risk acceptance level to the Board | P |
| 2.1.4 | Risk treatment options; risk acceptance criteria defined and approved by the Board | P |
| 2.2(iii) | Penetration test by a third party at least annually | P |
| 2.3(i) | Third-party risk management framework covering selection, due diligence, monitoring and incident response | P |
| 2.3(iii)-(v) | Contracts carry security measures; third parties are routinely assessed; service agreements give a right to audit | P |
| 2.3(vii) | Business continuity response and recovery planning and testing conducted with third-party providers | P |
| 3.3 | Capability for ongoing (24/7) monitoring to detect anomalies or incidents | P |
| 3.7 | Participation in industry cyber exercises; avoid creating single points of failure in the industry | P |
| 5.0(i)-(ii) | Performance metrics that identify deficiencies, failed controls and progress in resolving issues | P |
| 5.0(v) | Cyber incidents reported to the CBN not later than 24 hours after detection | P |
| 6.0(ii) | Participation in industry cyber exercises to evaluate preparedness to recover | P |
| App I | Definitions of critical systems and of a cyber-incident | P |
| App II 1.1(a)-(b) | Up-to-date inventory of IT assets; ownership assigned for each asset | P |
| App II 1.1(c) | Devices categorised by the criticality and sensitivity of the information they handle | P |
| App II 1.1(i)-(k) | Network topology diagram; catalogue of network connections to third parties, reviewed regularly | P |
| App II 1.4(a)-(c) | Record of third-party service providers; third-party connections identified, documented and reviewed | P |
| App II 1.5 | Privileged employee and service accounts recorded in an access control matrix and reviewed | P |
| App III 1.1(b) | Periodic review of user access against least privilege | P |
| App III 1.1(d)-(e) | Multi-factor authentication and role-based access; critical systems must use multi-factor authentication | P |
| App III 1.2 | Privileged access management controls, logging of privileged activity, no shared passwords on default or anonymous privileged accounts | P |
| App III 1.3(a)-(b) | Vendor access is not unfettered; it is approved, limited in scope and duration, monitored and revoked | P |
| App III 1.6(g) | Regular data backup, secure backup storage, and regular testing of restoration | P |
| App III 2.1(a) | Continuous (24x7) monitoring of critical systems, databases and networks | P |
| App III 2.1(d) | Monitoring of the physical environment, including the disaster recovery site | P |
| App III 2.1(e) | Security monitoring through a security operations centre | P |
| App III 2.1(g) | Logging enabled on all systems and applications | P |
| App III 3(a) | Incident response plan and playbooks | P |
| App III 3(b)-(c) | Regular drills and tabletop exercises; outcomes communicated to senior management, who also take part | P |
| App III 3(i) | Backup and recovery mechanisms for critical data; periodic backup restoration tests | P |
| App III 4(a) | Recovery plan, processes and procedures to restore affected systems and assets | P |
| App III 4(b) | Threats verified as addressed before affected systems, data or access are restored | P |

### NIST CSF 2.0

| Reference | Text | Status |
|---|---|---|
| GV.OC-04 | Critical objectives, capabilities, and services that external stakeholders depend on or expect from the organization are understood and communicated | P |
| GV.OC-05 | Outcomes, capabilities, and services that the organization depends on are understood and communicated | P |
| GV.RM-02 | Risk appetite and risk tolerance statements are established, communicated, and maintained | P |
| GV.RR-01 | Organizational leadership is responsible and accountable for cybersecurity risk and fosters a culture that is risk-aware, ethical, and continually improving | P |
| GV.RR-02 | Roles, responsibilities, and authorities related to cybersecurity risk management are established, communicated, understood, and enforced | P |
| GV.OV-03 | Organizational cybersecurity risk management performance is evaluated and reviewed for adjustments needed | P |
| GV.SC-04 | Suppliers are known and prioritized by criticality | P |
| GV.SC-05 | Requirements to address cybersecurity risks in supply chains are established, prioritized, and integrated into contracts and other types of agreements with suppliers and other relevant third parties | P |
| GV.SC-07 | The risks posed by a supplier, their products and services, and other third parties are understood, recorded, prioritized, assessed, responded to, and monitored over the course of the relationship | P |
| GV.SC-08 | Relevant suppliers and other third parties are included in incident planning, response, and recovery activities | P |
| ID.AM-01 | Inventories of hardware managed by the organization are maintained | P |
| ID.AM-02 | Inventories of software, services, and systems managed by the organization are maintained | P |
| ID.AM-03 | Representations of the organization's authorized network communication and internal and external network data flows are maintained | P |
| ID.AM-04 | Inventories of services provided by suppliers are maintained | P |
| ID.AM-05 | Assets are prioritized based on classification, criticality, resources, and impact on the mission | P |
| ID.RA-04 | Potential impacts and likelihoods of threats exploiting vulnerabilities are identified and recorded | P |
| ID.RA-06 | Risk responses are chosen, prioritized, planned, tracked, and communicated | P |
| ID.IM-02 | Improvements are identified from security tests and exercises, including those done in coordination with suppliers and relevant third parties | P |
| ID.IM-04 | Incident response plans and other cybersecurity plans that affect operations are established, communicated, maintained, and improved | P |
| PR.AA-03 | Users, services, and hardware are authenticated | P |
| PR.AA-05 | Access permissions, entitlements, and authorizations are defined in a policy, managed, enforced, and reviewed, and incorporate the principles of least privilege and separation of duties | P |
| PR.DS-11 | Backups of data are created, protected, maintained, and tested | P |
| PR.PS-04 | Log records are generated and made available for continuous monitoring | P |
| PR.IR-01 | Networks and environments are protected from unauthorized logical access and usage | P |
| PR.IR-03 | Mechanisms are implemented to achieve resilience requirements in normal and adverse situations | P |
| PR.IR-04 | Adequate resource capacity to ensure availability is maintained | P |
| DE.CM-01 | Networks and network services are monitored to find potentially adverse events | P |
| DE.CM-06 | External service provider activities and services are monitored to find potentially adverse events | P |
| DE.CM-09 | Computing hardware and software, runtime environments, and their data are monitored to find potentially adverse events | P |
| RS.MA-01 | The incident response plan is executed in coordination with relevant third parties once an incident is declared | P |
| RS.MA-05 | The criteria for initiating incident recovery are applied | P |
| RS.CO-02 | Internal and external stakeholders are notified of incidents | P |
| RC.RP-01 | The recovery portion of the incident response plan is executed once initiated from the incident response process | P |
| RC.RP-03 | The integrity of backups and other restoration assets is verified before using them for restoration | P |
| RC.RP-05 | The integrity of restored assets is verified, systems and services are restored, and normal operating status is confirmed | P |
| RC.RP-06 | The end of incident recovery is declared based on criteria, and incident-related documentation is completed | P |

### ISO/IEC 27001:2022 Annex A

| Reference | Text | Status |
|---|---|---|
| A.5.2 | Information security roles and responsibilities | S |
| A.5.9 | Inventory of information and other associated assets | S |
| A.5.18 | Access rights | S |
| A.5.19 | Information security in supplier relationships | S |
| A.5.20 | Addressing information security within supplier agreements | S |
| A.5.22 | Monitoring, review and change management of supplier services | S |
| A.5.24 | Information security incident management planning and preparation | S |
| A.5.26 | Response to information security incidents | S |
| A.5.29 | Information security during disruption | S |
| A.5.30 | ICT readiness for business continuity | S |
| A.8.2 | Privileged access rights | S |
| A.8.5 | Secure authentication | S |
| A.8.13 | Information backup | S |
| A.8.14 | Redundancy of information processing facilities | S |
| A.8.15 | Logging | S |
| A.8.16 | Monitoring activities | S |
| A.8.20 | Networks security | S |
| A.8.22 | Segregation of networks | S |

### ISO 22301:2019

| Reference | Text | Status |
|---|---|---|
| 5 | Leadership | S |
| 8.2 | Business impact analysis and risk assessment | S |
| 8.3 | Business continuity strategies and solutions | U |
| 8.4 | Business continuity plans and procedures | S |
| 8.5 | Exercise programme | S |
| 8.6 | Evaluation of business continuity documentation and capabilities | S |
| 9 | Performance evaluation | S |

### COBIT 2019

| Reference | Text | Status |
|---|---|---|
| EDM03 | Ensured Risk Optimization | U |
| APO10 | Managed Vendors | S |
| APO12 | Managed Risk | S |
| APO13 | Managed Security | S |
| BAI04 | Managed Availability and Capacity | U |
| BAI09 | Managed Assets | S |
| DSS02 | Managed Service Requests and Incidents | U |
| DSS04 | Managed Continuity | S |
| DSS05 | Managed Security Services | S |
| DSS06 | Managed Business Process Controls | U |
| MEA01 | Managed Performance and Conformance Monitoring | U |

### NIST SP 800-34 Rev. 1

| Reference | Text | Status |
|---|---|---|
| Step 2 | Conduct the business impact analysis | U |
| Step 4 | Create contingency strategies | U |
| Step 5 | Develop an information system contingency plan | U |
| Step 6 | Ensure plan testing, training and exercises | U |
