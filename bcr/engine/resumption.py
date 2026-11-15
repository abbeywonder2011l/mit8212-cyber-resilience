"""Tool 2: safe service-resumption checklist and decision (DR7-DR9; specification section 8).

Check 7.1 of the paper's Table 4.5 ("decision recorded") is the output of this
rule, so it is computed here and not entered.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date

YES, NO, NA = "yes", "no", "na"

RESUME = "Resume"
RESUME_CONDITIONALLY = "Resume conditionally"
WITHHOLD = "Withhold"

# (number, section, text, rule)
CHECKS: tuple[tuple[str, str, str, str], ...] = (
    ("1.1", "Compromise containment",
     "Compromised accounts, endpoints and connections are identified, isolated or revoked", "DR7"),
    ("1.2", "Compromise containment",
     "Threats are verified as addressed before reconnection", "DR7"),
    ("2.1", "Infrastructure restoration",
     "Restoration is in the recovery environment, using separate recovery administration", "DR4"),
    ("2.2", "Infrastructure restoration",
     "Restored software and configuration match the approved baseline", "DR7"),
    ("3.1", "Configuration and data integrity",
     "The clean recovery point is identified and its integrity checks are recorded", "DR5, DR7"),
    ("3.2", "Configuration and data integrity",
     "Privileged and service credentials are reset or revalidated", "DR7"),
    ("4.1", "Transaction reconciliation",
     "Payments: completed, failed, pending and potentially duplicated items reconciled with counterparties", "DR8"),
    ("4.2", "Transaction reconciliation",
     "Core banking: balances, histories and postings validated", "DR8"),
    ("4.3", "Transaction reconciliation",
     "ATM: cash dispensed, terminal and switch records and account debits reconciled", "DR8"),
    ("5.1", "Unresolved exceptions",
     "Every open exception is recorded with owner, due date and risk treatment", "DR10"),
    ("5.2", "Unresolved exceptions",
     "No open exception exceeds the approved tolerance", "DR9"),
    ("6.1", "Responsible approvals",
     "Technical owner, information security, operations and financial control, and business owner have approved", "DR9"),
)

CHECK_NUMBERS = tuple(c[0] for c in CHECKS)
RECONCILIATION = ("4.1", "4.2", "4.3")
MUST_BE_YES_FOR_CONDITIONAL = ("5.1", "5.2", "6.1")


@dataclass(frozen=True)
class ResumptionCondition:
    text: str
    owner: str
    expiry_date: date | None


@dataclass(frozen=True)
class Decision:
    decision: str
    reasons: tuple[str, ...]


def decide(results: dict[str, str | None], conditions: list[ResumptionCondition],
           exercise_date: date | None = None) -> Decision:
    reasons: list[str] = []

    unanswered = [n for n in CHECK_NUMBERS if results.get(n) not in (YES, NO, NA)]
    if unanswered:
        return Decision(WITHHOLD, (f"Unanswered checks: {', '.join(unanswered)}",))

    bad_na = [n for n in CHECK_NUMBERS if results[n] == NA and n not in RECONCILIATION]
    if bad_na:
        return Decision(WITHHOLD, (
            f"'Not applicable' is accepted only for reconciliation checks; found on {', '.join(bad_na)}",))

    if all(results[n] == NA for n in RECONCILIATION):
        return Decision(WITHHOLD, ("No reconciliation check is in scope; at least one service must be reconciled",))

    nos = [n for n in CHECK_NUMBERS if results[n] == NO]
    if not nos:
        return Decision(RESUME, ("Every applicable check is Yes",))

    outside = [n for n in nos if n not in RECONCILIATION]
    if outside:
        return Decision(WITHHOLD, (f"Checks not met: {', '.join(nos)}",))

    reasons.append(f"Reconciliation not complete on: {', '.join(nos)}")
    if any(results[n] != YES for n in MUST_BE_YES_FOR_CONDITIONAL):
        return Decision(WITHHOLD, tuple(reasons + ["Checks 5.1, 5.2 and 6.1 must all be Yes"]))
    if not conditions:
        return Decision(WITHHOLD, tuple(reasons + ["No condition recorded for conditional resumption"]))
    for c in conditions:
        if not c.text.strip() or not c.owner.strip() or c.expiry_date is None:
            return Decision(WITHHOLD, tuple(reasons + ["Each condition needs a description, an owner and an expiry date"]))
        if exercise_date is not None and c.expiry_date < exercise_date:
            return Decision(WITHHOLD, tuple(reasons + ["A condition has an expiry date before the exercise date"]))
    reasons.append(f"{len(conditions)} condition(s) recorded, each with an owner and an expiry date")
    return Decision(RESUME_CONDITIONALLY, tuple(reasons))
