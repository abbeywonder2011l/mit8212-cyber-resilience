"""Plain data structures used by the logic layer.

Nothing here imports the database or the interface, so the engine can be
tested alone and reused behind a different front end or data store.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Hashable

from bcr.library import Control

ORG = "ORG"  # label used for organisation-level items in outputs


@dataclass(frozen=True)
class Service:
    code: str
    name: str
    criticality: int
    business_owner: str = ""
    technical_owner: str = ""
    mtd_hours: float | None = None
    rto_hours: float | None = None
    rpo_minutes: float | None = None
    requirements_approved: bool = False
    depends_on: tuple[str, ...] = ()


@dataclass(frozen=True)
class Dependency:
    id: Hashable
    service_code: str
    asset_code: str
    asset_name: str
    is_third_party: bool = False
    single_point_of_failure: bool = False
    tested_alternative: bool = True
    recovery_coordination_tested: bool = True

    @property
    def unresolved_reasons(self) -> list[str]:
        reasons = []
        if self.single_point_of_failure and not self.tested_alternative:
            reasons.append("single point of failure with no tested alternative")
        if self.is_third_party and not self.recovery_coordination_tested:
            reasons.append("third party with no tested recovery coordination")
        return reasons


@dataclass(frozen=True)
class Risk:
    service_code: str
    title: str
    likelihood: int
    impact: int
    category: str = ""
    affects_recovery_environment: bool = False

    @property
    def rating(self) -> int:
        return self.likelihood * self.impact

    @property
    def band(self) -> str:
        return risk_band(self.rating)


def risk_band(rating: int) -> str:
    if rating >= 15:
        return "Critical"
    if rating >= 10:
        return "High"
    if rating >= 5:
        return "Medium"
    return "Low"


@dataclass(frozen=True)
class Item:
    """One assessed control for one service (service_code None = organisation level)."""

    service_code: str | None
    control_id: str
    applicable: bool = True
    na_justification: str = ""
    grade: int | None = None
    evidence_reference: str = ""
    evidence_date: date | None = None
    evidence_description: str = ""


@dataclass(frozen=True)
class ExceptionRecord:
    id: Hashable
    service_code: str
    gate: str = ""
    rule: str = ""
    dependency_id: Hashable | None = None
    control_id: str | None = None
    description: str = ""
    owner: str = ""
    treatment: str = ""  # "remediation" or "risk_acceptance"
    compensating_control: str = ""
    approved_by: str = ""
    due_date: date | None = None
    status: str = "open"  # "open" or "closed"
    closure_evidence: str = ""


@dataclass
class AssessmentInput:
    assessment_date: date
    controls: tuple[Control, ...]
    services: list[Service]
    validity_days: int = 365
    dependencies: list[Dependency] = field(default_factory=list)
    risks: list[Risk] = field(default_factory=list)
    items: list[Item] = field(default_factory=list)
    exceptions: list[ExceptionRecord] = field(default_factory=list)

    def service(self, code: str) -> Service:
        for s in self.services:
            if s.code == code:
                return s
        raise KeyError(code)
