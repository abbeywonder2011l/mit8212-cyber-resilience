"""Load a synthetic profile into the database (replaces all existing data)."""
from __future__ import annotations

from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from bcr.library import Library
from bcr.profiles import build_profile

from . import models as m


def reset_to_profile(engine: Engine, name: str, lib: Library) -> int:
    """Drop every table, recreate the schema and load one profile.

    Returns the id of the assessment created.
    """
    profile = build_profile(name, lib)
    m.Base.metadata.drop_all(engine)
    m.Base.metadata.create_all(engine)
    with Session(engine) as s:
        assessment_id = load_profile(s, profile)
        s.commit()
    return assessment_id


def load_profile(s: Session, profile: dict) -> int:
    org = profile["organisation"]
    s.add(m.Organisation(name=org["name"], is_fictional=org.get("is_fictional", True),
                         notice=profile.get("notice", "")))

    services: dict[str, m.Service] = {}
    for d in profile["services"]:
        row = m.Service(
            code=d["code"], name=d["name"], description=d.get("description", ""),
            criticality=d["criticality"], business_owner=d.get("business_owner", ""),
            technical_owner=d.get("technical_owner", ""), mtd_hours=d.get("mtd_hours"),
            rto_hours=d.get("rto_hours"), rpo_minutes=d.get("rpo_minutes"),
            requirements_approved=d.get("requirements_approved", False),
        )
        s.add(row)
        services[d["code"]] = row
    s.flush()
    for d in profile["services"]:
        for dep in d.get("depends_on", []):
            s.add(m.ServiceDependency(service_id=services[d["code"]].id, depends_on_id=services[dep].id))

    assets: dict[str, m.Asset] = {}
    for d in profile["assets"]:
        row = m.Asset(code=d["code"], name=d["name"], type=d["type"], site=d.get("site", ""),
                      criticality=d["criticality"], owner=d.get("owner", ""),
                      is_third_party=d.get("is_third_party", False), provider=d.get("provider", ""))
        s.add(row)
        assets[d["code"]] = row
    s.flush()

    links: dict[tuple[str, str], m.ServiceAsset] = {}
    for d in profile["service_assets"]:
        row = m.ServiceAsset(
            service_id=services[d["service"]].id, asset_id=assets[d["asset"]].id,
            single_point_of_failure=d["single_point_of_failure"],
            tested_alternative=d["tested_alternative"],
            recovery_coordination_tested=d["recovery_coordination_tested"], note=d.get("note", ""),
        )
        s.add(row)
        links[(d["service"], d["asset"])] = row
    s.flush()

    for d in profile["risks"]:
        s.add(m.ThreatScenario(
            service_id=services[d["service"]].id, title=d["title"], category=d.get("category", ""),
            likelihood=d["likelihood"], impact=d["impact"],
            affects_recovery_environment=d.get("affects_recovery_environment", False),
        ))

    a = profile["assessment"]
    assessment = m.Assessment(name=a["name"], assessment_date=a["assessment_date"],
                              assessor=a.get("assessor", ""), validity_days=a["validity_days"],
                              library_version=a.get("library_version", ""), status="draft")
    s.add(assessment)
    s.flush()

    for d in profile["items"]:
        s.add(m.AssessmentItem(
            assessment_id=assessment.id,
            service_id=services[d["service"]].id if d["service"] else None,
            control_id=d["control"], applicable=d["applicable"],
            na_justification=d["na_justification"], grade=d["grade"],
            evidence_description=d["evidence_description"],
            evidence_reference=d["evidence_reference"], evidence_date=d["evidence_date"],
        ))

    for d in profile["exceptions"]:
        s.add(m.ExceptionRow(
            assessment_id=assessment.id, service_id=services[d["service"]].id,
            rule=d.get("rule", ""), gate=d.get("gate", ""),
            service_asset_id=links[(d["service"], d["asset"])].id if d.get("asset") else None,
            control_id=d.get("control"), description=d.get("description", ""),
            owner=d.get("owner", ""), treatment=d.get("treatment", ""),
            compensating_control=d.get("compensating_control", ""),
            approved_by=d.get("approved_by", ""), due_date=d.get("due_date"),
            status=d.get("status", "open"), closure_evidence=d.get("closure_evidence", ""),
        ))

    for d in profile["exercises"]:
        row = m.Exercise(assessment_id=assessment.id, service_id=services[d["service"]].id,
                         exercise_date=d["exercise_date"], kind=d["kind"], scenario=d["scenario"])
        for number, result in d["results"].items():
            row.checks.append(m.ExerciseCheck(check_no=number, result=result))
        for c in d["conditions"]:
            row.conditions.append(m.ExerciseCondition(text=c["text"], owner=c["owner"],
                                                      expiry_date=c["expiry_date"]))
        s.add(row)

    s.flush()
    return assessment.id
