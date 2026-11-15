"""Load and validate the control library (data/control_library.json).

The JSON file is the single source of truth for the control catalogue.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_PATH = ROOT / "data" / "control_library.json"

VALID_GATES = (None, "G2", "G4", "G5", "G6")
VALID_BASIS_PARTS = {"Reg", "Std", "Des"}


class LibraryError(ValueError):
    """Raised when the control library fails validation."""

    def __init__(self, errors: list[str]):
        super().__init__("Control library failed validation: " + "; ".join(errors))
        self.errors = errors


@dataclass(frozen=True)
class Control:
    id: str
    domain: str
    scope: str  # "organisation" or "service"
    basis: str
    weight: int
    target: int
    gate: str | None
    title: str
    question: str
    evidence: tuple[str, ...]
    refs: dict
    rules: tuple[str, ...]
    rationale: str
    remediation: str


@dataclass(frozen=True)
class Library:
    version: str
    date: str
    note: str
    domains: dict
    references: dict
    basis_codes: dict
    status_codes: dict
    controls: tuple[Control, ...]

    def control(self, control_id: str) -> Control:
        for c in self.controls:
            if c.id == control_id:
                return c
        raise KeyError(control_id)

    def ids(self) -> list[str]:
        return [c.id for c in self.controls]


def validate_library(raw: dict) -> list[str]:
    """Return a list of problems; an empty list means the library is valid."""
    errors: list[str] = []
    for key in ("library_version", "domains", "references", "controls"):
        if key not in raw:
            errors.append(f"missing top-level key '{key}'")
    if errors:
        return errors
    seen: set[str] = set()
    for c in raw["controls"]:
        cid = c.get("id", "?")
        if cid in seen:
            errors.append(f"{cid}: duplicate id")
        seen.add(cid)
        if c.get("domain") not in raw["domains"]:
            errors.append(f"{cid}: unknown domain {c.get('domain')}")
        elif not cid.startswith(c["domain"] + "-"):
            errors.append(f"{cid}: id does not match domain {c['domain']}")
        if c.get("scope") not in ("organisation", "service"):
            errors.append(f"{cid}: bad scope {c.get('scope')}")
        if c.get("weight") not in (1, 2):
            errors.append(f"{cid}: weight must be 1 or 2")
        if c.get("target") not in (3, 4):
            errors.append(f"{cid}: target must be 3 or 4")
        if c.get("gate") not in VALID_GATES:
            errors.append(f"{cid}: unknown gate {c.get('gate')}")
        basis_parts = set(str(c.get("basis", "")).split("+"))
        if not basis_parts <= VALID_BASIS_PARTS:
            errors.append(f"{cid}: bad basis {c.get('basis')}")
        refs = c.get("refs", {})
        if "Reg" in basis_parts and not refs.get("CBN"):
            errors.append(f"{cid}: basis includes Reg but no CBN reference is given")
        for field in ("title", "question", "rationale", "remediation"):
            if not str(c.get(field, "")).strip():
                errors.append(f"{cid}: empty {field}")
        if not c.get("evidence"):
            errors.append(f"{cid}: no expected evidence")
        for fw, ids in refs.items():
            if fw not in raw["references"]:
                errors.append(f"{cid}: unknown framework {fw}")
                continue
            for rid in ids:
                if rid not in raw["references"][fw]:
                    errors.append(f"{cid}: {fw} reference '{rid}' is not in the reference register")
        if not any(refs.values()):
            errors.append(f"{cid}: no reference to any source framework")
    return errors


def parse_library(raw: dict) -> Library:
    errors = validate_library(raw)
    if errors:
        raise LibraryError(errors)
    controls = tuple(
        Control(
            id=c["id"], domain=c["domain"], scope=c["scope"], basis=c["basis"],
            weight=c["weight"], target=c["target"], gate=c["gate"], title=c["title"],
            question=c["question"], evidence=tuple(c["evidence"]), refs=c["refs"],
            rules=tuple(c["rules"]), rationale=c["rationale"], remediation=c["remediation"],
        )
        for c in raw["controls"]
    )
    return Library(
        version=raw["library_version"], date=raw.get("date", ""), note=raw.get("note", ""),
        domains=raw["domains"], references=raw["references"],
        basis_codes=raw.get("basis_codes", {}), status_codes=raw.get("status_codes", {}),
        controls=controls,
    )


def load_library(path: Path | str = DEFAULT_PATH) -> Library:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    return parse_library(raw)


def reference_label(lib: Library, framework: str, ref_id: str) -> str:
    """'A.8.13 [S]' style label; primary-verified references carry no mark."""
    status = lib.references[framework][ref_id]["status"]
    return ref_id if status == "P" else f"{ref_id} [{status}]"
