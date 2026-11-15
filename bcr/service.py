"""Glue between the database and the logic layer, used by the interface.

Keeps the interface free of business rules: pages call these functions and
display what they return.
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from bcr.data import repository as repo
from bcr.engine import AssessmentInput, AssessmentResult, assess
from bcr.library import Library
from bcr.reporting import ReportData


def run_assessment(s: Session, assessment_id: int, lib: Library,
                   scheme: str = "A") -> tuple[AssessmentInput, AssessmentResult]:
    inp = repo.load_assessment_input(s, assessment_id, lib)
    return inp, assess(inp, scheme)


def exercise_views(s: Session, assessment_id: int) -> list[dict]:
    """Tool 2 records with their computed decision, ready to display or report."""
    out = []
    for x in repo.list_exercises(s, assessment_id):
        decision = repo.exercise_decision(x)
        out.append({
            "id": x.id, "service": x.service.code, "date": x.exercise_date.isoformat(),
            "kind": x.kind, "scenario": x.scenario,
            "results": {c.check_no: c.result for c in x.checks},
            "evidence": {c.check_no: c.evidence_reference for c in x.checks},
            "conditions": [{"text": c.text, "owner": c.owner,
                            "expiry_date": c.expiry_date.isoformat() if c.expiry_date else ""}
                           for c in x.conditions],
            "decision": decision.decision, "reasons": decision.reasons,
        })
    return out


def build_report_data(s: Session, assessment_id: int, lib: Library, scheme: str = "A") -> ReportData:
    from bcr.data import models as m
    assessment = s.get(m.Assessment, assessment_id)
    org = repo.get_organisation(s)
    inp, result = run_assessment(s, assessment_id, lib, scheme)
    return ReportData(
        organisation=org.name if org else "Organisation not named",
        notice=org.notice if org else "",
        assessment_name=assessment.name, assessor=assessment.assessor,
        library_version=assessment.library_version, inp=inp, result=result, lib=lib,
        exercises=exercise_views(s, assessment_id),
    )
