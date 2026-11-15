"""Scenario tests: B0 and SC1-SC5 against the expected results written in
docs/04-synthetic-environment-and-scenarios.md before the software existed.
"""
from __future__ import annotations

import pytest

from bcr.engine import (
    FAIL, NOT_DEMONSTRATED, PASS, PASS_WITH_EXCEPTION, READY, READY_WITH_EXCEPTIONS,
    exception_is_overdue,
)
from bcr.engine.resumption import RESUME, RESUME_CONDITIONALLY, WITHHOLD, decide
from bcr.profiles import exercise_conditions

CBS, PAY, ATM = "SVC-CBS", "SVC-PAY", "SVC-ATM"


def statuses(result):
    return {code: r.status for code, r in result.readiness.items()}


def gate(result, service, gate_id):
    return result.readiness[service].gates[gate_id].result


def actions_for(result, service):
    return [a for a in result.actions if a.service_code == service]


def find_action(result, service, ref):
    matches = [a for a in result.actions if a.service_code == service and a.ref == ref]
    assert len(matches) == 1, f"expected one action for {service}/{ref}, found {len(matches)}"
    return matches[0]


def decision_for(profile_data, index=0):
    x = profile_data["exercises"][index]
    return decide(x["results"], exercise_conditions(x), x["exercise_date"]).decision


# --- B0 -----------------------------------------------------------------

def test_b0_all_ready_and_no_actions(run):
    _, result = run("B0")
    assert statuses(result) == {CBS: READY, PAY: READY, ATM: READY}
    for code in (CBS, PAY, ATM):
        assert all(r.result == PASS for r in result.readiness[code].gates.values())
    assert result.actions == []


def test_b0_scores_match_hand_calculation(run):
    """Hand calculation (specification section 4):
    domain scores at target are GOV .75, AST .75, ACC .75, NET .875, RED .8333,
    BKP .8333, MON .75, INC .80, BCP .8125, TPR .8333; mean = 0.79875.
    """
    _, a = run("B0", "A")
    _, b = run("B0", "B")
    _, c = run("B0", "C")
    for code in (CBS, PAY, ATM):
        assert a.scores.services[code].score == pytest.approx(0.79875)
        assert b.scores.services[code].score == pytest.approx(0.8020833, abs=1e-6)
        assert c.scores.services[code].score == pytest.approx(0.8047619, abs=1e-6)
    assert a.scores.overall == pytest.approx(0.79875)
    assert a.scores.services[CBS].domain_scores["INC"] == pytest.approx(0.8)
    assert a.scores.services[CBS].domain_scores["BCP"] == pytest.approx(0.8125)


def test_b0_coverage_and_demonstrated_share(run):
    _, result = run("B0")
    p = result.scores.services[CBS].profile
    assert p.applicable == 30 and p.assessed == 30
    assert p.coverage == 1.0
    assert p.demonstrated == 6
    assert p.demonstrated_share == pytest.approx(0.2)
    # 3 organisation-level + 27 x 3 service-level items
    assert result.scores.profile.applicable == 84


# --- SC1 ----------------------------------------------------------------

def test_sc1_ready_with_one_ordinary_gap(run, profile):
    _, result = run("SC1")
    assert statuses(result) == {CBS: READY, PAY: READY, ATM: READY}
    assert len(result.actions) == 1
    a = result.actions[0]
    assert (a.service_code, a.ref, a.action_type, a.tier) == (CBS, "MON-02", "Record evidence", "P3")
    assert decision_for(profile("SC1")) == RESUME


# --- SC2 ----------------------------------------------------------------

def test_sc2_step1_unresolved_dependency_propagates(run):
    _, result = run("SC2a")
    assert gate(result, PAY, "G3") == FAIL
    assert gate(result, ATM, "G7") == FAIL
    assert statuses(result) == {CBS: READY, PAY: NOT_DEMONSTRATED, ATM: NOT_DEMONSTRATED}
    dep = find_action(result, PAY, "A20")
    assert dep.tier == "P1" and dep.source == "dependency"
    tpr = find_action(result, PAY, "TPR-03")
    assert tpr.tier == "P2" and tpr.gap == 3


def test_sc2_step2_approved_exception_waives_the_gate(run):
    inp, result = run("SC2b")
    assert gate(result, PAY, "G3") == PASS_WITH_EXCEPTION
    assert statuses(result) == {CBS: READY, PAY: READY_WITH_EXCEPTIONS, ATM: READY}
    assert len(inp.exceptions) == 1


def test_sc2_step3_overdue_exception_no_longer_waives(run):
    inp, result = run("SC2c")
    assert exception_is_overdue(inp.exceptions[0], inp.assessment_date)
    assert gate(result, PAY, "G3") == FAIL
    assert statuses(result) == {CBS: READY, PAY: NOT_DEMONSTRATED, ATM: NOT_DEMONSTRATED}


# --- SC3 ----------------------------------------------------------------

def test_sc3_shared_credentials_and_no_exercise(run):
    _, result = run("SC3")
    assert result.effective[(PAY, "ACC-04")].value == 2  # evidence rule
    assert gate(result, PAY, "G4") == FAIL
    assert gate(result, PAY, "G6") == FAIL
    assert gate(result, ATM, "G7") == FAIL
    assert statuses(result) == {CBS: READY, PAY: NOT_DEMONSTRATED, ATM: NOT_DEMONSTRATED}
    for ref in ("ACC-03", "ACC-04", "BCP-03"):
        assert find_action(result, PAY, ref).tier == "P1"


def test_sc3_resumption_decisions(profile):
    data = profile("SC3")
    assert decision_for(data, 0) == RESUME_CONDITIONALLY
    assert decision_for(data, 1) == WITHHOLD  # same record with no conditions


# --- SC4 ----------------------------------------------------------------

def test_sc4_good_score_but_failed_gate(run):
    _, base = run("B0")
    _, result = run("SC4")
    assert result.effective[(CBS, "ACC-03")].value == 2
    assert gate(result, CBS, "G4") == FAIL
    assert statuses(result) == {CBS: NOT_DEMONSTRATED, PAY: NOT_DEMONSTRATED, ATM: NOT_DEMONSTRATED}
    assert gate(result, PAY, "G7") == FAIL and gate(result, ATM, "G7") == FAIL
    # Hand calculation: ACC 4.75/7 = .678571, RED 2.0/3 = .666667 -> service 0.7749405
    score = result.scores.services[CBS].score
    assert score == pytest.approx(0.7749405, abs=1e-6)
    assert base.scores.services[CBS].score - score < 0.03  # falls by under 3 points
    # redundancy that was tested stays at target
    assert result.effective[(CBS, "RED-01")].value == 3
    assert result.effective[(CBS, "RED-02")].value == 4
    assert find_action(result, CBS, "RED-03").tier == "P2"


# --- SC5 ----------------------------------------------------------------

def test_sc5_stale_test_and_missing_evidence(run):
    _, result = run("SC5")
    assert result.effective[(ATM, "BKP-02")].value == 3  # validity rule
    assert result.effective[(ATM, "BKP-03")].value == 2  # evidence rule
    assert gate(result, ATM, "G5") == FAIL
    assert statuses(result) == {CBS: READY, PAY: READY, ATM: NOT_DEMONSTRATED}
    atm = actions_for(result, ATM)
    assert [(a.ref, a.action_type, a.tier) for a in atm] == [
        ("BKP-02", "Test and record the result", "P1"),
        ("BKP-03", "Record evidence", "P1"),
    ]


def test_sc5_variant_longer_validity_period(run):
    inp, result = run("SC5b")
    assert inp.validity_days == 730
    assert result.effective[(ATM, "BKP-02")].value == 4
    assert gate(result, ATM, "G5") == FAIL  # still fails on BKP-03
    assert [a.ref for a in actions_for(result, ATM)] == ["BKP-03"]


# --- Checks applied to every scenario -----------------------------------

ALL = ["B0", "SC1", "SC2a", "SC2b", "SC2c", "SC3", "SC4", "SC5", "SC5b", "DEMO"]


@pytest.mark.parametrize("name", ALL)
def test_status_is_identical_under_every_weighting_scheme(run, name):
    results = [run(name, scheme)[1] for scheme in ("A", "B", "C")]
    assert statuses(results[0]) == statuses(results[1]) == statuses(results[2])
    for code in (CBS, PAY, ATM):
        gates = [{g: r.result for g, r in res.readiness[code].gates.items()} for res in results]
        assert gates[0] == gates[1] == gates[2]


@pytest.mark.parametrize("name", ALL)
def test_same_input_gives_same_output(lib, name):
    from bcr.engine import assess
    from bcr.profiles import build_profile, profile_to_input
    first = assess(profile_to_input(build_profile(name, lib), lib))
    second = assess(profile_to_input(build_profile(name, lib), lib))
    assert first.scores.overall == second.scores.overall
    assert statuses(first) == statuses(second)
    assert first.actions == second.actions


@pytest.mark.parametrize("name", ALL)
def test_every_action_is_traceable(run, name):
    _, result = run(name)
    for a in result.actions:
        assert a.service_code and a.ref and a.title and a.tier in ("P1", "P2", "P3")
        assert a.expected_evidence
        if a.source == "control":
            assert a.current is not None and a.target is not None and a.gap == a.target - a.current
        else:
            assert a.gate and a.rules
