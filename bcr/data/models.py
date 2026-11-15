"""Database schema (SQLAlchemy 2 declarative models).

No SQLite-only features are used, so the same models can be pointed at
PostgreSQL by changing the connection string.
"""
from __future__ import annotations

from datetime import date

from sqlalchemy import Boolean, Date, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Organisation(Base):
    __tablename__ = "organisation"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    is_fictional: Mapped[bool] = mapped_column(Boolean, default=True)
    notice: Mapped[str] = mapped_column(Text, default="")


class Service(Base):
    __tablename__ = "service"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(30), unique=True)
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text, default="")
    criticality: Mapped[int] = mapped_column(Integer)
    business_owner: Mapped[str] = mapped_column(String(200), default="")
    technical_owner: Mapped[str] = mapped_column(String(200), default="")
    mtd_hours: Mapped[float | None] = mapped_column(Float, nullable=True)
    rto_hours: Mapped[float | None] = mapped_column(Float, nullable=True)
    rpo_minutes: Mapped[float | None] = mapped_column(Float, nullable=True)
    requirements_approved: Mapped[bool] = mapped_column(Boolean, default=False)


class ServiceDependency(Base):
    __tablename__ = "service_dependency"
    __table_args__ = (UniqueConstraint("service_id", "depends_on_id"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    service_id: Mapped[int] = mapped_column(ForeignKey("service.id"))
    depends_on_id: Mapped[int] = mapped_column(ForeignKey("service.id"))


class Asset(Base):
    __tablename__ = "asset"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(30), unique=True)
    name: Mapped[str] = mapped_column(String(200))
    type: Mapped[str] = mapped_column(String(60))
    site: Mapped[str] = mapped_column(String(100), default="")
    criticality: Mapped[int] = mapped_column(Integer)
    owner: Mapped[str] = mapped_column(String(200), default="")
    is_third_party: Mapped[bool] = mapped_column(Boolean, default=False)
    provider: Mapped[str] = mapped_column(String(200), default="")


class ServiceAsset(Base):
    __tablename__ = "service_asset"
    __table_args__ = (UniqueConstraint("service_id", "asset_id"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    service_id: Mapped[int] = mapped_column(ForeignKey("service.id"))
    asset_id: Mapped[int] = mapped_column(ForeignKey("asset.id"))
    single_point_of_failure: Mapped[bool] = mapped_column(Boolean, default=False)
    tested_alternative: Mapped[bool] = mapped_column(Boolean, default=True)
    recovery_coordination_tested: Mapped[bool] = mapped_column(Boolean, default=True)
    note: Mapped[str] = mapped_column(Text, default="")
    service: Mapped[Service] = relationship()
    asset: Mapped[Asset] = relationship()


class ThreatScenario(Base):
    __tablename__ = "threat_scenario"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    service_id: Mapped[int] = mapped_column(ForeignKey("service.id"))
    title: Mapped[str] = mapped_column(String(300))
    category: Mapped[str] = mapped_column(String(60), default="")
    likelihood: Mapped[int] = mapped_column(Integer)
    impact: Mapped[int] = mapped_column(Integer)
    affects_recovery_environment: Mapped[bool] = mapped_column(Boolean, default=False)
    note: Mapped[str] = mapped_column(Text, default="")
    service: Mapped[Service] = relationship()


class Assessment(Base):
    __tablename__ = "assessment"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    assessment_date: Mapped[date] = mapped_column(Date)
    assessor: Mapped[str] = mapped_column(String(200), default="")
    library_version: Mapped[str] = mapped_column(String(40), default="")
    validity_days: Mapped[int] = mapped_column(Integer, default=365)
    status: Mapped[str] = mapped_column(String(20), default="draft")


class AssessmentItem(Base):
    __tablename__ = "assessment_item"
    __table_args__ = (UniqueConstraint("assessment_id", "service_id", "control_id"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    assessment_id: Mapped[int] = mapped_column(ForeignKey("assessment.id"))
    service_id: Mapped[int | None] = mapped_column(ForeignKey("service.id"), nullable=True)
    control_id: Mapped[str] = mapped_column(String(20))
    applicable: Mapped[bool] = mapped_column(Boolean, default=True)
    na_justification: Mapped[str] = mapped_column(Text, default="")
    grade: Mapped[int | None] = mapped_column(Integer, nullable=True)
    evidence_description: Mapped[str] = mapped_column(Text, default="")
    evidence_reference: Mapped[str] = mapped_column(String(300), default="")
    evidence_date: Mapped[date | None] = mapped_column(Date, nullable=True)


class ExceptionRow(Base):
    __tablename__ = "exception_record"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    assessment_id: Mapped[int] = mapped_column(ForeignKey("assessment.id"))
    service_id: Mapped[int] = mapped_column(ForeignKey("service.id"))
    rule: Mapped[str] = mapped_column(String(20), default="")
    gate: Mapped[str] = mapped_column(String(10), default="")
    service_asset_id: Mapped[int | None] = mapped_column(ForeignKey("service_asset.id"), nullable=True)
    control_id: Mapped[str | None] = mapped_column(String(20), nullable=True)
    description: Mapped[str] = mapped_column(Text, default="")
    owner: Mapped[str] = mapped_column(String(200), default="")
    treatment: Mapped[str] = mapped_column(String(30), default="")
    compensating_control: Mapped[str] = mapped_column(Text, default="")
    approved_by: Mapped[str] = mapped_column(String(200), default="")
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String(10), default="open")
    closure_evidence: Mapped[str] = mapped_column(Text, default="")
    service: Mapped[Service] = relationship()


class Exercise(Base):
    __tablename__ = "exercise"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    assessment_id: Mapped[int] = mapped_column(ForeignKey("assessment.id"))
    service_id: Mapped[int] = mapped_column(ForeignKey("service.id"))
    exercise_date: Mapped[date] = mapped_column(Date)
    kind: Mapped[str] = mapped_column(String(20), default="exercise")
    scenario: Mapped[str] = mapped_column(Text, default="")
    service: Mapped[Service] = relationship()
    checks: Mapped[list["ExerciseCheck"]] = relationship(
        cascade="all, delete-orphan", order_by="ExerciseCheck.check_no")
    conditions: Mapped[list["ExerciseCondition"]] = relationship(
        cascade="all, delete-orphan", order_by="ExerciseCondition.id")


class ExerciseCheck(Base):
    __tablename__ = "exercise_check"
    __table_args__ = (UniqueConstraint("exercise_id", "check_no"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    exercise_id: Mapped[int] = mapped_column(ForeignKey("exercise.id"))
    check_no: Mapped[str] = mapped_column(String(5))
    result: Mapped[str | None] = mapped_column(String(5), nullable=True)
    evidence_reference: Mapped[str] = mapped_column(String(300), default="")


class ExerciseCondition(Base):
    __tablename__ = "exercise_condition"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    exercise_id: Mapped[int] = mapped_column(ForeignKey("exercise.id"))
    text: Mapped[str] = mapped_column(Text)
    owner: Mapped[str] = mapped_column(String(200), default="")
    expiry_date: Mapped[date | None] = mapped_column(Date, nullable=True)
