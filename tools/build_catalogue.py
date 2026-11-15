"""Validate data/control_library.json and generate docs/03-control-catalogue.md.

Run from the project root:  python tools/build_catalogue.py
The JSON file is the single source of truth; the Markdown file is generated.
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "data" / "control_library.json"
OUT = ROOT / "docs" / "03-control-catalogue.md"

FRAMEWORK_LABELS = {
    "CBN": "CBN (2024)",
    "CSF": "NIST CSF 2.0",
    "ISO27001": "ISO/IEC 27001:2022 Annex A",
    "ISO22301": "ISO 22301:2019",
    "COBIT": "COBIT 2019",
    "SP80034": "NIST SP 800-34 Rev. 1",
}

sys.path.insert(0, str(ROOT))
from bcr.library import validate_library as validate  # noqa: E402  (one validator, shared with the app)


def used_refs(lib: dict) -> dict[str, set[str]]:
    used: dict[str, set[str]] = {fw: set() for fw in lib["references"]}
    for c in lib["controls"]:
        for fw, ids in c["refs"].items():
            used[fw].update(ids)
    return used


def ref_str(lib: dict, fw: str, ids: list[str]) -> str:
    if not ids:
        return "none identified"
    parts = []
    for rid in ids:
        status = lib["references"][fw][rid]["status"]
        mark = "" if status == "P" else f" [{status}]"
        parts.append(f"{rid}{mark}")
    return "; ".join(parts)


def build(lib: dict) -> str:
    controls = lib["controls"]
    L: list[str] = []
    L.append("# Control Catalogue")
    L.append("")
    L.append("> Generated from `data/control_library.json` by `tools/build_catalogue.py`. "
             "Edit the JSON file, not this file.")
    L.append("")
    L.append(f"**Library version:** {lib['library_version']} ({lib['date']})")
    L.append("")
    L.append(lib["note"])
    L.append("")
    L.append("## Summary")
    L.append("")
    by_domain = Counter(c["domain"] for c in controls)
    by_basis = Counter(c["basis"] for c in controls)
    L.append(f"- Controls: **{len(controls)}** in {len(lib['domains'])} domains "
             f"({sum(1 for c in controls if c['scope'] == 'organisation')} assessed once for the organisation, "
             f"{sum(1 for c in controls if c['scope'] == 'service')} assessed for each service).")
    L.append(f"- Gate conditions: **{sum(1 for c in controls if c['gate'])}** controls. "
             f"Weight 2: **{sum(1 for c in controls if c['weight'] == 2)}** controls. "
             f"Target grade 4 (demonstrated by test): **{sum(1 for c in controls if c['target'] == 4)}** controls.")
    L.append("- Basis: " + ", ".join(f"{k} = {v}" for k, v in sorted(by_basis.items())) + ".")
    no_cbn = [c["id"] for c in controls if not c["refs"]["CBN"]]
    L.append(f"- Controls with no CBN requirement identified in the text read: {', '.join(no_cbn) or 'none'}.")
    L.append("")
    L.append("| Domain | Controls |")
    L.append("|---|---:|")
    for d, name in lib["domains"].items():
        L.append(f"| {d} {name} | {by_domain.get(d, 0)} |")
    L.append("")
    L.append("**Basis codes:** " + "; ".join(f"{k} = {v}" for k, v in lib["basis_codes"].items()) + ".")
    L.append("")
    L.append("**Reference status:** unmarked = " + lib["status_codes"]["P"].lower()
             + "; [S] = " + lib["status_codes"]["S"].lower()
             + "; [U] = " + lib["status_codes"]["U"].lower() + ".")
    L.append("")
    L.append("## Mapping overview")
    L.append("")
    L.append("| ID | Control | Basis | Wt | Target | Gate | CBN (2024) | CSF 2.0 | ISO 27001 | ISO 22301 | COBIT 2019 |")
    L.append("|---|---|---|---:|---:|---|---|---|---|---|---|")
    for c in controls:
        r = c["refs"]
        L.append(
            f"| {c['id']} | {c['title']} | {c['basis']} | {c['weight']} | {c['target']} | {c['gate'] or ''} | "
            f"{ref_str(lib, 'CBN', r['CBN'])} | {ref_str(lib, 'CSF', r['CSF'])} | "
            f"{ref_str(lib, 'ISO27001', r['ISO27001']) if r['ISO27001'] else ''} | "
            f"{ref_str(lib, 'ISO22301', r['ISO22301']) if r['ISO22301'] else ''} | "
            f"{ref_str(lib, 'COBIT', r['COBIT']) if r['COBIT'] else ''} |"
        )
    L.append("")
    L.append("## Control details")
    for d, name in lib["domains"].items():
        L.append("")
        L.append(f"### {d}: {name}")
        for c in (x for x in controls if x["domain"] == d):
            L.append("")
            L.append(f"#### {c['id']} {c['title']}")
            L.append("")
            scope = "once for the organisation" if c["scope"] == "organisation" else "for each service"
            rules = ", ".join(c["rules"]) if c["rules"] else "none"
            L.append(f"- **Assessed:** {scope}. **Basis:** {c['basis']}. **Weight:** {c['weight']}. "
                     f"**Target grade:** {c['target']}. **Decision rules:** {rules}. "
                     f"**Gate:** {c['gate'] or 'none'}.")
            L.append(f"- **Assessment question:** {c['question']}")
            L.append("- **Expected evidence:** " + "; ".join(c["evidence"]) + ".")
            for fw, label in FRAMEWORK_LABELS.items():
                if c["refs"][fw] or fw == "CBN":
                    L.append(f"- **{label}:** {ref_str(lib, fw, c['refs'][fw])}")
            L.append(f"- **Mapping rationale:** {c['rationale']}")
            L.append(f"- **Remediation guidance:** {c['remediation']}")
    L.append("")
    L.append("## Reference register")
    L.append("")
    L.append("Only references used by at least one control are listed. CBN entries are the researcher's "
             "paraphrases. NIST CSF entries are quoted from the published text, which NIST makes freely "
             "available. ISO and COBIT entries give short titles only.")
    used = used_refs(lib)
    for fw, label in FRAMEWORK_LABELS.items():
        L.append("")
        L.append(f"### {label}")
        L.append("")
        L.append("| Reference | Text | Status |")
        L.append("|---|---|---|")
        for rid, entry in lib["references"][fw].items():
            if rid in used[fw]:
                L.append(f"| {rid} | {entry['text']} | {entry['status']} |")
    L.append("")
    return "\n".join(L)


def main() -> int:
    lib = json.loads(SRC.read_text(encoding="utf-8"))
    errors = validate(lib)
    if errors:
        print("VALIDATION FAILED")
        for e in errors:
            print(" -", e)
        return 1
    unused = {fw: sorted(set(lib["references"][fw]) - ids) for fw, ids in used_refs(lib).items()}
    OUT.write_text(build(lib), encoding="utf-8")
    counts = Counter(lib["references"][fw][rid]["status"]
                     for fw, ids in used_refs(lib).items() for rid in ids)
    print(f"OK: {len(lib['controls'])} controls validated; wrote {OUT.relative_to(ROOT)}")
    print("reference status (used):", dict(sorted(counts.items())))
    print("unused register entries:", {k: v for k, v in unused.items() if v} or "none")
    return 0


if __name__ == "__main__":
    sys.exit(main())
