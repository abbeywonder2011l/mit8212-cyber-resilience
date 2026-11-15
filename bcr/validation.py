"""Input validation. Each function returns a list of plain-language errors
(empty when the input is valid). Invalid input never reaches the database.
"""
from __future__ import annotations

from datetime import date

ASSET_TYPES = (
    "Application server", "Database", "Network", "Firewall", "Security system",
    "Identity system", "Backup", "Data centre", "ATM or payment infrastructure",
    "Third-party connectivity", "Third-party service", "Other",
)
RISK_CATEGORIES = (
    "Cyberattack", "Infrastructure failure", "Site failure", "Connectivity",
    "Power", "Third-party dependency", "Data integrity", "Other",
)
TREATMENTS = ("remediation", "risk_acceptance")


class ValidationError(ValueError):
    def __init__(self, errors: list[str]):
        super().__init__("; ".join(errors))
        self.errors = errors


def _blank(value) -> bool:
    return value is None or not str(value).strip()


def _scale(value, name: str, errors: list[str]) -> None:
    if not isinstance(value, int) or isinstance(value, bool) or not 1 <= value <= 5:
        errors.append(f"{name} must be a whole number from 1 to 5.")


def _non_negative(value, name: str, errors: list[str]) -> None:
    if value is None:
        return
    try:
        if float(value) < 0:
            errors.append(f"{name} cannot be negative.")
    except (TypeError, ValueError):
        errors.append(f"{name} must be a number.")


def validate_service(d: dict) -> list[str]:
    errors: list[str] = []
    if _blank(d.get("code")):
        errors.append("Service code is required.")
    if _blank(d.get("name")):
        errors.append("Service name is required.")
    _scale(d.get("criticality"), "Criticality", errors)
    for field, label in (("mtd_hours", "Maximum tolerable downtime"), ("rto_hours", "RTO"),
                         ("rpo_minutes", "RPO")):
        _non_negative(d.get(field), label, errors)
    mtd, rto = d.get("mtd_hours"), d.get("rto_hours")
    if not errors and mtd is not None and rto is not None and float(rto) > float(mtd):
        errors.append("RTO cannot be greater than the maximum tolerable downtime.")
    if d.get("requirements_approved") and None in (mtd, rto, d.get("rpo_minutes")):
        errors.append("Recovery requirements cannot be marked approved until all three are recorded.")
    return errors


def validate_service_dependency(service_code: str, depends_on_code: str) -> list[str]:
    if service_code == depends_on_code:
        return ["A service cannot depend on itself."]
    return []


def validate_asset(d: dict) -> list[str]:
    errors: list[str] = []
    if _blank(d.get("code")):
        errors.append("Asset code is required.")
    if _blank(d.get("name")):
        errors.append("Asset name is required.")
    if d.get("type") not in ASSET_TYPES:
        errors.append("Asset type is not one of the listed types.")
    _scale(d.get("criticality"), "Criticality", errors)
    if d.get("is_third_party") and _blank(d.get("provider")):
        errors.append("A third-party asset needs a provider name.")
    return errors


def validate_risk(d: dict) -> list[str]:
    errors: list[str] = []
    if _blank(d.get("title")):
        errors.append("Risk title is required.")
    _scale(d.get("likelihood"), "Likelihood", errors)
    _scale(d.get("impact"), "Impact", errors)
    return errors


def validate_item(d: dict, assessment_date: date | None = None) -> tuple[list[str], list[str]]:
    """Return (errors, warnings). Warnings do not block saving: the engine
    applies the effective-grade rules and the assessor is told why."""
    errors: list[str] = []
    warnings: list[str] = []
    grade = d.get("grade")
    applicable = d.get("applicable", True)
    if grade is not None and (isinstance(grade, bool) or grade not in (0, 1, 2, 3, 4)):
        errors.append("Grade must be 0, 1, 2, 3 or 4.")
    if not applicable and _blank(d.get("na_justification")):
        errors.append("A control can be marked not applicable only with a written justification.")
    if errors or not applicable or grade is None:
        return errors, warnings
    if grade >= 3 and _blank(d.get("evidence_reference")):
        warnings.append("No evidence reference: this grade will count as 2.")
    if grade == 4 and d.get("evidence_date") is None:
        warnings.append("No test date: grade 4 will count as 3.")
    if (grade == 4 and d.get("evidence_date") is not None and assessment_date is not None
            and d["evidence_date"] > assessment_date):
        warnings.append("Test date is after the assessment date: grade 4 will count as 3.")
    return errors, warnings


def validate_assessment(d: dict) -> list[str]:
    errors: list[str] = []
    if _blank(d.get("name")):
        errors.append("Assessment name is required.")
    if d.get("assessment_date") is None:
        errors.append("Assessment date is required.")
    days = d.get("validity_days")
    if not isinstance(days, int) or isinstance(days, bool) or days < 1:
        errors.append("Validity period must be a whole number of days, at least 1.")
    return errors


def validate_exception(d: dict) -> list[str]:
    errors: list[str] = []
    if _blank(d.get("description")):
        errors.append("Exception description is required.")
    if _blank(d.get("owner")):
        errors.append("Exception owner is required.")
    if d.get("treatment") not in TREATMENTS:
        errors.append("Treatment must be remediation or risk acceptance.")
    if d.get("due_date") is None:
        errors.append("Due date is required.")
    if d.get("status", "open") == "closed" and _blank(d.get("closure_evidence")):
        errors.append("An exception cannot be closed without closure evidence.")
    return errors


def validate_exception_close(closure_evidence: str) -> list[str]:
    if _blank(closure_evidence):
        return ["An exception cannot be closed without closure evidence."]
    return []


def validate_exercise(d: dict) -> list[str]:
    errors: list[str] = []
    if d.get("exercise_date") is None:
        errors.append("Exercise date is required.")
    if d.get("kind") not in ("exercise", "incident"):
        errors.append("Kind must be exercise or incident.")
    if _blank(d.get("scenario")):
        errors.append("Scenario description is required.")
    return errors
