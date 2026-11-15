"""Gap analysis and remediation priorities (framework specification, section 7)."""
from __future__ import annotations

from dataclasses import dataclass

from .gates import FAIL, GATE_CONDITIONS, GATE_RULES, Readiness
from .grades import lookup
from .models import ORG, AssessmentInput

IMPLEMENT = "Implement"
RECORD_EVIDENCE = "Record evidence"
TEST = "Test and record the result"
RESOLVE = "Resolve"

# Non-control actions (owners, requirements, dependencies, upstream services) have no
# grade gap. They are given the largest gap and weight so they sort first within P1.
REGISTER_GAP = 4
REGISTER_WEIGHT = 2


@dataclass(frozen=True)
class Action:
    service_code: str  # ORG for organisation-level controls
    source: str  # control | owner | requirements | dependency | upstream
    ref: str
    title: str
    action_type: str
    current: int | None
    target: int | None
    gap: int
    gate: str
    rules: str
    tier: str
    priority: float
    detail: str
    expected_evidence: str
    basis: str
    risk_note: str

    @property
    def sort_key(self):
        return (self.tier, -self.priority, self.service_code, self.ref)


def risk_factor(inp: AssessmentInput, service_code: str) -> tuple[float, str]:
    """1 + highest rating / 25; 2.0 (worst case) when no risk is recorded."""
    ratings = [r.rating for r in inp.risks if r.service_code == service_code]
    if not ratings:
        return 2.0, "No risk recorded for this service: worst case assumed"
    top = max(ratings)
    return 1 + top / 25, f"Highest recorded risk rating {top}"


def _org_factor(inp: AssessmentInput) -> tuple[int, float, str]:
    criticality = max((s.criticality for s in inp.services), default=1)
    factors = [risk_factor(inp, s.code)[0] for s in inp.services]
    return criticality, (max(factors) if factors else 2.0), "Highest factor across services"


def action_type_for(effective: int, target: int) -> str:
    if effective <= 1:
        return IMPLEMENT
    if effective == 2:
        return RECORD_EVIDENCE
    return TEST


def build_actions(inp: AssessmentInput, eff: dict, readiness: dict[str, Readiness]) -> list[Action]:
    actions: list[Action] = []
    minimum_for = {cid: (gate, minimum) for gate, conds in GATE_CONDITIONS.items() for cid, minimum in conds}

    def failing_gate_condition(service_code: str, control_id: str) -> bool:
        """True if this control is a failed (not waived) condition of a failed gate."""
        if control_id not in minimum_for:
            return False
        gate = minimum_for[control_id][0]
        result = readiness[service_code].gates[gate]
        return any(c.kind == "control" and c.ref == control_id and not c.ok for c in result.conditions)

    # Control gaps
    seen_org: set[str] = set()
    for service in inp.services:
        factor, note = risk_factor(inp, service.code)
        for control in inp.controls:
            e = lookup(eff, service.code, control)
            if e.value is None or e.value >= control.target:
                continue
            if control.scope == "organisation":
                if control.id in seen_org:
                    continue
                seen_org.add(control.id)
                code = ORG
                criticality, f, n = _org_factor(inp)
                p1 = False
            else:
                code = service.code
                criticality, f, n = service.criticality, factor, note
                p1 = failing_gate_condition(service.code, control.id)
            gap = control.target - e.value
            tier = "P1" if p1 else ("P2" if control.weight == 2 or gap >= 2 else "P3")
            detail = control.remediation
            if not e.assessed:
                detail += " (This control has not been assessed.)"
            elif e.reason:
                detail += f" ({e.reason}.)"
            actions.append(Action(
                service_code=code, source="control", ref=control.id, title=control.title,
                action_type=action_type_for(e.value, control.target),
                current=e.value, target=control.target, gap=gap,
                gate=control.gate or "", rules=", ".join(control.rules),
                tier=tier, priority=round(gap * control.weight * criticality * f, 4),
                detail=detail, expected_evidence="; ".join(control.evidence),
                basis=control.basis, risk_note=n,
            ))

    # Register, dependency and upstream conditions of failed gates
    for service in inp.services:
        factor, note = risk_factor(inp, service.code)
        priority = round(REGISTER_GAP * REGISTER_WEIGHT * service.criticality * factor, 4)
        for gate, result in readiness[service.code].gates.items():
            if result.result != FAIL:
                continue
            for cond in result.failed:
                if cond.kind == "control":
                    continue
                titles = {
                    "owner": "Name the service owner",
                    "requirements": "Record and approve the recovery requirements",
                    "dependency": "Resolve the dependency",
                    "upstream": "Service depended on is not ready",
                }
                evidence = {
                    "owner": "Critical services register entry with named owners",
                    "requirements": "Business impact analysis and written approval",
                    "dependency": "Tested alternative, joint recovery test, or an approved exception",
                    "upstream": "Readiness of the service depended on",
                }
                actions.append(Action(
                    service_code=service.code, source=cond.kind, ref=cond.ref,
                    title=titles[cond.kind], action_type=RESOLVE,
                    current=None, target=None, gap=REGISTER_GAP,
                    gate=gate, rules=GATE_RULES[gate][0], tier="P1", priority=priority,
                    detail=cond.detail, expected_evidence=evidence[cond.kind],
                    basis="", risk_note=note,
                ))

    actions.sort(key=lambda a: a.sort_key)
    return actions
