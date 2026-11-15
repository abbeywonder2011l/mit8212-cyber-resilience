"""Assessment report: self-contained HTML plus CSV extracts.

The report carries no generation timestamp, so the same assessment always
produces byte-identical output.
"""
from __future__ import annotations

import csv
import hashlib
import io
from dataclasses import dataclass, field
from html import escape

from bcr.engine import GATES, ORG, AssessmentInput, AssessmentResult, assess, pct, sensitivity
from bcr.engine.gates import GATE_RULES, exception_is_overdue, exception_is_valid
from bcr.engine.grades import GRADE_LABELS, lookup
from bcr.engine.resumption import CHECKS
from bcr.engine.scoring import SCHEMES
from bcr.library import Library

LIMITATIONS = (
    "This is an academic prototype. It is not a compliance assessment, a certification result or a "
    "substitute for regulatory supervision.",
    "The score is a researcher-developed measure. It is not a NIST CSF Tier and not the maturity level "
    "produced by the CBN Cybersecurity Self-Assessment Tool.",
    "Grades, weights, targets, gates and the priority rule are design assumptions that have not been "
    "reviewed by practitioners or validated in a bank.",
    "Inputs are self-declared. The tool checks that evidence is referenced and dated, not that it is true.",
    "Averaging grades and multiplying risk scales treats ordinal values as numbers. Read the score "
    "together with coverage, the demonstrated share, the grade distribution and the gate results.",
    "ISO and COBIT references are identifiers and short titles from secondary sources; some remain "
    "unverified and are marked in the control catalogue.",
)

RESULT_LABELS = {"PASS": "Pass", "PASS_WITH_EXCEPTION": "Pass (exception)", "FAIL": "Fail"}
ANSWER_LABELS = {"yes": "Yes", "no": "No", "na": "Not applicable", None: "Unanswered"}


@dataclass
class ReportData:
    organisation: str
    notice: str
    assessment_name: str
    assessor: str
    library_version: str
    inp: AssessmentInput
    result: AssessmentResult
    lib: Library
    exercises: list = field(default_factory=list)  # dicts: service, date, kind, scenario, results, conditions, decision, reasons
    asset_notes: dict = field(default_factory=dict)  # dependency id -> note


def _t(value) -> str:
    return escape("" if value is None else str(value))


def _num(value) -> str:
    """Format a number the same way whether it arrived as 4 or 4.0."""
    return "not recorded" if value is None else f"{float(value):g}"


def _table(headers: list[str], rows: list[list], classes: str = "") -> str:
    head = "".join(f"<th>{_t(h)}</th>" for h in headers)
    body = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in row) + "</tr>" for row in rows)
    if not rows:
        body = f'<tr><td colspan="{len(headers)}"><em>None</em></td></tr>'
    return f'<table class="{classes}"><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>'


def _status_badge(status: str) -> str:
    cls = {"Ready": "ok", "Ready with accepted exceptions": "warn"}.get(status, "bad")
    return f'<span class="badge {cls}">{_t(status)}</span>'


def _gate_cell(result: str) -> str:
    cls = {"PASS": "ok", "PASS_WITH_EXCEPTION": "warn", "FAIL": "bad"}[result]
    return f'<span class="badge {cls}">{_t(RESULT_LABELS[result])}</span>'


def tool1_rows(inp: AssessmentInput, res: AssessmentResult, service_code: str) -> list[tuple[str, str]]:
    """Tool 1 (paper Table 4.4) for one service, as plain (field, entry) pairs."""
    s = inp.service(service_code)
    deps = [x for x in inp.dependencies if x.service_code == s.code]
    dep_text = "; ".join(
        f"{x.asset_code} {x.asset_name}"
        + (" [UNRESOLVED: " + "; ".join(x.unresolved_reasons) + "]" if x.unresolved_reasons else "")
        for x in deps) or "None recorded"
    risks = "; ".join(f"{r.title} ({r.band}, {r.rating})"
                      for r in inp.risks if r.service_code == s.code) or "None recorded"
    approved = "approved" if s.requirements_approved else "NOT approved"
    gate_controls = [c for c in inp.controls if c.gate]

    def grade(c) -> str:
        value = lookup(res.effective, s.code, c).value
        return "n/a" if value is None else str(value)

    controls = "; ".join(f"{c.id} grade {grade(c)} (needs {c.target})" for c in gate_controls)
    failed = "; ".join(f"{g}: {c.detail}" for g in GATES
                       for c in res.readiness[s.code].gates[g].failed) or "None"
    return [
        ("Service name", f"{s.code} {s.name}"),
        ("Business owner", s.business_owner or "not named"),
        ("Technical owner", s.technical_owner or "not named"),
        ("Depends on services", ", ".join(s.depends_on) or "None"),
        ("Dependencies", dep_text),
        ("Disruption scenarios", risks),
        ("Recovery objectives", f"Maximum tolerable downtime {_num(s.mtd_hours)} h; "
                                f"RTO {_num(s.rto_hours)} h; RPO {_num(s.rpo_minutes)} min ({approved})"),
        ("Gate controls (effective grade)", controls),
        ("Acceptance criteria not yet met", failed),
    ]


CSS = """
body{font-family:Segoe UI,Arial,sans-serif;color:#1c2430;margin:32px auto;max-width:1100px;padding:0 16px;line-height:1.45}
h1{font-size:24px;margin-bottom:4px} h2{font-size:18px;margin-top:32px;border-bottom:2px solid #d5dbe3;padding-bottom:4px}
h3{font-size:15px;margin-top:20px} table{border-collapse:collapse;width:100%;margin:8px 0 16px;font-size:13px}
th,td{border:1px solid #d5dbe3;padding:5px 8px;text-align:left;vertical-align:top} th{background:#eef2f6}
.notice{background:#fff4d6;border:1px solid #e0b84a;padding:10px 14px;margin:12px 0;font-size:14px}
.meta{font-size:13px;color:#4a5665} .badge{padding:1px 8px;border-radius:10px;font-size:12px;white-space:nowrap}
.ok{background:#d9f2e1;color:#14532d}.warn{background:#fdecc8;color:#7a4b00}.bad{background:#f9d6d5;color:#7f1d1d}
.kpi{display:flex;gap:12px;flex-wrap:wrap}.kpi div{border:1px solid #d5dbe3;padding:10px 14px;min-width:150px}
.kpi b{display:block;font-size:20px} ul{margin-top:4px}
"""


def render_html(d: ReportData) -> str:
    inp, res, lib = d.inp, d.result, d.lib
    scheme = SCHEMES[res.scheme]
    by_id = {c.id: c for c in lib.controls}
    parts: list[str] = []
    add = parts.append

    add(f"<h1>Cyber-Resilience Assessment Report</h1>"
        f'<div class="meta">{_t(d.organisation)} &middot; {_t(d.assessment_name)}</div>')
    add(f'<div class="notice"><b>Fictional data.</b> {_t(d.notice)}</div>')
    add(_table(["Assessment date", "Assessor", "Control library", "Validity period", "Weighting scheme"],
               [[_t(inp.assessment_date.isoformat()), _t(d.assessor), _t(d.library_version),
                 f"{inp.validity_days} days", _t(f"{scheme.key}: {scheme.name}")]]))

    # 1 Summary
    p = res.scores.profile
    ready = sum(1 for r in res.readiness.values() if r.status != "Not demonstrated")
    add("<h2>1. Summary</h2>")
    add('<div class="kpi">'
        f"<div>Overall score<b>{pct(res.scores.overall)}</b></div>"
        f"<div>Coverage<b>{pct(p.coverage)}</b></div>"
        f"<div>Demonstrated by test<b>{pct(p.demonstrated_share)}</b></div>"
        f"<div>Services ready<b>{ready} of {len(inp.services)}</b></div>"
        f"<div>Open actions<b>{len(res.actions)}</b></div></div>")
    add("<p>The readiness status comes from pass/fail gates and does not depend on the score or on any "
        "weighting. A high score cannot compensate for a failed gate.</p>")

    # 2 Services
    add("<h2>2. Readiness by service</h2>")
    rows = []
    for s in inp.services:
        r, sc = res.readiness[s.code], res.scores.services[s.code]
        rows.append([_t(s.code), _t(s.name), s.criticality, pct(sc.score), pct(sc.profile.coverage),
                     pct(sc.profile.demonstrated_share), _status_badge(r.status)]
                    + [_gate_cell(r.gates[g].result) for g in GATES])
    add(_table(["Code", "Service", "Criticality", "Score", "Coverage", "Demonstrated", "Status"] + list(GATES), rows))
    add("<p class='meta'>" + "; ".join(f"{g} = {GATE_RULES[g][1]} ({GATE_RULES[g][0]})" for g in GATES) + ".</p>")
    rows = []
    for s in inp.services:
        for g in GATES:
            for c in res.readiness[s.code].gates[g].conditions:
                if not c.met:
                    state = "Waived by exception" if c.waived else "Not met"
                    rows.append([_t(s.code), g, _t(c.ref), state, _t(c.detail)])
    add("<h3>Gate conditions not met</h3>")
    add(_table(["Service", "Gate", "Condition", "State", "Detail"], rows))

    # 3 Domain scores
    add("<h2>3. Scores by control domain</h2>")
    rows = [[_t(f"{dom} {name}")] + [pct(res.scores.services[s.code].domain_scores.get(dom)) for s in inp.services]
            for dom, name in lib.domains.items()]
    add(_table(["Domain"] + [s.code for s in inp.services], rows))
    add("<h3>Grade distribution (all assessed controls)</h3>")
    add(_table(["Grade", "Meaning", "Controls"],
               [[g, _t(GRADE_LABELS[g]), p.distribution[g]] for g in range(5)]))

    # 4 Risk
    add("<h2>4. Risk register</h2>")
    rows = [[_t(r.service_code), _t(r.title), _t(r.category), r.likelihood, r.impact, r.rating, _t(r.band),
             "Yes" if r.affects_recovery_environment else "No"]
            for r in sorted(inp.risks, key=lambda r: (-r.rating, r.service_code, r.title))]
    add(_table(["Service", "Threat scenario", "Category", "Likelihood", "Impact", "Rating", "Band",
                "Affects recovery environment"], rows))

    # 5 Actions
    add("<h2>5. Gap analysis and remediation plan</h2>")
    add("<p>Tier P1 = a condition of a failed gate; P2 = other gaps on weight-2 controls or gaps of two "
        "grades or more; P3 = remaining gaps. Within a tier, actions are ordered by gap &times; control "
        "weight &times; service criticality &times; risk factor.</p>")
    rows = [[n, a.tier, _t(a.service_code), _t(a.ref), _t(a.title), _t(a.action_type),
             "" if a.current is None else a.current, "" if a.target is None else a.target,
             _t(a.gate), _t(a.rules), f"{a.priority:.2f}", _t(a.detail), _t(a.expected_evidence)]
            for n, a in enumerate(res.actions, 1)]
    add(_table(["#", "Tier", "Service", "Ref", "Item", "Action", "Current", "Target", "Gate", "Rules",
                "Priority", "Detail", "Expected evidence"], rows))

    # 6 Exceptions
    add("<h2>6. Exception register</h2>")
    rows = []
    dep_code = {x.id: x.asset_code for x in inp.dependencies}
    for e in inp.exceptions:
        if e.status == "closed":
            state = "Closed"
        elif exception_is_overdue(e, inp.assessment_date):
            state = "Overdue: no longer waives a gate"
        elif exception_is_valid(e, inp.assessment_date):
            state = "Open and approved"
        else:
            state = "Open, not approved"
        rows.append([_t(e.service_code), _t(e.gate), _t(e.rule), _t(e.control_id or dep_code.get(e.dependency_id, "")),
                     _t(e.description), _t(e.owner), _t(e.treatment.replace("_", " ")),
                     _t(e.compensating_control), _t(e.approved_by),
                     _t(e.due_date.isoformat() if e.due_date else ""), _t(state)])
    add(_table(["Service", "Gate", "Rule", "Relates to", "Description", "Owner", "Treatment",
                "Compensating control", "Approved by", "Due", "State"], rows))

    # 7 Tool 1
    add("<h2>7. Tool 1: service dependency and recovery planning matrix</h2>")
    for s in inp.services:
        add(f"<h3>{_t(s.code)} {_t(s.name)}</h3>")
        rows = [[_t(k), _t(v)] for k, v in tool1_rows(inp, res, s.code)]
        rows.append(["Readiness status", _status_badge(res.readiness[s.code].status)])
        add(_table(["Field", "Entry"], rows))

    # 8 Tool 2
    add("<h2>8. Tool 2: resumption checklists</h2>")
    if not d.exercises:
        add("<p><em>No exercise or incident record.</em></p>")
    for x in d.exercises:
        add(f"<h3>{_t(x['service'])} &middot; {_t(x['date'])} &middot; {_t(x['kind'])}</h3>")
        add(f"<p>{_t(x['scenario'])}</p>")
        add(_table(["#", "Check", "Rule", "Result"],
                   [[n, _t(text), _t(rule), _t(ANSWER_LABELS[x['results'].get(n)])]
                    for n, _section, text, rule in CHECKS]))
        if x["conditions"]:
            add(_table(["Condition", "Owner", "Expiry"],
                       [[_t(c["text"]), _t(c["owner"]), _t(c["expiry_date"])] for c in x["conditions"]]))
        add(f"<p><b>Decision: {_t(x['decision'])}.</b> {_t('; '.join(x['reasons']))}</p>")

    # 9 Sensitivity
    add("<h2>9. Sensitivity to weighting</h2>")
    sens = sensitivity(inp)
    rows = []
    for key, v in sens.items():
        rows.append([_t(f"{key}: {v['name']}"), pct(v["overall"])]
                    + [pct(v["services"][s.code]) for s in inp.services]
                    + [_t(" > ".join(v["ranking"]))])
    add(_table(["Scheme", "Overall"] + [s.code for s in inp.services] + ["Ranking by score"], rows))
    same = len({tuple(sorted(v["status"].items())) for v in sens.values()}) == 1
    add(f"<p>Readiness status is {'identical' if same else 'NOT identical'} under all three schemes.</p>")

    # 10 Limitations
    add("<h2>10. Limitations</h2><ul>" + "".join(f"<li>{_t(x)}</li>" for x in LIMITATIONS) + "</ul>")

    body = "\n".join(parts)
    return (f"<!doctype html><html lang='en'><head><meta charset='utf-8'>"
            f"<title>Cyber-Resilience Assessment Report</title><style>{CSS}</style></head>"
            f"<body>{body}</body></html>")


def actions_csv(result: AssessmentResult) -> str:
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(["order", "tier", "service", "source", "ref", "item", "action", "current_grade",
                "target_grade", "gap", "gate", "rules", "priority", "detail", "expected_evidence", "risk_note"])
    for n, a in enumerate(result.actions, 1):
        w.writerow([n, a.tier, a.service_code, a.source, a.ref, a.title, a.action_type,
                    "" if a.current is None else a.current, "" if a.target is None else a.target,
                    a.gap, a.gate, a.rules, f"{a.priority:.4f}", a.detail, a.expected_evidence, a.risk_note])
    return buf.getvalue()


def gaps_csv(inp: AssessmentInput, result: AssessmentResult) -> str:
    """Every assessed control for every service, with recorded and effective grade."""
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(["service", "control", "domain", "title", "basis", "weight", "recorded_grade",
                "effective_grade", "target_grade", "gap", "assessed", "reason"])
    rows = []
    for (code, control_id), e in result.effective.items():
        c = next(x for x in inp.controls if x.id == control_id)
        gap = "" if e.value is None else max(0, c.target - e.value)
        rows.append([code or ORG, c.id, c.domain, c.title, c.basis, c.weight,
                     "" if e.recorded is None else e.recorded,
                     "n/a" if e.value is None else e.value, c.target, gap,
                     "yes" if e.assessed else "no", e.reason])
    for row in sorted(rows, key=lambda r: (r[0], r[1])):
        w.writerow(row)
    return buf.getvalue()


def content_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def report_from_profile(profile: dict, lib: Library, scheme: str = "A") -> ReportData:
    from bcr.engine.resumption import decide
    from bcr.profiles import exercise_conditions, profile_to_input
    inp = profile_to_input(profile, lib)
    exercises = []
    for x in profile["exercises"]:
        dec = decide(x["results"], exercise_conditions(x), x["exercise_date"])
        exercises.append({
            "service": x["service"], "date": x["exercise_date"].isoformat(), "kind": x["kind"],
            "scenario": x["scenario"], "results": x["results"],
            "conditions": [{"text": c["text"], "owner": c["owner"],
                            "expiry_date": c["expiry_date"].isoformat()} for c in x["conditions"]],
            "decision": dec.decision, "reasons": dec.reasons,
        })
    a = profile["assessment"]
    return ReportData(
        organisation=profile["organisation"]["name"], notice=profile["notice"],
        assessment_name=a["name"], assessor=a["assessor"], library_version=a["library_version"],
        inp=inp, result=assess(inp, scheme), lib=lib, exercises=exercises,
    )
