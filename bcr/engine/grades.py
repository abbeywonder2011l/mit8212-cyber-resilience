"""Effective evidence grades (framework specification, section 3).

The engine never trusts a recorded grade that lacks its supporting record.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from .models import AssessmentInput, Item

GRADE_LABELS = {
    0: "Not implemented or no information",
    1: "Planned or partly implemented",
    2: "Implemented by statement only",
    3: "Implemented, with evidence",
    4: "Demonstrated by test or exercise",
}


@dataclass(frozen=True)
class Effective:
    value: int | None  # None = excluded (not applicable, with justification)
    recorded: int | None
    assessed: bool
    reason: str = ""  # empty when the recorded grade stands


NOT_ASSESSED = Effective(value=0, recorded=None, assessed=False, reason="Not assessed")


def effective_grade(item: Item | None, assessment_date: date, validity_days: int) -> Effective:
    if item is None:
        return NOT_ASSESSED
    if not item.applicable:
        if item.na_justification.strip():
            return Effective(None, item.grade, True, "Not applicable (justified)")
        return Effective(0, item.grade, False, "Marked not applicable without a justification")
    if item.grade is None:
        return NOT_ASSESSED
    grade = item.grade
    if grade not in (0, 1, 2, 3, 4):
        raise ValueError(f"grade must be 0-4, got {grade!r}")
    if grade >= 3 and not item.evidence_reference.strip():
        return Effective(2, grade, True, "No evidence reference: capped at 2")
    if grade == 4:
        if item.evidence_date is None:
            return Effective(3, grade, True, "No test date: capped at 3")
        age = (assessment_date - item.evidence_date).days
        if age < 0:
            return Effective(3, grade, True, "Test date is after the assessment date: capped at 3")
        if age > validity_days:
            return Effective(
                3, grade, True,
                f"Test is {age} days old; validity period is {validity_days} days: capped at 3",
            )
    return Effective(grade, grade, True, "")


def effective_map(inp: AssessmentInput) -> dict[tuple[str | None, str], Effective]:
    """Effective grade for every (service, control) pair the assessment should cover.

    Organisation-level controls use the key (None, control_id).
    """
    recorded = {(i.service_code, i.control_id): i for i in inp.items}
    out: dict[tuple[str | None, str], Effective] = {}
    for control in inp.controls:
        if control.scope == "organisation":
            key = (None, control.id)
            out[key] = effective_grade(recorded.get(key), inp.assessment_date, inp.validity_days)
        else:
            for service in inp.services:
                key = (service.code, control.id)
                out[key] = effective_grade(recorded.get(key), inp.assessment_date, inp.validity_days)
    return out


def lookup(eff: dict, service_code: str, control) -> Effective:
    """Effective grade of a control as it applies to a service."""
    key = (None, control.id) if control.scope == "organisation" else (service_code, control.id)
    return eff[key]
