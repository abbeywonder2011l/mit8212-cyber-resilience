"""Readiness gates G1-G7 and service status (framework specification, section 5).

A gate is pass/fail. A high score cannot compensate for a failed gate, and
gate results do not depend on any weighting scheme.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from .grades import lookup
from .models import AssessmentInput, ExceptionRecord

PASS = "PASS"
PASS_WITH_EXCEPTION = "PASS_WITH_EXCEPTION"
FAIL = "FAIL"

READY = "Ready"
READY_WITH_EXCEPTIONS = "Ready with accepted exceptions"
NOT_DEMONSTRATED = "Not demonstrated"

GATES = ("G1", "G2", "G3", "G4", "G5", "G6", "G7")

GATE_RULES = {
    "G1": ("DR1", "Named business and technical owners"),
    "G2": ("DR2", "Approved recovery requirements"),
    "G3": ("DR3", "No unresolved dependency"),
    "G4": ("DR4", "Privileged access and separation of recovery administration"),
    "G5": ("DR5", "Protected and verified backups"),
    "G6": ("DR6", "Recovery readiness demonstrated"),
    "G7": ("Finding Two", "Services depended on are ready"),
}

# (control id, minimum effective grade). Must agree with the 'gate' field of the catalogue.
GATE_CONDITIONS: dict[str, tuple[tuple[str, int], ...]] = {
    "G2": (("BCP-01", 3),),
    "G4": (("ACC-02", 3), ("ACC-03", 3), ("ACC-04", 3)),
    "G5": (("BKP-01", 3), ("BKP-02", 4), ("BKP-03", 3)),
    "G6": (("BCP-02", 3), ("BCP-03", 4), ("INC-02", 3)),
}

WAIVABLE_CONTROLS = {"ACC-03"}  # DR4(b): exception with a compensating control


@dataclass(frozen=True)
class Condition:
    gate: str
    kind: str  # owner | requirements | dependency | control | upstream
    ref: str
    met: bool
    waived: bool = False
    detail: str = ""

    @property
    def ok(self) -> bool:
        return self.met or self.waived


@dataclass
class GateResult:
    gate: str
    conditions: list[Condition] = field(default_factory=list)

    @property
    def result(self) -> str:
        if all(c.met for c in self.conditions):
            return PASS
        if all(c.ok for c in self.conditions):
            return PASS_WITH_EXCEPTION
        return FAIL

    @property
    def failed(self) -> list[Condition]:
        return [c for c in self.conditions if not c.ok]


@dataclass
class Readiness:
    service_code: str
    gates: dict  # gate -> GateResult
    status: str = NOT_DEMONSTRATED

    def failed_gates(self) -> list[str]:
        return [g for g, r in self.gates.items() if r.result == FAIL]


def exception_is_overdue(exc: ExceptionRecord, assessment_date) -> bool:
    return exc.status == "open" and exc.due_date is not None and exc.due_date < assessment_date


def exception_is_valid(exc: ExceptionRecord, assessment_date) -> bool:
    """Approved, still open, and not past its due date."""
    return (
        exc.status == "open"
        and bool(exc.approved_by.strip())
        and exc.due_date is not None
        and exc.due_date >= assessment_date
    )


def _waiver_for_dependency(inp: AssessmentInput, service_code: str, dep_id) -> bool:
    return any(
        e.service_code == service_code and e.dependency_id == dep_id
        and exception_is_valid(e, inp.assessment_date)
        for e in inp.exceptions
    )


def _waiver_for_control(inp: AssessmentInput, service_code: str, control_id: str) -> bool:
    if control_id not in WAIVABLE_CONTROLS:
        return False
    return any(
        e.service_code == service_code and e.control_id == control_id
        and e.compensating_control.strip() and exception_is_valid(e, inp.assessment_date)
        for e in inp.exceptions
    )


def _control_conditions(inp, eff, service_code: str, gate: str) -> list[Condition]:
    by_id = {c.id: c for c in inp.controls}
    out = []
    for control_id, minimum in GATE_CONDITIONS[gate]:
        control = by_id.get(control_id)
        if control is None:  # a gate condition cannot be met by a control that is not assessed
            out.append(Condition(gate, "control", control_id, False,
                                 detail="control is not in the catalogue in use"))
            continue
        e = lookup(eff, service_code, control)
        if e.value is None:  # not applicable, justified
            out.append(Condition(gate, "control", control_id, True, detail="Not applicable (justified)"))
            continue
        met = e.value >= minimum
        waived = (not met) and _waiver_for_control(inp, service_code, control_id)
        detail = f"effective grade {e.value}, needs {minimum}"
        if e.reason:
            detail += f" ({e.reason})"
        if waived:
            detail += "; waived by an approved exception with a compensating control"
        out.append(Condition(gate, "control", control_id, met, waived, detail))
    return out


def _own_gates(inp: AssessmentInput, eff: dict, service) -> dict[str, GateResult]:
    gates: dict[str, GateResult] = {}

    g1 = GateResult("G1")
    g1.conditions.append(Condition("G1", "owner", "business_owner", bool(service.business_owner.strip()),
                                   detail="named business owner"))
    g1.conditions.append(Condition("G1", "owner", "technical_owner", bool(service.technical_owner.strip()),
                                   detail="named technical owner"))
    gates["G1"] = g1

    g2 = GateResult("G2")
    recorded = None not in (service.mtd_hours, service.rto_hours, service.rpo_minutes)
    g2.conditions.append(Condition("G2", "requirements", "recorded", recorded,
                                   detail="maximum tolerable downtime, RTO and RPO recorded"))
    g2.conditions.append(Condition("G2", "requirements", "approved", bool(service.requirements_approved),
                                   detail="recovery requirements approved"))
    consistent = recorded and service.rto_hours <= service.mtd_hours
    g2.conditions.append(Condition("G2", "requirements", "rto_within_mtd", bool(consistent),
                                   detail="RTO does not exceed the maximum tolerable downtime"))
    g2.conditions.extend(_control_conditions(inp, eff, service.code, "G2"))
    gates["G2"] = g2

    g3 = GateResult("G3")
    for dep in inp.dependencies:
        if dep.service_code != service.code:
            continue
        reasons = dep.unresolved_reasons
        if not reasons:
            continue
        waived = _waiver_for_dependency(inp, service.code, dep.id)
        detail = f"{dep.asset_name}: " + "; ".join(reasons)
        if waived:
            detail += "; covered by an approved exception"
        g3.conditions.append(Condition("G3", "dependency", dep.asset_code, False, waived, detail))
    gates["G3"] = g3

    for gate in ("G4", "G5", "G6"):
        gates[gate] = GateResult(gate, _control_conditions(inp, eff, service.code, gate))
    return gates


def _upstream(inp: AssessmentInput, code: str) -> list[str]:
    """All services that `code` depends on, directly or indirectly (cycle-safe)."""
    known = {s.code: s for s in inp.services}
    seen: list[str] = []
    stack = list(known[code].depends_on)
    while stack:
        nxt = stack.pop(0)
        if nxt == code or nxt in seen or nxt not in known:
            continue
        seen.append(nxt)
        stack.extend(known[nxt].depends_on)
    return seen


def evaluate_gates(inp: AssessmentInput, eff: dict) -> dict[str, Readiness]:
    own = {s.code: _own_gates(inp, eff, s) for s in inp.services}
    own_fail = {code: any(r.result == FAIL for r in gates.values()) for code, gates in own.items()}
    out: dict[str, Readiness] = {}
    for service in inp.services:
        gates = dict(own[service.code])
        g7 = GateResult("G7")
        for up in _upstream(inp, service.code):
            if own_fail[up]:
                g7.conditions.append(Condition(
                    "G7", "upstream", up, False,
                    detail=f"depends on {up}, which is not demonstrated on its own gates"))
        gates["G7"] = g7
        results = [gates[g].result for g in GATES]
        if FAIL in results:
            status = NOT_DEMONSTRATED
        elif PASS_WITH_EXCEPTION in results:
            status = READY_WITH_EXCEPTIONS
        else:
            status = READY
        out[service.code] = Readiness(service.code, gates, status)
    return out
