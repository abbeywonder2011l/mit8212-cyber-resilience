"""Unit tests: input validation and control-library validation."""
from __future__ import annotations

import copy
import json
from datetime import date

import pytest

from bcr import validation as v
from bcr.library import DEFAULT_PATH, LibraryError, parse_library, validate_library

GOOD_SERVICE = {"code": "SVC-X", "name": "X", "criticality": 3, "mtd_hours": 4, "rto_hours": 2,
                "rpo_minutes": 15, "requirements_approved": True}


def test_valid_service_passes():
    assert v.validate_service(GOOD_SERVICE) == []


@pytest.mark.parametrize("changes, fragment", [
    ({"code": " "}, "code is required"),
    ({"name": ""}, "name is required"),
    ({"criticality": 0}, "1 to 5"),
    ({"criticality": 6}, "1 to 5"),
    ({"criticality": 2.5}, "1 to 5"),
    ({"rto_hours": -1}, "cannot be negative"),
    ({"rto_hours": 9}, "cannot be greater"),
    ({"rpo_minutes": None}, "until all three"),
])
def test_invalid_service_is_rejected(changes, fragment):
    errors = v.validate_service({**GOOD_SERVICE, **changes})
    assert any(fragment in e for e in errors), errors


def test_service_cannot_depend_on_itself():
    assert v.validate_service_dependency("A", "A")
    assert v.validate_service_dependency("A", "B") == []


def test_asset_validation():
    good = {"code": "A1", "name": "Server", "type": "Database", "criticality": 4}
    assert v.validate_asset(good) == []
    assert v.validate_asset({**good, "type": "Spaceship"})
    assert v.validate_asset({**good, "is_third_party": True, "provider": ""})
    assert v.validate_asset({**good, "is_third_party": True, "provider": "Carrier A"}) == []


def test_risk_validation():
    assert v.validate_risk({"title": "x", "likelihood": 3, "impact": 5}) == []
    assert v.validate_risk({"title": "", "likelihood": 3, "impact": 5})
    assert v.validate_risk({"title": "x", "likelihood": 0, "impact": 5})
    assert v.validate_risk({"title": "x", "likelihood": 3, "impact": True})


def test_item_validation_errors():
    errors, _ = v.validate_item({"grade": 7})
    assert errors
    errors, _ = v.validate_item({"applicable": False, "na_justification": "  "})
    assert any("written justification" in e for e in errors)
    errors, _ = v.validate_item({"applicable": False, "na_justification": "No vendor access."})
    assert errors == []


def test_item_validation_warnings_mirror_the_effective_grade_rules():
    d = date(2026, 11, 1)
    _, w = v.validate_item({"grade": 3, "evidence_reference": ""}, d)
    assert any("count as 2" in x for x in w)
    _, w = v.validate_item({"grade": 4, "evidence_reference": "E", "evidence_date": None}, d)
    assert any("count as 3" in x for x in w)
    _, w = v.validate_item({"grade": 4, "evidence_reference": "E", "evidence_date": date(2026, 12, 1)}, d)
    assert any("after the assessment date" in x for x in w)
    _, w = v.validate_item({"grade": 4, "evidence_reference": "E", "evidence_date": date(2026, 10, 1)}, d)
    assert w == []


def test_exception_cannot_be_closed_without_evidence():
    assert v.validate_exception_close("  ")
    assert v.validate_exception_close("Second carrier path commissioned; test report TR-9") == []
    base = {"description": "d", "owner": "o", "treatment": "risk_acceptance", "due_date": date(2026, 12, 1)}
    assert v.validate_exception(base) == []
    assert v.validate_exception({**base, "status": "closed", "closure_evidence": ""})
    assert v.validate_exception({**base, "treatment": "ignore"})
    assert v.validate_exception({**base, "due_date": None})


def test_assessment_validation():
    good = {"name": "A", "assessment_date": date(2026, 11, 1), "validity_days": 365}
    assert v.validate_assessment(good) == []
    assert v.validate_assessment({**good, "validity_days": 0})
    assert v.validate_assessment({**good, "name": ""})


# --- control library -----------------------------------------------------

@pytest.fixture
def raw():
    return json.loads(DEFAULT_PATH.read_text(encoding="utf-8"))


def test_shipped_library_is_valid(raw):
    assert validate_library(raw) == []


def test_reg_basis_requires_a_cbn_reference(raw):
    bad = copy.deepcopy(raw)
    bad["controls"][0]["refs"]["CBN"] = []
    assert any("no CBN reference" in e for e in validate_library(bad))


def test_unknown_reference_is_rejected(raw):
    bad = copy.deepcopy(raw)
    bad["controls"][0]["refs"]["CSF"].append("ZZ.ZZ-99")
    assert any("not in the reference register" in e for e in validate_library(bad))


def test_duplicate_id_and_bad_weight_are_rejected(raw):
    bad = copy.deepcopy(raw)
    bad["controls"][1]["id"] = bad["controls"][0]["id"]
    bad["controls"][2]["weight"] = 5
    errors = validate_library(bad)
    assert any("duplicate id" in e for e in errors) and any("weight must be" in e for e in errors)


def test_invalid_library_cannot_be_loaded(raw):
    bad = copy.deepcopy(raw)
    bad["controls"][0]["target"] = 9
    with pytest.raises(LibraryError):
        parse_library(bad)
