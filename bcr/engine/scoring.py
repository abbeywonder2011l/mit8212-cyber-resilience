"""Scores, coverage and grade distribution (framework specification, section 4).

The score is a researcher-developed measure. It is not a NIST CSF Tier and
not the CBN self-assessment maturity level.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field

from .grades import Effective, lookup
from .models import AssessmentInput


@dataclass(frozen=True)
class Scheme:
    key: str
    name: str
    use_control_weights: bool
    domain_weights: dict
    use_criticality: bool

    def control_weight(self, control) -> int:
        return control.weight if self.use_control_weights else 1

    def domain_weight(self, domain: str) -> int:
        return self.domain_weights.get(domain, 1)

    def service_weight(self, service) -> int:
        return service.criticality if self.use_criticality else 1


SCHEMES: dict[str, Scheme] = {
    "A": Scheme("A", "Baseline", True, {}, True),
    "B": Scheme("B", "Equal weights", False, {}, False),
    "C": Scheme("C", "Recovery emphasis", True, {"BKP": 2, "BCP": 2, "RED": 2, "INC": 2}, True),
}


@dataclass
class Profile:
    """Coverage figures shown beside every score."""

    applicable: int = 0
    assessed: int = 0
    demonstrated: int = 0
    distribution: dict = field(default_factory=lambda: {g: 0 for g in range(5)})

    @property
    def coverage(self) -> float | None:
        return self.assessed / self.applicable if self.applicable else None

    @property
    def demonstrated_share(self) -> float | None:
        return self.demonstrated / self.applicable if self.applicable else None


@dataclass
class ServiceScore:
    service_code: str
    domain_scores: dict  # domain -> float | None
    score: float | None
    profile: Profile


@dataclass
class Scores:
    scheme: str
    services: dict  # code -> ServiceScore
    overall: float | None
    profile: Profile


def _profile(values: list[Effective]) -> Profile:
    p = Profile()
    counts = Counter()
    for e in values:
        if e.value is None:
            continue
        p.applicable += 1
        if e.assessed:
            p.assessed += 1
        if e.value == 4:
            p.demonstrated += 1
        counts[e.value] += 1
    p.distribution = {g: counts.get(g, 0) for g in range(5)}
    return p


def compute_scores(inp: AssessmentInput, eff: dict, scheme: Scheme) -> Scores:
    domains = list(dict.fromkeys(c.domain for c in inp.controls))
    services: dict[str, ServiceScore] = {}
    for service in inp.services:
        domain_scores: dict[str, float | None] = {}
        for domain in domains:
            num = 0.0
            den = 0.0
            for control in inp.controls:
                if control.domain != domain:
                    continue
                e = lookup(eff, service.code, control)
                if e.value is None:
                    continue
                w = scheme.control_weight(control)
                num += w * e.value / 4
                den += w
            domain_scores[domain] = (num / den) if den else None
        num = sum(scheme.domain_weight(d) * s for d, s in domain_scores.items() if s is not None)
        den = sum(scheme.domain_weight(d) for d, s in domain_scores.items() if s is not None)
        values = [lookup(eff, service.code, c) for c in inp.controls]
        services[service.code] = ServiceScore(
            service_code=service.code,
            domain_scores=domain_scores,
            score=(num / den) if den else None,
            profile=_profile(values),
        )
    num = sum(scheme.service_weight(s) * services[s.code].score
              for s in inp.services if services[s.code].score is not None)
    den = sum(scheme.service_weight(s) for s in inp.services if services[s.code].score is not None)
    return Scores(
        scheme=scheme.key,
        services=services,
        overall=(num / den) if den else None,
        profile=_profile(list(eff.values())),
    )


def pct(value: float | None) -> str:
    """Format a 0-1 score as a percentage with one decimal place."""
    return "n/a" if value is None else f"{value * 100:.1f}%"
