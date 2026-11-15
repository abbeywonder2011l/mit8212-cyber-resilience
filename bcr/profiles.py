"""Build synthetic assessment profiles (B0, SC1-SC5, DEMO) from the seed files.

All data is fictional. A profile is the reference state B0 plus the changes
listed for it in data/seed/profiles.json. This module does not touch the
database, so the engine can be tested against profiles directly.
"""
from __future__ import annotations

import json
from datetime import date, timedelta
from pathlib import Path

from bcr.engine.models import (
    AssessmentInput, Dependency, ExceptionRecord, Item, Risk, Service,
)
from bcr.engine.resumption import CHECK_NUMBERS, ResumptionCondition
from bcr.library import ROOT, Library

SEED_DIR = ROOT / "data" / "seed"


def _load(name: str, seed_dir: Path = SEED_DIR) -> dict:
    return json.loads((seed_dir / name).read_text(encoding="utf-8"))


def profile_names(seed_dir: Path = SEED_DIR) -> dict[str, str]:
    """Profile key -> title."""
    return {k: v["title"] for k, v in _load("profiles.json", seed_dir)["profiles"].items()}


def _merged_changes(profiles: dict, name: str) -> dict:
    """Resolve 'extends' by concatenating list changes, parent first."""
    spec = profiles[name]
    merged: dict = {}
    if spec.get("extends"):
        merged = _merged_changes(profiles, spec["extends"])
    out = {k: list(v) for k, v in merged.items() if isinstance(v, list)}
    for key in ("items", "service_assets", "risks", "exceptions", "exercises"):
        out[key] = out.get(key, []) + list(spec.get(key, []))
    if "validity_days" in spec:
        out["validity_days"] = spec["validity_days"]
    elif "validity_days" in merged:
        out["validity_days"] = merged["validity_days"]
    return out


def build_profile(name: str, lib: Library, seed_dir: Path = SEED_DIR) -> dict:
    """Return a complete, database-independent snapshot of one profile."""
    bank = _load("bank_x.json", seed_dir)
    pf = _load("profiles.json", seed_dir)
    if name not in pf["profiles"]:
        raise KeyError(f"Unknown profile '{name}'")
    spec = pf["profiles"][name]
    changes = _merged_changes(pf["profiles"], name)
    assessment_date = date.fromisoformat(pf["assessment_date"])
    validity_days = changes.get("validity_days", pf["validity_days"])
    test_date = assessment_date - timedelta(days=pf["baseline_test_days_ago"])

    services = [dict(s) for s in bank["services"]]
    assets = []
    service_assets = []
    for a in bank["assets"]:
        a = dict(a)
        used_by = a.pop("used_by")
        a.setdefault("is_third_party", False)
        a.setdefault("provider", "")
        assets.append(a)
        for code in used_by:
            service_assets.append({
                "service": code, "asset": a["code"],
                "single_point_of_failure": False, "tested_alternative": True,
                "recovery_coordination_tested": True, "note": "",
            })
    for change in changes["service_assets"]:
        for sa in service_assets:
            if sa["service"] == change["service"] and sa["asset"] == change["asset"]:
                sa.update({k: v for k, v in change.items() if k not in ("service", "asset")})
                break
        else:
            raise KeyError(f"{name}: no dependency {change['service']} -> {change['asset']}")

    risks = [dict(r) for r in bank["risks"]] + [dict(r) for r in changes["risks"]]

    # Reference state: every control at target, with evidence.
    items: dict[tuple, dict] = {}
    for control in lib.controls:
        codes = [None] if control.scope == "organisation" else [s["code"] for s in services]
        for code in codes:
            items[(code, control.id)] = {
                "service": code, "control": control.id, "applicable": True, "na_justification": "",
                "grade": control.target,
                "evidence_reference": f"EV-{control.id}-{code or 'ORG'}",
                "evidence_date": test_date if control.target == 4 else None,
                "evidence_description": "Fictional evidence record.",
            }
    for change in changes["items"]:
        key = (change["service"], change["control"])
        if key not in items:
            raise KeyError(f"{name}: no item for {key}")
        item = items[key]
        for field, value in change.items():
            if field in ("service", "control"):
                continue
            if field == "evidence_days_ago":
                item["evidence_date"] = assessment_date - timedelta(days=value)
            elif field == "evidence_date":
                item["evidence_date"] = date.fromisoformat(value) if value else None
            else:
                item[field] = value

    exceptions = []
    for e in changes["exceptions"]:
        e = dict(e)
        due = e.pop("due_in_days", None)
        e["due_date"] = assessment_date + timedelta(days=due) if due is not None else None
        e.setdefault("asset", None)
        e.setdefault("control", None)
        e.setdefault("closure_evidence", "")
        exceptions.append(e)

    exercises = []
    for x in changes["exercises"]:
        default = x["results"].get("default")
        results = {n: x["results"].get(n, default) for n in CHECK_NUMBERS}
        exercise_date = assessment_date - timedelta(days=x.get("days_ago", 0))
        exercises.append({
            "service": x["service"], "exercise_date": exercise_date, "kind": x["kind"],
            "scenario": x["scenario"], "results": results,
            "conditions": [
                {"text": c["text"], "owner": c["owner"],
                 "expiry_date": exercise_date + timedelta(days=c["expiry_in_days"])}
                for c in x.get("conditions", [])
            ],
        })

    return {
        "name": name, "title": spec["title"], "description": spec.get("description", ""),
        "notice": bank["notice"], "organisation": dict(bank["organisation"]),
        "assessment": {
            "name": spec["title"], "assessment_date": assessment_date,
            "assessor": "Synthetic data (no human assessor)", "validity_days": validity_days,
            "library_version": lib.version,
        },
        "services": services, "assets": assets, "service_assets": service_assets,
        "risks": risks, "items": list(items.values()), "exceptions": exceptions,
        "exercises": exercises,
    }


def dependency_key(service: str, asset: str) -> str:
    return f"{service}>{asset}"


def profile_to_input(profile: dict, lib: Library) -> AssessmentInput:
    """Convert a profile snapshot straight into engine input (no database)."""
    asset_by_code = {a["code"]: a for a in profile["assets"]}
    services = [
        Service(
            code=s["code"], name=s["name"], criticality=s["criticality"],
            business_owner=s.get("business_owner", ""), technical_owner=s.get("technical_owner", ""),
            mtd_hours=s.get("mtd_hours"), rto_hours=s.get("rto_hours"), rpo_minutes=s.get("rpo_minutes"),
            requirements_approved=s.get("requirements_approved", False),
            depends_on=tuple(s.get("depends_on", [])),
        )
        for s in profile["services"]
    ]
    dependencies = [
        Dependency(
            id=dependency_key(sa["service"], sa["asset"]), service_code=sa["service"],
            asset_code=sa["asset"], asset_name=asset_by_code[sa["asset"]]["name"],
            is_third_party=asset_by_code[sa["asset"]].get("is_third_party", False),
            single_point_of_failure=sa["single_point_of_failure"],
            tested_alternative=sa["tested_alternative"],
            recovery_coordination_tested=sa["recovery_coordination_tested"],
        )
        for sa in profile["service_assets"]
    ]
    risks = [
        Risk(service_code=r["service"], title=r["title"], likelihood=r["likelihood"], impact=r["impact"],
             category=r.get("category", ""),
             affects_recovery_environment=r.get("affects_recovery_environment", False))
        for r in profile["risks"]
    ]
    items = [
        Item(service_code=i["service"], control_id=i["control"], applicable=i["applicable"],
             na_justification=i["na_justification"], grade=i["grade"],
             evidence_reference=i["evidence_reference"], evidence_date=i["evidence_date"],
             evidence_description=i["evidence_description"])
        for i in profile["items"]
    ]
    exceptions = [
        ExceptionRecord(
            id=n, service_code=e["service"], gate=e.get("gate", ""), rule=e.get("rule", ""),
            dependency_id=dependency_key(e["service"], e["asset"]) if e.get("asset") else None,
            control_id=e.get("control"), description=e.get("description", ""), owner=e.get("owner", ""),
            treatment=e.get("treatment", ""), compensating_control=e.get("compensating_control", ""),
            approved_by=e.get("approved_by", ""), due_date=e.get("due_date"),
            status=e.get("status", "open"), closure_evidence=e.get("closure_evidence", ""),
        )
        for n, e in enumerate(profile["exceptions"], 1)
    ]
    a = profile["assessment"]
    return AssessmentInput(
        assessment_date=a["assessment_date"], validity_days=a["validity_days"],
        controls=lib.controls, services=services, dependencies=dependencies,
        risks=risks, items=items, exceptions=exceptions,
    )


def exercise_conditions(exercise: dict) -> list[ResumptionCondition]:
    return [ResumptionCondition(c["text"], c["owner"], c["expiry_date"]) for c in exercise["conditions"]]
