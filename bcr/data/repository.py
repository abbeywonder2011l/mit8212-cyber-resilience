"""Data access: every read and write goes through these functions.

Writes are validated first; invalid input raises ValidationError and nothing
is stored.
"""
from __future__ import annotations

from datetime import date
from pathlib import Path

from sqlalchemy import create_engine, select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from bcr import validation as v
from bcr.engine import models as em
from bcr.engine.resumption import CHECK_NUMBERS, Decision, ResumptionCondition, decide
from bcr.library import Library

from . import models as m


# --- engine and sessions -------------------------------------------------

def make_engine(db_path: str | Path) -> Engine:
    """Create the engine and any missing tables. Accept SQLite paths or PostgreSQL URLs."""
    target = str(db_path)
    if target == ":memory:":
        url = "sqlite://"
    elif target.startswith(("postgres://", "postgresql://", "postgresql+psycopg://")):
        url = target.replace("postgres://", "postgresql://", 1)
        if url.startswith("postgresql://"):
            url = url.replace("postgresql://", "postgresql+psycopg://", 1)
    else:
        url = f"sqlite:///{Path(target).as_posix()}"
    engine = create_engine(url, pool_pre_ping=True)
    m.Base.metadata.create_all(engine)
    return engine


def make_session_factory(engine: Engine) -> sessionmaker:
    return sessionmaker(engine, expire_on_commit=False)


def _check(errors: list[str]) -> None:
    if errors:
        raise v.ValidationError(errors)


# --- organisation --------------------------------------------------------

def get_organisation(s: Session) -> m.Organisation | None:
    return s.scalars(select(m.Organisation)).first()


# --- services ------------------------------------------------------------

SERVICE_FIELDS = ("code", "name", "description", "criticality", "business_owner", "technical_owner",
                  "mtd_hours", "rto_hours", "rpo_minutes", "requirements_approved")


def list_services(s: Session) -> list[m.Service]:
    return list(s.scalars(select(m.Service).order_by(m.Service.id)))


def save_service(s: Session, data: dict, service_id: int | None = None) -> m.Service:
    _check(v.validate_service(data))
    code = data["code"].strip()
    clash = s.scalars(select(m.Service).where(m.Service.code == code)).first()
    if clash is not None and clash.id != service_id:
        _check([f"Service code '{code}' is already in use."])
    row = s.get(m.Service, service_id) if service_id else m.Service()
    for f in SERVICE_FIELDS:
        if f in data:
            value = data[f]
            setattr(row, f, value.strip() if isinstance(value, str) else value)
    s.add(row)
    s.commit()
    return row


def depends_on_map(s: Session) -> dict[int, list[int]]:
    out: dict[int, list[int]] = {}
    for d in s.scalars(select(m.ServiceDependency).order_by(m.ServiceDependency.id)):
        out.setdefault(d.service_id, []).append(d.depends_on_id)
    return out


def set_service_dependencies(s: Session, service_id: int, depends_on_ids: list[int]) -> None:
    if service_id in depends_on_ids:
        _check(["A service cannot depend on itself."])
    for d in s.scalars(select(m.ServiceDependency).where(m.ServiceDependency.service_id == service_id)):
        s.delete(d)
    s.flush()
    for dep_id in dict.fromkeys(depends_on_ids):
        s.add(m.ServiceDependency(service_id=service_id, depends_on_id=dep_id))
    s.commit()


# --- assets and dependencies --------------------------------------------

ASSET_FIELDS = ("code", "name", "type", "site", "criticality", "owner", "is_third_party", "provider")


def list_assets(s: Session) -> list[m.Asset]:
    return list(s.scalars(select(m.Asset).order_by(m.Asset.code)))


def save_asset(s: Session, data: dict, asset_id: int | None = None) -> m.Asset:
    _check(v.validate_asset(data))
    code = data["code"].strip()
    clash = s.scalars(select(m.Asset).where(m.Asset.code == code)).first()
    if clash is not None and clash.id != asset_id:
        _check([f"Asset code '{code}' is already in use."])
    row = s.get(m.Asset, asset_id) if asset_id else m.Asset()
    for f in ASSET_FIELDS:
        if f in data:
            value = data[f]
            setattr(row, f, value.strip() if isinstance(value, str) else value)
    s.add(row)
    s.commit()
    return row


def list_service_assets(s: Session, service_id: int | None = None) -> list[m.ServiceAsset]:
    q = select(m.ServiceAsset).order_by(m.ServiceAsset.service_id, m.ServiceAsset.asset_id)
    if service_id is not None:
        q = q.where(m.ServiceAsset.service_id == service_id)
    return list(s.scalars(q))


def save_service_asset(s: Session, service_id: int, asset_id: int, data: dict) -> m.ServiceAsset:
    row = s.scalars(select(m.ServiceAsset).where(
        m.ServiceAsset.service_id == service_id, m.ServiceAsset.asset_id == asset_id)).first()
    if row is None:
        row = m.ServiceAsset(service_id=service_id, asset_id=asset_id)
    for f in ("single_point_of_failure", "tested_alternative", "recovery_coordination_tested", "note"):
        if f in data:
            setattr(row, f, data[f])
    s.add(row)
    s.commit()
    return row


# --- risks ---------------------------------------------------------------

def list_risks(s: Session) -> list[m.ThreatScenario]:
    return list(s.scalars(select(m.ThreatScenario).order_by(m.ThreatScenario.id)))


def save_risk(s: Session, service_id: int, data: dict, risk_id: int | None = None) -> m.ThreatScenario:
    _check(v.validate_risk(data))
    row = s.get(m.ThreatScenario, risk_id) if risk_id else m.ThreatScenario(service_id=service_id)
    row.service_id = service_id
    for f in ("title", "category", "likelihood", "impact", "affects_recovery_environment", "note"):
        if f in data:
            setattr(row, f, data[f])
    s.add(row)
    s.commit()
    return row


def delete_risk(s: Session, risk_id: int) -> None:
    row = s.get(m.ThreatScenario, risk_id)
    if row is not None:
        s.delete(row)
        s.commit()


# --- assessments and items -----------------------------------------------

def list_assessments(s: Session) -> list[m.Assessment]:
    return list(s.scalars(select(m.Assessment).order_by(m.Assessment.id)))


def create_assessment(s: Session, data: dict, lib: Library, copy_from: int | None = None) -> m.Assessment:
    _check(v.validate_assessment(data))
    row = m.Assessment(
        name=data["name"].strip(), assessment_date=data["assessment_date"],
        assessor=data.get("assessor", "").strip(), validity_days=data["validity_days"],
        library_version=lib.version, status="draft",
    )
    s.add(row)
    s.flush()
    if copy_from is not None:
        for item in s.scalars(select(m.AssessmentItem).where(m.AssessmentItem.assessment_id == copy_from)):
            s.add(m.AssessmentItem(
                assessment_id=row.id, service_id=item.service_id, control_id=item.control_id,
                applicable=item.applicable, na_justification=item.na_justification, grade=item.grade,
                evidence_description=item.evidence_description,
                evidence_reference=item.evidence_reference, evidence_date=item.evidence_date,
            ))
    s.commit()
    return row


def get_items(s: Session, assessment_id: int) -> dict[tuple[int | None, str], m.AssessmentItem]:
    rows = s.scalars(select(m.AssessmentItem).where(m.AssessmentItem.assessment_id == assessment_id))
    return {(r.service_id, r.control_id): r for r in rows}


def save_item(s: Session, assessment_id: int, service_id: int | None, control_id: str,
              data: dict, lib: Library) -> list[str]:
    """Store one assessed control. Returns warnings (the effective-grade rules that will apply)."""
    control = lib.control(control_id)  # KeyError if the control is not in the library
    if control.scope == "organisation" and service_id is not None:
        _check([f"{control_id} is assessed once for the organisation, not per service."])
    if control.scope == "service" and service_id is None:
        _check([f"{control_id} must be assessed for a service."])
    assessment = s.get(m.Assessment, assessment_id)
    errors, warnings = v.validate_item(data, assessment.assessment_date)
    _check(errors)
    q = select(m.AssessmentItem).where(
        m.AssessmentItem.assessment_id == assessment_id, m.AssessmentItem.control_id == control_id)
    q = q.where(m.AssessmentItem.service_id.is_(None) if service_id is None
                else m.AssessmentItem.service_id == service_id)
    row = s.scalars(q).first()
    if row is None:
        row = m.AssessmentItem(assessment_id=assessment_id, service_id=service_id, control_id=control_id)
    row.applicable = data.get("applicable", True)
    row.na_justification = (data.get("na_justification") or "").strip()
    row.grade = data.get("grade")
    row.evidence_description = (data.get("evidence_description") or "").strip()
    row.evidence_reference = (data.get("evidence_reference") or "").strip()
    row.evidence_date = data.get("evidence_date")
    s.add(row)
    s.commit()
    return warnings


# --- exceptions ----------------------------------------------------------

def list_exceptions(s: Session, assessment_id: int) -> list[m.ExceptionRow]:
    return list(s.scalars(select(m.ExceptionRow)
                          .where(m.ExceptionRow.assessment_id == assessment_id)
                          .order_by(m.ExceptionRow.id)))


def save_exception(s: Session, assessment_id: int, service_id: int, data: dict) -> m.ExceptionRow:
    _check(v.validate_exception(data))
    row = m.ExceptionRow(assessment_id=assessment_id, service_id=service_id)
    for f in ("rule", "gate", "service_asset_id", "control_id", "description", "owner", "treatment",
              "compensating_control", "approved_by", "due_date", "status", "closure_evidence"):
        if f in data:
            setattr(row, f, data[f])
    s.add(row)
    s.commit()
    return row


def close_exception(s: Session, exception_id: int, closure_evidence: str) -> m.ExceptionRow:
    _check(v.validate_exception_close(closure_evidence))
    row = s.get(m.ExceptionRow, exception_id)
    row.status = "closed"
    row.closure_evidence = closure_evidence.strip()
    s.commit()
    return row


# --- exercises (Tool 2) --------------------------------------------------

def list_exercises(s: Session, assessment_id: int) -> list[m.Exercise]:
    return list(s.scalars(select(m.Exercise)
                          .where(m.Exercise.assessment_id == assessment_id)
                          .order_by(m.Exercise.id)))


def save_exercise(s: Session, assessment_id: int, service_id: int, data: dict,
                  results: dict[str, str | None], evidence: dict[str, str] | None = None,
                  conditions: list[dict] | None = None) -> m.Exercise:
    _check(v.validate_exercise(data))
    bad = [k for k, val in results.items() if k not in CHECK_NUMBERS or val not in ("yes", "no", "na", None)]
    if bad:
        _check([f"Invalid checklist entries: {', '.join(bad)}"])
    row = m.Exercise(assessment_id=assessment_id, service_id=service_id,
                     exercise_date=data["exercise_date"], kind=data["kind"],
                     scenario=data["scenario"].strip())
    for n in CHECK_NUMBERS:
        row.checks.append(m.ExerciseCheck(check_no=n, result=results.get(n),
                                          evidence_reference=(evidence or {}).get(n, "")))
    for c in conditions or []:
        row.conditions.append(m.ExerciseCondition(text=c["text"], owner=c.get("owner", ""),
                                                  expiry_date=c.get("expiry_date")))
    s.add(row)
    s.commit()
    return row


def exercise_decision(exercise: m.Exercise) -> Decision:
    results = {c.check_no: c.result for c in exercise.checks}
    conditions = [ResumptionCondition(c.text, c.owner, c.expiry_date) for c in exercise.conditions]
    return decide(results, conditions, exercise.exercise_date)


# --- engine input --------------------------------------------------------

def load_assessment_input(s: Session, assessment_id: int, lib: Library) -> em.AssessmentInput:
    assessment = s.get(m.Assessment, assessment_id)
    if assessment is None:
        raise KeyError(f"No assessment with id {assessment_id}")
    service_rows = list_services(s)
    code_of = {r.id: r.code for r in service_rows}
    deps = depends_on_map(s)
    services = [
        em.Service(
            code=r.code, name=r.name, criticality=r.criticality,
            business_owner=r.business_owner or "", technical_owner=r.technical_owner or "",
            mtd_hours=r.mtd_hours, rto_hours=r.rto_hours, rpo_minutes=r.rpo_minutes,
            requirements_approved=bool(r.requirements_approved),
            depends_on=tuple(code_of[d] for d in deps.get(r.id, []) if d in code_of),
        )
        for r in service_rows
    ]
    dependencies = [
        em.Dependency(
            id=sa.id, service_code=code_of[sa.service_id], asset_code=sa.asset.code,
            asset_name=sa.asset.name, is_third_party=bool(sa.asset.is_third_party),
            single_point_of_failure=bool(sa.single_point_of_failure),
            tested_alternative=bool(sa.tested_alternative),
            recovery_coordination_tested=bool(sa.recovery_coordination_tested),
        )
        for sa in list_service_assets(s)
    ]
    risks = [
        em.Risk(service_code=code_of[r.service_id], title=r.title, likelihood=r.likelihood,
                impact=r.impact, category=r.category or "",
                affects_recovery_environment=bool(r.affects_recovery_environment))
        for r in list_risks(s)
    ]
    known = set(lib.ids())
    items = [
        em.Item(
            service_code=code_of.get(r.service_id) if r.service_id is not None else None,
            control_id=r.control_id, applicable=bool(r.applicable),
            na_justification=r.na_justification or "", grade=r.grade,
            evidence_reference=r.evidence_reference or "", evidence_date=r.evidence_date,
            evidence_description=r.evidence_description or "",
        )
        for r in get_items(s, assessment_id).values() if r.control_id in known
    ]
    exceptions = [
        em.ExceptionRecord(
            id=r.id, service_code=code_of[r.service_id], gate=r.gate or "", rule=r.rule or "",
            dependency_id=r.service_asset_id, control_id=r.control_id,
            description=r.description or "", owner=r.owner or "", treatment=r.treatment or "",
            compensating_control=r.compensating_control or "", approved_by=r.approved_by or "",
            due_date=r.due_date, status=r.status, closure_evidence=r.closure_evidence or "",
        )
        for r in list_exceptions(s, assessment_id)
    ]
    return em.AssessmentInput(
        assessment_date=assessment.assessment_date, validity_days=assessment.validity_days,
        controls=lib.controls, services=services, dependencies=dependencies,
        risks=risks, items=items, exceptions=exceptions,
    )


def today() -> date:
    return date.today()
