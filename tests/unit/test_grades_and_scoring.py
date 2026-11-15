"""Unit tests: effective-grade rules and scoring formulas on a small fixture
whose expected values are worked out by hand in the comments.
"""
from __future__ import annotations

from datetime import date

import pytest

from bcr.engine import assess, effective_map
from bcr.engine.grades import effective_grade
from bcr.engine.models import AssessmentInput, Item, Service
from bcr.engine.scoring import SCHEMES, compute_scores, pct
from bcr.library import Control

D = date(2026, 11, 1)


def item(grade, ref="EV-1", when=None, applicable=True, why=""):
    return Item("S1", "X-01", applicable=applicable, na_justification=why, grade=grade,
                evidence_reference=ref, evidence_date=when)


# --- effective grade (specification section 3) ---------------------------

def test_missing_item_is_not_assessed():
    e = effective_grade(None, D, 365)
    assert (e.value, e.assessed) == (0, False)


def test_grade_none_is_not_assessed():
    e = effective_grade(item(None), D, 365)
    assert (e.value, e.assessed) == (0, False)


@pytest.mark.parametrize("grade", [0, 1, 2])
def test_low_grades_stand_without_evidence(grade):
    e = effective_grade(item(grade, ref=""), D, 365)
    assert (e.value, e.assessed, e.reason) == (grade, True, "")


@pytest.mark.parametrize("grade", [3, 4])
def test_grade_3_or_4_without_evidence_reference_counts_as_2(grade):
    assert effective_grade(item(grade, ref="  ", when=date(2026, 10, 1)), D, 365).value == 2


def test_grade_3_with_reference_stands():
    assert effective_grade(item(3), D, 365).value == 3


def test_grade_4_without_test_date_counts_as_3():
    assert effective_grade(item(4, when=None), D, 365).value == 3


def test_grade_4_within_validity_stands():
    assert effective_grade(item(4, when=date(2025, 11, 1)), D, 365).value == 4  # exactly 365 days


def test_grade_4_older_than_validity_counts_as_3():
    e = effective_grade(item(4, when=date(2025, 10, 31)), D, 365)  # 366 days
    assert e.value == 3 and "366" in e.reason


def test_grade_4_with_future_test_date_counts_as_3():
    assert effective_grade(item(4, when=date(2026, 11, 2)), D, 365).value == 3


def test_not_applicable_with_justification_is_excluded():
    e = effective_grade(item(None, applicable=False, why="No vendor access exists."), D, 365)
    assert e.value is None and e.assessed


def test_not_applicable_without_justification_scores_zero():
    e = effective_grade(item(3, applicable=False, why=" "), D, 365)
    assert (e.value, e.assessed) == (0, False)


def test_invalid_grade_is_rejected():
    with pytest.raises(ValueError):
        effective_grade(item(5), D, 365)


# --- scoring formulas (specification section 4) --------------------------

def ctl(cid, domain, weight=1, target=3, scope="service"):
    return Control(id=cid, domain=domain, scope=scope, basis="Des", weight=weight, target=target,
                   gate=None, title=cid, question="q", evidence=("e",), refs={}, rules=(),
                   rationale="r", remediation="m")


@pytest.fixture
def small():
    """Two services, two domains.

    Controls: AAA-01 (w1), AAA-02 (w2), BKP-01 (w1), ORG-level GOV-01 (w1).
    S1 (criticality 5): AAA-01=4, AAA-02=2, BKP-01=3, GOV-01=2
    S2 (criticality 1): AAA-01=0, AAA-02 not applicable, BKP-01 not assessed, GOV-01=2
    """
    controls = (ctl("AAA-01", "AAA"), ctl("AAA-02", "AAA", weight=2), ctl("BKP-01", "BKP"),
                ctl("GOV-01", "GOV", scope="organisation"))
    items = [
        Item("S1", "AAA-01", grade=4, evidence_reference="E", evidence_date=date(2026, 10, 1)),
        Item("S1", "AAA-02", grade=2),
        Item("S1", "BKP-01", grade=3, evidence_reference="E"),
        Item("S2", "AAA-01", grade=0),
        Item("S2", "AAA-02", applicable=False, na_justification="Not used by S2."),
        Item(None, "GOV-01", grade=2),
    ]
    return AssessmentInput(assessment_date=D, controls=controls,
                           services=[Service("S1", "One", 5), Service("S2", "Two", 1)], items=items)


def test_scheme_a_hand_calculation(small):
    """S1: AAA = (1*1.0 + 2*0.5)/3 = 0.666667; BKP = 0.75; GOV = 0.5 -> mean 0.638889
    S2: AAA = 0/1 = 0 (AAA-02 excluded); BKP = 0 (not assessed); GOV = 0.5 -> mean 0.166667
    Overall = (5*0.638889 + 1*0.166667)/6 = 0.560185
    """
    s = compute_scores(small, effective_map(small), SCHEMES["A"])
    assert s.services["S1"].domain_scores == pytest.approx({"AAA": 2 / 3, "BKP": 0.75, "GOV": 0.5})
    assert s.services["S1"].score == pytest.approx(0.6388889, abs=1e-6)
    assert s.services["S2"].score == pytest.approx(0.1666667, abs=1e-6)
    assert s.overall == pytest.approx(0.5601852, abs=1e-6)


def test_scheme_b_hand_calculation(small):
    """Equal weights. S1: AAA = (1.0 + 0.5)/2 = 0.75; BKP .75; GOV .5 -> 0.666667
    S2 unchanged at 0.166667. Overall = (0.666667 + 0.166667)/2 = 0.416667
    """
    s = compute_scores(small, effective_map(small), SCHEMES["B"])
    assert s.services["S1"].score == pytest.approx(0.6666667, abs=1e-6)
    assert s.overall == pytest.approx(0.4166667, abs=1e-6)


def test_scheme_c_hand_calculation(small):
    """BKP domain weight 2. S1 = (0.666667 + 2*0.75 + 0.5)/4 = 0.666667
    S2 = (0 + 2*0 + 0.5)/4 = 0.125. Overall = (5*0.666667 + 0.125)/6 = 0.576389
    """
    s = compute_scores(small, effective_map(small), SCHEMES["C"])
    assert s.services["S1"].score == pytest.approx(0.6666667, abs=1e-6)
    assert s.services["S2"].score == pytest.approx(0.125)
    assert s.overall == pytest.approx(0.5763889, abs=1e-6)


def test_coverage_demonstrated_share_and_distribution(small):
    s = compute_scores(small, effective_map(small), SCHEMES["A"])
    p1, p2 = s.services["S1"].profile, s.services["S2"].profile
    assert (p1.applicable, p1.assessed, p1.demonstrated) == (4, 4, 1)
    assert p1.distribution == {0: 0, 1: 0, 2: 2, 3: 1, 4: 1}
    # S2: AAA-02 excluded; BKP-01 not assessed -> 3 applicable, 2 assessed
    assert (p2.applicable, p2.assessed, p2.demonstrated) == (3, 2, 0)
    assert p2.coverage == pytest.approx(2 / 3)
    # Overall counts the organisation-level control once: 4 + 2 + 1 - excluded
    assert s.profile.applicable == 6 and s.profile.assessed == 5


def test_service_with_no_applicable_controls_has_no_score():
    inp = AssessmentInput(assessment_date=D, controls=(ctl("AAA-01", "AAA"),),
                          services=[Service("S1", "One", 3)],
                          items=[Item("S1", "AAA-01", applicable=False, na_justification="n/a here")])
    result = assess(inp)
    assert result.scores.services["S1"].score is None
    assert result.scores.overall is None
    assert pct(result.scores.overall) == "n/a"


def test_pct_formats_one_decimal():
    assert pct(0.79875) == "79.9%"
    assert pct(1.0) == "100.0%"
