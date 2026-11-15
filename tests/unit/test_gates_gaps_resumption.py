"""Unit tests: gates, waivers, priorities, the Tool 2 decision table, and
consistency between the code and the control catalogue.
"""
from __future__ import annotations

from dataclasses import replace
from datetime import date, timedelta

import pytest

from bcr.engine import FAIL, NOT_DEMONSTRATED, PASS, PASS_WITH_EXCEPTION, READY, assess
from bcr.engine.gaps import IMPLEMENT, RECORD_EVIDENCE, TEST, action_type_for, risk_factor
from bcr.engine.gates import GATE_CONDITIONS
from bcr.engine.models import ExceptionRecord, Risk, risk_band
from bcr.engine.resumption import (
    CHECK_NUMBERS, RESUME, RESUME_CONDITIONALLY, WITHHOLD, ResumptionCondition, decide,
)
from bcr.profiles import profile_to_input

PAY, CBS, ATM = "SVC-PAY", "SVC-CBS", "SVC-ATM"


@pytest.fixture
def b0(lib, profile):
    return profile_to_input(profile("B0"), lib)


def with_service(inp, code, **changes):
    inp.services = [replace(s, **changes) if s.code == code else s for s in inp.services]
    return inp


def with_item(inp, code, control_id, **changes):
    inp.items = [replace(i, **changes) if (i.service_code, i.control_id) == (code, control_id) else i
                 for i in inp.items]
    return inp


def gate(result, code, g):
    return result.readiness[code].gates[g].result


# --- catalogue consistency ----------------------------------------------

def test_gate_conditions_agree_with_the_catalogue(lib):
    from_code = {cid: g for g, conds in GATE_CONDITIONS.items() for cid, _ in conds}
    from_catalogue = {c.id: c.gate for c in lib.controls if c.gate}
    assert from_code == from_catalogue


def test_gate_minimum_equals_target_grade(lib):
    for conds in GATE_CONDITIONS.values():
        for cid, minimum in conds:
            assert lib.control(cid).target == minimum


def test_catalogue_counts(lib):
    assert len(lib.controls) == 30
    assert len(lib.domains) == 10
    assert sum(c.weight == 2 for c in lib.controls) == 12
    assert sum(c.target == 4 for c in lib.controls) == 6
    assert sum(c.scope == "organisation" for c in lib.controls) == 3


# --- G1, G2 --------------------------------------------------------------

def test_g1_fails_without_a_named_owner(b0):
    result = assess(with_service(b0, CBS, technical_owner="  "))
    assert gate(result, CBS, "G1") == FAIL
    assert result.status(CBS) == NOT_DEMONSTRATED
    action = next(a for a in result.actions if a.service_code == CBS and a.source == "owner")
    assert action.tier == "P1" and action.gate == "G1"


@pytest.mark.parametrize("changes", [
    {"rto_hours": None},
    {"requirements_approved": False},
    {"rto_hours": 9, "mtd_hours": 4},
])
def test_g2_fails_on_missing_unapproved_or_inconsistent_requirements(b0, changes):
    assert gate(assess(with_service(b0, CBS, **changes)), CBS, "G2") == FAIL


def test_g2_fails_when_bcp01_lacks_evidence(b0):
    assert gate(assess(with_item(b0, CBS, "BCP-01", evidence_reference="")), CBS, "G2") == FAIL


# --- G3 and waivers ------------------------------------------------------

def unresolved(inp):
    inp.dependencies = [
        replace(d, single_point_of_failure=True, tested_alternative=False)
        if (d.service_code, d.asset_code) == (PAY, "A04") else d for d in inp.dependencies]
    return inp


def exception_for(inp, **changes):
    base = ExceptionRecord(id=1, service_code=PAY, gate="G3", rule="DR3", dependency_id=f"{PAY}>A04",
                           description="accepted", owner="owner", treatment="risk_acceptance",
                           approved_by="Board Risk Committee",
                           due_date=inp.assessment_date + timedelta(days=30))
    return replace(base, **changes)


def test_g3_single_point_of_failure_without_alternative_fails(b0):
    assert gate(assess(unresolved(b0)), PAY, "G3") == FAIL


def test_g3_third_party_without_tested_coordination_fails(b0):
    b0.dependencies = [replace(d, recovery_coordination_tested=False)
                       if (d.service_code, d.asset_code) == (PAY, "A20") else d for d in b0.dependencies]
    assert gate(assess(b0), PAY, "G3") == FAIL


def test_g3_valid_exception_waives(b0):
    inp = unresolved(b0)
    inp.exceptions = [exception_for(inp)]
    assert gate(assess(inp), PAY, "G3") == PASS_WITH_EXCEPTION


@pytest.mark.parametrize("changes", [
    {"approved_by": ""},
    {"status": "closed", "closure_evidence": "done"},
    {"due_date": None},
    {"service_code": CBS},
    {"dependency_id": f"{PAY}>A05"},
])
def test_g3_invalid_exception_does_not_waive(b0, changes):
    inp = unresolved(b0)
    inp.exceptions = [exception_for(inp, **changes)]
    assert gate(assess(inp), PAY, "G3") == FAIL


def test_exception_due_on_the_assessment_date_still_waives(b0):
    inp = unresolved(b0)
    inp.exceptions = [exception_for(inp, due_date=inp.assessment_date)]
    assert gate(assess(inp), PAY, "G3") == PASS_WITH_EXCEPTION


# --- G4 waiver applies to ACC-03 only ------------------------------------

def control_exception(inp, control_id, compensating="Dual approval per session"):
    return ExceptionRecord(id=2, service_code=PAY, gate="G4", rule="DR4", control_id=control_id,
                           description="x", owner="o", treatment="risk_acceptance",
                           compensating_control=compensating, approved_by="CISO",
                           due_date=inp.assessment_date + timedelta(days=30))


def test_g4_acc03_can_be_waived_with_a_compensating_control(b0):
    inp = with_item(b0, PAY, "ACC-03", grade=1)
    assert gate(assess(inp), PAY, "G4") == FAIL
    inp.exceptions = [control_exception(inp, "ACC-03")]
    result = assess(inp)
    assert gate(result, PAY, "G4") == PASS_WITH_EXCEPTION
    # the gap remains on the action list, but no longer as a failed gate condition
    action = next(a for a in result.actions if (a.service_code, a.ref) == (PAY, "ACC-03"))
    assert action.tier == "P2"


def test_g4_acc03_waiver_needs_a_compensating_control(b0):
    inp = with_item(b0, PAY, "ACC-03", grade=1)
    inp.exceptions = [control_exception(inp, "ACC-03", compensating="  ")]
    assert gate(assess(inp), PAY, "G4") == FAIL


def test_g4_acc02_cannot_be_waived(b0):
    inp = with_item(b0, PAY, "ACC-02", grade=1)
    inp.exceptions = [control_exception(inp, "ACC-02")]
    assert gate(assess(inp), PAY, "G4") == FAIL


def test_justified_not_applicable_satisfies_a_gate_condition(b0):
    inp = with_item(b0, PAY, "ACC-04", applicable=False, na_justification="No vendor has access.")
    assert gate(assess(inp), PAY, "G4") == PASS


def test_unassessed_gating_control_fails_the_gate(b0):
    assert gate(assess(with_item(b0, PAY, "BKP-01", grade=None)), PAY, "G5") == FAIL


def test_gating_control_missing_from_the_catalogue_fails_the_gate(b0):
    b0.controls = tuple(c for c in b0.controls if c.id != "BKP-01")
    result = assess(b0)
    assert gate(result, CBS, "G5") == FAIL


# --- G5, G6 need a demonstrated test -------------------------------------

def test_g5_needs_grade_4_on_restoration_test(b0):
    assert gate(assess(with_item(b0, CBS, "BKP-02", grade=3)), CBS, "G5") == FAIL


def test_g6_needs_grade_4_on_restoration_exercise(b0):
    assert gate(assess(with_item(b0, CBS, "BCP-03", grade=3)), CBS, "G6") == FAIL


# --- G7 propagation ------------------------------------------------------

def test_g7_propagates_downstream_and_transitively(b0):
    # CBS fails its own gate; PAY depends on CBS, ATM depends on PAY and CBS
    result = assess(with_item(b0, CBS, "BKP-01", grade=1))
    assert gate(result, PAY, "G7") == FAIL and gate(result, ATM, "G7") == FAIL


def test_g7_does_not_propagate_upstream(b0):
    # ATM fails its own gate; nothing depends on ATM
    result = assess(with_item(b0, ATM, "BKP-01", grade=1))
    assert result.status(ATM) == NOT_DEMONSTRATED
    assert gate(result, CBS, "G7") == PASS and gate(result, PAY, "G7") == PASS


def test_g7_survives_a_circular_dependency(b0):
    inp = with_service(b0, CBS, depends_on=(PAY,))  # CBS <-> PAY cycle
    result = assess(inp)
    assert {c: result.status(c) for c in (CBS, PAY, ATM)} == {CBS: READY, PAY: READY, ATM: READY}


# --- priorities ----------------------------------------------------------

def test_action_type_by_effective_grade():
    assert action_type_for(0, 3) == IMPLEMENT and action_type_for(1, 4) == IMPLEMENT
    assert action_type_for(2, 3) == RECORD_EVIDENCE
    assert action_type_for(3, 4) == TEST


def test_risk_factor_uses_highest_rating_and_worst_case_when_missing(b0):
    b0.risks = [Risk(PAY, "a", 2, 5), Risk(PAY, "b", 4, 5)]
    factor, _ = risk_factor(b0, PAY)
    assert factor == pytest.approx(1 + 20 / 25)
    factor, note = risk_factor(b0, CBS)
    assert factor == 2.0 and "worst case" in note


def test_risk_bands():
    assert [risk_band(x) for x in (1, 4, 5, 9, 10, 14, 15, 25)] == [
        "Low", "Low", "Medium", "Medium", "High", "High", "Critical", "Critical"]


def test_priority_formula_and_ordering(b0):
    """NET-01 for PAY at grade 1: gap 2, weight 1, criticality 5, factor 1 + 12/25 = 1.48 -> 14.8 (P2).
    MON-01 for ATM at grade 2: gap 1, weight 1, criticality 4, factor 1 + 9/25 = 1.36 -> 5.44 (P3).
    """
    inp = with_item(with_item(b0, PAY, "NET-01", grade=1), ATM, "MON-01", grade=2)
    actions = assess(inp).actions
    assert [(a.service_code, a.ref, a.tier) for a in actions] == [(PAY, "NET-01", "P2"), (ATM, "MON-01", "P3")]
    assert actions[0].priority == pytest.approx(14.8)
    assert actions[1].priority == pytest.approx(5.44)


def test_organisation_level_gap_is_listed_once(b0):
    inp = with_item(b0, None, "GOV-02", grade=1)
    gov = [a for a in assess(inp).actions if a.ref == "GOV-02"]
    assert len(gov) == 1 and gov[0].service_code == "ORG"


# --- Tool 2 decision table ----------------------------------------------

EXERCISE_DATE = date(2026, 11, 1)


def answers():
    return {n: "yes" for n in CHECK_NUMBERS}


COND_NO_EXPIRY = [ResumptionCondition("Manual review of pending items", "Head of Payments", None)]


def cond(days=7):
    return [ResumptionCondition("Manual review of pending items", "Head of Payments",
                                EXERCISE_DATE + timedelta(days=days))]


def test_all_yes_resumes():
    assert decide(answers(), []).decision == RESUME


def test_reconciliation_out_of_scope_may_be_not_applicable():
    assert decide({**answers(), "4.1": "na", "4.3": "na"}, []).decision == RESUME


def test_unanswered_check_withholds():
    assert decide({**answers(), "2.2": None}, []).decision == WITHHOLD


def test_not_applicable_outside_reconciliation_withholds():
    assert decide({**answers(), "1.2": "na"}, []).decision == WITHHOLD


def test_all_reconciliation_not_applicable_withholds():
    assert decide({**answers(), "4.1": "na", "4.2": "na", "4.3": "na"}, []).decision == WITHHOLD


@pytest.mark.parametrize("check", ["1.1", "1.2", "2.1", "2.2", "3.1", "3.2", "5.1", "5.2", "6.1"])
def test_any_no_outside_reconciliation_withholds(check):
    assert decide({**answers(), check: "no"}, cond()).decision == WITHHOLD


@pytest.mark.parametrize("check", ["4.1", "4.2", "4.3"])
def test_reconciliation_no_with_conditions_resumes_conditionally(check):
    assert decide({**answers(), check: "no"}, cond()).decision == RESUME_CONDITIONALLY


def test_reconciliation_no_without_conditions_withholds():
    assert decide({**answers(), "4.1": "no"}, []).decision == WITHHOLD


def test_condition_without_owner_or_expiry_withholds():
    assert decide({**answers(), "4.1": "no"}, COND_NO_EXPIRY).decision == WITHHOLD
    no_owner = [ResumptionCondition("x", " ", cond()[0].expiry_date)]
    assert decide({**answers(), "4.1": "no"}, no_owner).decision == WITHHOLD


def test_condition_expiring_before_the_exercise_withholds():
    assert decide({**answers(), "4.1": "no"}, cond(days=-1), EXERCISE_DATE).decision == WITHHOLD


def test_technical_restoration_alone_never_resumes():
    """All technical checks Yes, reconciliation and approvals not done."""
    results = {**answers(), "4.1": "no", "4.2": "no", "4.3": "no", "6.1": "no"}
    assert decide(results, cond()).decision == WITHHOLD
