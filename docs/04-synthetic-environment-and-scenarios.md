# Synthetic Banking Environment and Demonstration Scenarios

**Version:** 0.1 draft for student review, 14 November 2026

> **Everything in this document is fictional.** "Bank X" is not a real bank. No asset, provider, configuration, date or result describes any Nigerian bank or any real incident. Provider names are generic on purpose. Results produced from this data are tests of the software, not findings about banks.

Expected results are written here **before** the prototype exists, so that the tests in Phase 5 compare the software against a prediction and not the other way round.

---

## 1. Bank X

### 1.1 Services

| ID | Service | Criticality (1–5) | Depends on |
|---|---|---:|---|
| SVC-CBS | Core banking transactions | 5 | None |
| SVC-PAY | Electronic payments | 5 | SVC-CBS |
| SVC-ATM | ATM services | 4 | SVC-PAY, SVC-CBS |

The existing paper's illustration treats payments and core banking as depending on each other. The prototype records one direction only (payments depend on core banking) to keep the dependency rule simple. This is a stated simplification.

### 1.2 Assets

| ID | Asset | Type | Site | Used by |
|---|---|---|---|---|
| A01 | Core banking application cluster | Application server | Primary DC | CBS |
| A02 | Core banking database (primary) | Database | Primary DC | CBS |
| A03 | Core banking database (standby) | Database | DR site | CBS |
| A04 | Payment switch application | Application server | Primary DC | PAY |
| A05 | Payment database | Database | Primary DC | PAY |
| A06 | Hardware security module pair | Security system | Primary DC | PAY, ATM |
| A07 | ATM terminal handler | Application server | Primary DC | ATM |
| A08 | ATM fleet network links | Network | Branches | ATM |
| A09 | Core network switches | Network | Primary DC | CBS, PAY, ATM |
| A10 | Perimeter firewall pair | Firewall | Primary DC | CBS, PAY, ATM |
| A11 | Internal segmentation firewall | Firewall | Primary DC | CBS, PAY, ATM |
| A12 | Identity directory | Identity system | Primary DC | CBS, PAY, ATM |
| A13 | Privileged access management server | Security system | Primary DC | CBS, PAY, ATM |
| A14 | Security monitoring platform (SOC) | Security system | Primary DC | CBS, PAY, ATM |
| A15 | Backup server and protected backup vault | Backup | DR site | CBS, PAY, ATM |
| A16 | Primary data centre facility | Data centre | Primary DC | CBS, PAY, ATM |
| A17 | Disaster recovery site | Data centre | DR site | CBS, PAY, ATM |
| A18 | Wide-area carrier A | Third-party connectivity | External | CBS, PAY, ATM |
| A19 | Wide-area carrier B | Third-party connectivity | External | CBS, PAY, ATM |
| A20 | National payment switch connection ("SwitchCo") | Third-party service | External | PAY |

### 1.3 Reference state B0

B0 is a clean reference used for testing, not a claim about what banks look like. In B0:

- every service has named owners and approved recovery requirements;
- every control is at its target grade with an evidence reference, and every grade 4 has a test date within the validity period;
- no dependency is unresolved;
- one threat scenario is recorded for each service.

**Expected result for B0:** all gates pass for all three services; all three are **Ready**; the action list is empty. The overall score is below 100% because most targets are grade 3. The exact figure will be calculated by hand from the formulas in the specification and compared with the software's output.

Each scenario below is B0 plus the stated changes.

A separate **demonstration profile** combining several deficiencies will be seeded for the dashboard, so that the screens show a realistic mixture. It is not used as a test oracle.

---

## 2. Scenarios

### SC1 Failure of a primary core banking application server

| | |
|---|---|
| **Purpose** | The positive path: the tool must be able to say "Ready", and an ordinary gap must not block readiness |
| **Assumptions** | One node of A01 fails. The cluster and the standby database are available. No compromise is involved |
| **Changes to B0** | Risk scenario for CBS: likelihood 3, impact 4. MON-02 for CBS is recorded at grade 2 (monitoring of the standby is stated but no evidence is referenced). A Tool 2 record for a fail-over exercise has every check answered Yes |
| **Expected** | CBS, PAY and ATM are all **Ready**. Exactly one action appears: MON-02 for CBS, action type "Record evidence", tier **P3**. Tool 2 decision: **Resume** |

### SC2 Loss of connectivity to the payment processor

| | |
|---|---|
| **Purpose** | Dependency rule (DR3), propagation to a dependent service (G7), and the exception waiver |
| **Assumptions** | The link to "SwitchCo" (A20) runs over carrier A only. Joint recovery with the provider has not been tested |
| **Changes to B0** | Dependency PAY→A20 is marked as a single point of failure with no tested alternative and no tested recovery coordination. TPR-03 for PAY is grade 1 |
| **Expected, step 1** | PAY: G3 **fails**; status **Not demonstrated**. ATM: G7 **fails**; status **Not demonstrated**. CBS: **Ready**. Actions include a P1 item for the unresolved dependency and an item for TPR-03 |
| **Step 2** | An approved, in-date risk-acceptance exception is recorded against the dependency PAY→A20 |
| **Expected, step 2** | PAY: G3 passes by exception; status **Ready with accepted exceptions**. ATM: **Ready**. The exception is listed in the report |
| **Step 3** | The exception's due date is moved into the past |
| **Expected, step 3** | The exception is flagged overdue and no longer waives the gate; results return to those of step 1 |

### SC3 Ransomware affecting payment processing

This reproduces the hypothetical illustration in Section 4.8.6 of the existing paper.

| | |
|---|---|
| **Purpose** | Shared credentials (DR4), a missing restoration exercise (DR6), and a conditional resumption decision (DR9) |
| **Assumptions** | A04 and A05 are encrypted. The attacker used a vendor support account that is also valid at the DR site. No service-level restoration exercise has been run for payments |
| **Changes to B0** | For PAY: ACC-03 grade 1; ACC-04 recorded at grade 3 but with no evidence reference; BCP-03 grade 1. Risk scenario for PAY: likelihood 4, impact 5, affects the recovery environment |
| **Expected** | PAY: ACC-04 has an effective grade of 2 (evidence rule). G4 **fails** and G6 **fails**; status **Not demonstrated**. ATM: G7 **fails**; **Not demonstrated**. CBS: **Ready**. The three PAY items are tier **P1** |
| **Tool 2 record** | All checks Yes except 4.1 (payments reconciliation), which is No. Checks 5.1, 5.2 and 6.1 are Yes. Two conditions are recorded, each with an owner and an expiry date |
| **Expected decision** | **Resume conditionally**, as in the paper's Table 4.6 |
| **Variant** | The same record with the conditions removed |
| **Expected decision** | **Withhold** |

### SC4 Failure of the primary data centre

| | |
|---|---|
| **Purpose** | A good score with a failed gate: redundancy that is tested for availability but not independent of a compromise (Finding Three) |
| **Assumptions** | A16 is lost. Fail-over of core banking to the DR site has been tested and works. The standby replicates from the primary without delay or validation, and the DR site is administered with production credentials |
| **Changes to B0** | For CBS: RED-03 grade 1; ACC-03 recorded at grade 3 with no evidence reference. RED-01 and RED-02 stay at target |
| **Expected** | CBS: ACC-03 has an effective grade of 2; G4 **fails**; status **Not demonstrated**. PAY and ATM: G7 **fails**; **Not demonstrated**. The CBS score falls only slightly from its B0 value, because just two of its controls changed. The hand calculation in Phase 5 will state both figures. The redundancy domain shows RED-01 and RED-02 at target |
| **Point demonstrated** | The score and the status disagree, and the status governs |

### SC5 Inadequate backup testing

| | |
|---|---|
| **Purpose** | The validity-period rule and the evidence rule (DR5) |
| **Assumptions** | Backups of the ATM terminal handler data exist and are protected. The last restoration test is 500 days before the assessment date. The integrity check is claimed but not evidenced |
| **Changes to B0** | For ATM: BKP-02 recorded at grade 4 with a test date 500 days old; BKP-03 recorded at grade 3 with no evidence reference |
| **Expected** | ATM: BKP-02 has an effective grade of 3 and BKP-03 an effective grade of 2. G5 **fails**; status **Not demonstrated**. CBS and PAY: **Ready**, because ATM depends on them and not the reverse. Two P1 actions for ATM: BKP-02 "Test and record the result" and BKP-03 "Record evidence" |
| **Variant** | Validity period set to 730 days |
| **Expected** | BKP-02 is effective at grade 4, but G5 still fails on BKP-03 |

---

## 3. Checks applied to every scenario

1. **Consistency.** Running the same scenario twice gives identical scores, gate results, action order and report content.
2. **Weight independence of status.** Gate results and readiness status are identical under weighting schemes A, B and C.
3. **Traceability.** Every action in the report names a service, a control or dependency, the current and target grade, and the gate or rule.
4. **Sensitivity.** Scores and service rankings are recorded under schemes A, B and C and any change in ranking is reported.

---

## 4. What the scenarios do not show

The scenarios confirm that the software applies the specified rules. They do not show that the rules are the right ones, that a bank could supply the inputs, or that using the framework would shorten recovery or reduce loss. The expected results were written by the same person who wrote the rules, which is a limitation of any self-evaluated artefact.
