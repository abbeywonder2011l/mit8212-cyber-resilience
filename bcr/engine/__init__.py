"""Logic layer: one entry point, `assess`, that turns inputs into results.

Pure functions only: the same input always gives the same output.
"""
from __future__ import annotations

from dataclasses import dataclass

from .gaps import Action, build_actions
from .gates import (
    FAIL, GATES, NOT_DEMONSTRATED, PASS, PASS_WITH_EXCEPTION, READY, READY_WITH_EXCEPTIONS,
    Readiness, evaluate_gates, exception_is_overdue, exception_is_valid,
)
from .grades import Effective, effective_map, lookup
from .models import ORG, AssessmentInput, Dependency, ExceptionRecord, Item, Risk, Service
from .scoring import SCHEMES, Scores, compute_scores, pct


@dataclass
class AssessmentResult:
    scheme: str
    effective: dict
    scores: Scores
    readiness: dict  # service code -> Readiness
    actions: list  # list[Action], already ordered

    def status(self, service_code: str) -> str:
        return self.readiness[service_code].status


def assess(inp: AssessmentInput, scheme: str = "A") -> AssessmentResult:
    eff = effective_map(inp)
    scores = compute_scores(inp, eff, SCHEMES[scheme])
    readiness = evaluate_gates(inp, eff)
    actions = build_actions(inp, eff, readiness)
    return AssessmentResult(scheme, eff, scores, readiness, actions)


def sensitivity(inp: AssessmentInput) -> dict:
    """Scores and service ranking under each weighting scheme.

    Readiness status is included to show that it does not depend on weights.
    """
    out = {}
    for key, scheme in SCHEMES.items():
        result = assess(inp, key)
        ranked = sorted(
            inp.services,
            key=lambda s: (-(result.scores.services[s.code].score or 0), s.code),
        )
        out[key] = {
            "name": scheme.name,
            "overall": result.scores.overall,
            "services": {s.code: result.scores.services[s.code].score for s in inp.services},
            "ranking": [s.code for s in ranked],
            "status": {s.code: result.status(s.code) for s in inp.services},
        }
    return out


__all__ = [
    "Action", "AssessmentInput", "AssessmentResult", "Dependency", "Effective", "ExceptionRecord",
    "FAIL", "GATES", "Item", "NOT_DEMONSTRATED", "ORG", "PASS", "PASS_WITH_EXCEPTION", "READY",
    "READY_WITH_EXCEPTIONS", "Readiness", "Risk", "SCHEMES", "Scores", "Service", "assess",
    "effective_map", "exception_is_overdue", "exception_is_valid", "lookup", "pct", "sensitivity",
]
