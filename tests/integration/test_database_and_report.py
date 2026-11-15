"""Integration tests: database round trip, seed loading, repository rules and report generation."""
from __future__ import annotations

from datetime import date, timedelta

import pytest

from bcr.data import repository as repo
from bcr.data.seed import reset_to_profile
from bcr.engine import FAIL, NOT_DEMONSTRATED, PASS_WITH_EXCEPTION, READY, assess
from bcr.profiles import profile_to_input
from bcr.reporting import actions_csv, content_hash, gaps_csv, render_html, report_from_profile
from bcr.service import build_report_data, exercise_views, run_assessment
from bcr.validation import ValidationError

PROFILES = ["B0", "SC1", "SC2a", "SC2b", "SC2c", "SC3", "SC4", "SC5", "SC5b", "DEMO"]
PAY, CBS, ATM = "SVC-PAY", "SVC-CBS", "SVC-ATM"


@pytest.fixture
def db(tmp_path):
    engine = repo.make_engine(tmp_path / "test.sqlite3")
    yield engine, repo.make_session_factory(engine)
    engine.dispose()


def summary(result):
    return (
        round(result.scores.overall, 10),
        {c: r.status for c, r in result.readiness.items()},
        {c: {g: x.result for g, x in r.gates.items()} for c, r in result.readiness.items()},
        [(a.tier, a.service_code, a.ref, a.action_type, a.priority) for a in result.actions],
    )


@pytest.mark.parametrize("name", PROFILES)
def test_database_round_trip_matches_direct_calculation(db, lib, profile, name):
    """Loading a profile into the database and reading it back gives the same result
    as running the engine on the profile directly."""
    engine, Session = db
    assessment_id = reset_to_profile(engine, name, lib)
    with Session() as s:
        _, from_db = run_assessment(s, assessment_id, lib)
    direct = assess(profile_to_input(profile(name), lib))
    assert summary(from_db) == summary(direct)


def test_seed_counts(db, lib):
    engine, Session = db
    assessment_id = reset_to_profile(engine, "B0", lib)
    with Session() as s:
        assert len(repo.list_services(s)) == 3
        assert len(repo.list_assets(s)) == 20
        assert len(repo.get_items(s, assessment_id)) == 84
        assert repo.get_organisation(s).is_fictional is True


def test_reset_replaces_previous_data(db, lib):
    engine, Session = db
    reset_to_profile(engine, "DEMO", lib)
    assessment_id = reset_to_profile(engine, "B0", lib)
    with Session() as s:
        assert len(repo.list_assessments(s)) == 1
        assert repo.list_exceptions(s, assessment_id) == []


# --- repository rules ----------------------------------------------------

@pytest.fixture
def b0(db, lib):
    engine, Session = db
    assessment_id = reset_to_profile(engine, "B0", lib)
    with Session() as s:
        yield s, assessment_id


def service_id(s, code):
    return next(x.id for x in repo.list_services(s) if x.code == code)


def test_invalid_service_is_not_stored(b0):
    s, _ = b0
    with pytest.raises(ValidationError):
        repo.save_service(s, {"code": "SVC-NEW", "name": "", "criticality": 9})
    assert len(repo.list_services(s)) == 3


def test_duplicate_service_code_is_rejected(b0):
    s, _ = b0
    with pytest.raises(ValidationError):
        repo.save_service(s, {"code": CBS, "name": "Copy", "criticality": 3})


def test_create_and_edit_service_and_asset(b0):
    s, _ = b0
    row = repo.save_service(s, {"code": "SVC-MOB", "name": "Mobile banking", "criticality": 4})
    repo.save_service(s, {"code": "SVC-MOB", "name": "Mobile banking app", "criticality": 5}, row.id)
    assert {x.code: (x.name, x.criticality) for x in repo.list_services(s)}["SVC-MOB"] == ("Mobile banking app", 5)
    asset = repo.save_asset(s, {"code": "A21", "name": "API gateway", "type": "Application server",
                                "site": "Primary DC", "criticality": 4, "owner": "Platform Lead"})
    repo.save_service_asset(s, row.id, asset.id, {"single_point_of_failure": True, "tested_alternative": False})
    assert len(repo.list_service_assets(s, row.id)) == 1


def test_service_cannot_depend_on_itself(b0):
    s, _ = b0
    sid = service_id(s, CBS)
    with pytest.raises(ValidationError):
        repo.set_service_dependencies(s, sid, [sid])


def test_editing_a_dependency_changes_the_result(b0, lib):
    s, assessment_id = b0
    link = next(x for x in repo.list_service_assets(s) if x.asset.code == "A20")
    repo.save_service_asset(s, link.service_id, link.asset_id,
                            {"single_point_of_failure": True, "tested_alternative": False})
    _, result = run_assessment(s, assessment_id, lib)
    assert result.readiness[PAY].gates["G3"].result == FAIL
    assert result.status(ATM) == NOT_DEMONSTRATED and result.status(CBS) == READY


def test_save_item_warns_and_the_engine_applies_the_rule(b0, lib):
    s, assessment_id = b0
    warnings = repo.save_item(s, assessment_id, service_id(s, ATM), "BKP-03",
                              {"grade": 3, "evidence_reference": ""}, lib)
    assert any("count as 2" in w for w in warnings)
    _, result = run_assessment(s, assessment_id, lib)
    assert result.effective[(ATM, "BKP-03")].value == 2
    assert result.readiness[ATM].gates["G5"].result == FAIL


def test_not_applicable_needs_a_justification(b0, lib):
    s, assessment_id = b0
    with pytest.raises(ValidationError):
        repo.save_item(s, assessment_id, service_id(s, ATM), "TPR-02", {"applicable": False}, lib)


def test_item_scope_is_enforced(b0, lib):
    s, assessment_id = b0
    with pytest.raises(ValidationError):
        repo.save_item(s, assessment_id, service_id(s, ATM), "GOV-01", {"grade": 3}, lib)
    with pytest.raises(ValidationError):
        repo.save_item(s, assessment_id, None, "BKP-01", {"grade": 3}, lib)
    with pytest.raises(KeyError):
        repo.save_item(s, assessment_id, None, "ZZZ-99", {"grade": 3}, lib)


def test_exception_lifecycle(b0, lib):
    s, assessment_id = b0
    link = next(x for x in repo.list_service_assets(s) if x.asset.code == "A20")
    repo.save_service_asset(s, link.service_id, link.asset_id,
                            {"single_point_of_failure": True, "tested_alternative": False})
    exc = repo.save_exception(s, assessment_id, link.service_id, {
        "gate": "G3", "rule": "DR3", "service_asset_id": link.id, "description": "Single path accepted",
        "owner": "Head of Payments", "treatment": "risk_acceptance", "approved_by": "Board Risk Committee",
        "due_date": date(2026, 11, 1) + timedelta(days=30), "status": "open"})
    _, result = run_assessment(s, assessment_id, lib)
    assert result.readiness[PAY].gates["G3"].result == PASS_WITH_EXCEPTION
    with pytest.raises(ValidationError):
        repo.close_exception(s, exc.id, "   ")
    repo.close_exception(s, exc.id, "Second path commissioned; test report TR-12")
    _, result = run_assessment(s, assessment_id, lib)
    assert result.readiness[PAY].gates["G3"].result == FAIL  # a closed exception waives nothing


def test_exercise_is_stored_and_decided(b0):
    s, assessment_id = b0
    results = {n: "yes" for n in repo.CHECK_NUMBERS}
    results["4.1"] = "no"
    repo.save_exercise(s, assessment_id, service_id(s, PAY),
                       {"exercise_date": date(2026, 11, 1), "kind": "exercise", "scenario": "Tabletop"},
                       results, conditions=[{"text": "Manual review", "owner": "Head of Payments",
                                             "expiry_date": date(2026, 11, 8)}])
    view = exercise_views(s, assessment_id)[0]
    assert view["decision"] == "Resume conditionally"
    assert view["results"]["4.1"] == "no" and len(view["conditions"]) == 1


def test_new_assessment_can_copy_an_existing_one(b0, lib):
    s, assessment_id = b0
    new = repo.create_assessment(s, {"name": "Re-assessment", "assessment_date": date(2027, 2, 1),
                                     "assessor": "Tester", "validity_days": 365}, lib, copy_from=assessment_id)
    assert len(repo.get_items(s, new.id)) == 84
    assert new.library_version == lib.version
    blank = repo.create_assessment(s, {"name": "Blank", "assessment_date": date(2027, 2, 1),
                                       "assessor": "", "validity_days": 365}, lib)
    _, result = run_assessment(s, blank.id, lib)
    assert result.scores.overall == 0 and result.scores.profile.coverage == 0


# --- report --------------------------------------------------------------

@pytest.mark.parametrize("name", PROFILES)
def test_report_is_identical_for_identical_input(lib, profile, name):
    first = render_html(report_from_profile(profile(name), lib))
    second = render_html(report_from_profile(profile(name), lib))
    assert content_hash(first) == content_hash(second)


def test_report_from_database_equals_report_from_profile(db, lib, profile):
    engine, Session = db
    assessment_id = reset_to_profile(engine, "SC3", lib)
    with Session() as s:
        from_db = render_html(build_report_data(s, assessment_id, lib))
    direct = render_html(report_from_profile(profile("SC3"), lib))
    assert from_db == direct


def test_report_contains_required_sections_and_notices(lib, profile):
    html = render_html(report_from_profile(profile("DEMO"), lib))
    for text in ("Fictional data", "Readiness by service", "Scores by control domain", "Risk register",
                 "Gap analysis and remediation plan", "Exception register", "Tool 1", "Tool 2",
                 "Sensitivity to weighting", "Limitations", "not a NIST CSF Tier",
                 "identical under all three schemes", "Control library", "Validity period"):
        assert text in html, text
    assert "<script" not in html.lower()


def test_report_escapes_user_text(lib, profile):
    data = profile("B0")
    data["services"][0]["business_owner"] = "<script>alert(1)</script>"
    html = render_html(report_from_profile(data, lib))
    assert "<script>alert(1)</script>" not in html
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in html


def test_every_action_in_the_report_is_traceable(lib, profile):
    """Decision support: each action row cites service, reference, grades or gate, and expected evidence."""
    for name in PROFILES:
        d = report_from_profile(profile(name), lib)
        lines = actions_csv(d.result).splitlines()
        assert len(lines) == len(d.result.actions) + 1
        for a in d.result.actions:
            assert a.service_code and a.ref and a.expected_evidence
            assert (a.current is not None and a.target is not None) or (a.gate and a.rules)


def test_gaps_csv_lists_every_assessed_item(lib, profile):
    d = report_from_profile(profile("SC5"), lib)
    lines = gaps_csv(d.inp, d.result).splitlines()
    assert len(lines) == 84 + 1
    row = next(x for x in lines if x.startswith("SVC-ATM,BKP-02,"))
    assert ",4,3,4,1,yes," in row  # recorded 4, effective 3, target 4, gap 1
