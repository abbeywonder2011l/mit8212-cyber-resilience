"""Modules 2, 3, 5 and 6: control library, assessment, gaps and remediation, exceptions."""
from __future__ import annotations

import streamlit as st

from app.common import Ctx, save, table
from bcr.data import repository as repo
from bcr.engine import ORG, exception_is_overdue, exception_is_valid
from bcr.engine.grades import GRADE_LABELS, lookup
from bcr.library import reference_label

FRAMEWORKS = {
    "CBN": "CBN (2024)", "CSF": "NIST CSF 2.0", "ISO27001": "ISO/IEC 27001:2022 Annex A",
    "ISO22301": "ISO 22301:2019", "COBIT": "COBIT 2019", "SP80034": "NIST SP 800-34 Rev. 1",
}
ORG_LABEL = "Organisation-level controls"


def library(ctx: Ctx) -> None:
    lib = ctx.lib
    st.header("Control library")
    st.caption(f"Version {lib.version} ({lib.date}). {lib.note}")
    st.info("The library is read-only here. It is maintained as a versioned file "
            "(data/control_library.json) so that every reference can be checked.")
    c1, c2 = st.columns(2)
    domains = c1.multiselect("Domain", list(lib.domains), format_func=lambda d: f"{d} {lib.domains[d]}")
    bases = c2.multiselect("Basis contains", ["Reg", "Std", "Des"])
    controls = [c for c in lib.controls
                if (not domains or c.domain in domains)
                and (not bases or any(b in c.basis.split("+") for b in bases))]
    table([{
        "ID": c.id, "Control": c.title, "Domain": lib.domains[c.domain],
        "Assessed": "Once" if c.scope == "organisation" else "Per service",
        "Basis": c.basis, "Weight": c.weight, "Target": c.target, "Gate": c.gate or "",
        "Rules": ", ".join(c.rules),
    } for c in controls])
    st.caption("Basis: " + "; ".join(f"{k} = {v}" for k, v in lib.basis_codes.items()))
    if not controls:
        return
    control_id = st.selectbox("Show details for", [c.id for c in controls],
                              format_func=lambda i: f"{i} {lib.control(i).title}")
    control = lib.control(control_id)
    st.subheader(f"{control.id} {control.title}")
    st.markdown(f"**Assessment question.** {control.question}")
    st.markdown("**Expected evidence.** " + "; ".join(control.evidence) + ".")
    st.markdown(f"**Mapping rationale.** {control.rationale}")
    refs = []
    for fw, label in FRAMEWORKS.items():
        for rid in control.refs.get(fw, []):
            entry = lib.references[fw][rid]
            refs.append({"Source": label, "Reference": rid, "Text": entry["text"],
                         "Verification": lib.status_codes.get(entry["status"], entry["status"])})
    table(refs)
    if not control.refs.get("CBN"):
        st.caption("No CBN requirement was identified in the text read for this control.")


def assessment(ctx: Ctx) -> None:
    s, lib, a = ctx.session, ctx.lib, ctx.assessment
    st.header("Resilience assessment")
    st.caption(f"{a.name} · assessment date {a.assessment_date.isoformat()} · validity period "
               f"{a.validity_days} days · library {a.library_version}")
    with st.expander("Evidence grades and the rules applied to them"):
        table([{"Grade": g, "Meaning": label} for g, label in GRADE_LABELS.items()])
        st.markdown(
            "- A grade of 3 or 4 with no evidence reference counts as 2.\n"
            "- A grade of 4 with no test date, or a test older than the validity period, counts as 3.\n"
            "- A control can be marked not applicable only with a written justification.\n"
            "- A control that is not assessed counts as 0.")
    services = repo.list_services(s)
    by_code = {r.code: r for r in services}
    picked = st.selectbox("Assess", [ORG_LABEL] + list(by_code),
                          format_func=lambda c: c if c == ORG_LABEL else f"{c} {by_code[c].name}")
    svc = by_code.get(picked)
    scope = "organisation" if svc is None else "service"
    controls = [c for c in lib.controls if c.scope == scope]
    items = repo.get_items(s, a.id)
    _, result = ctx.run()
    code = None if svc is None else svc.code

    rows = []
    for c in controls:
        item = items.get((svc.id if svc else None, c.id))
        e = result.effective.get((code, c.id))
        rows.append({
            "ID": c.id, "Control": c.title,
            "Recorded": "" if item is None or item.grade is None else item.grade,
            "Effective": "n/a" if e is None or e.value is None else e.value,
            "Target": c.target, "Rule applied": e.reason if e else "",
            "Evidence reference": item.evidence_reference if item else "",
            "Test date": item.evidence_date.isoformat() if item and item.evidence_date else "",
        })
    table(rows)

    st.subheader("Record or update one control")
    control_id = st.selectbox("Control", [c.id for c in controls],
                              format_func=lambda i: f"{i} {lib.control(i).title}")
    control = lib.control(control_id)
    item = items.get((svc.id if svc else None, control.id))
    st.markdown(f"**Question.** {control.question}")
    st.markdown("**Expected evidence.** " + "; ".join(control.evidence) + ".")
    k = f"item_{a.id}_{svc.id if svc else 0}_{control.id}_"
    grade_options = [None, 0, 1, 2, 3, 4]
    with st.form(k + "form"):
        applicable = st.checkbox("Applicable to this service", value=item.applicable if item else True, key=k + "app")
        justification = st.text_input("Justification if not applicable",
                                      value=item.na_justification if item else "", key=k + "why")
        grade = st.selectbox(
            "Evidence grade", grade_options,
            index=grade_options.index(item.grade) if item and item.grade in grade_options else 0,
            format_func=lambda g: "Not assessed" if g is None else f"{g}: {GRADE_LABELS[g]}", key=k + "grade")
        description = st.text_area("Evidence description", value=item.evidence_description if item else "", key=k + "desc")
        c1, c2 = st.columns(2)
        reference = c1.text_input("Evidence reference (document or record identifier)",
                                  value=item.evidence_reference if item else "", key=k + "ref")
        when = c2.date_input("Date of test or exercise (needed for grade 4)",
                             value=item.evidence_date if item else None, key=k + "date")
        submitted = st.form_submit_button("Save")
    if submitted:
        data = {"applicable": applicable, "na_justification": justification, "grade": grade,
                "evidence_description": description, "evidence_reference": reference, "evidence_date": when}
        save(lambda: repo.save_item(s, a.id, svc.id if svc else None, control.id, data, lib),
             f"{control.id} saved.")


def gaps(ctx: Ctx) -> None:
    st.header("Gap analysis and remediation plan")
    st.caption("P1 = a condition of a failed gate. P2 = other gaps on weight-2 controls or gaps of two grades "
               "or more. P3 = remaining gaps. Within a tier: gap x control weight x service criticality x risk factor.")
    inp, result = ctx.run()
    actions = result.actions
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Open actions", len(actions))
    for col, tier in ((c2, "P1"), (c3, "P2"), (c4, "P3")):
        col.metric(tier, sum(a.tier == tier for a in actions))
    c1, c2 = st.columns(2)
    codes = [ORG] + [x.code for x in inp.services]
    pick_services = c1.multiselect("Service", codes)
    pick_tiers = c2.multiselect("Tier", ["P1", "P2", "P3"])
    shown = [(n, a) for n, a in enumerate(actions, 1)
             if (not pick_services or a.service_code in pick_services)
             and (not pick_tiers or a.tier in pick_tiers)]
    table([{
        "#": n, "Tier": a.tier, "Service": a.service_code, "Ref": a.ref, "Item": a.title,
        "Action": a.action_type, "Current": "" if a.current is None else a.current,
        "Target": "" if a.target is None else a.target, "Gate": a.gate, "Rules": a.rules,
        "Priority": round(a.priority, 2), "Detail": a.detail, "Expected evidence": a.expected_evidence,
        "Risk basis": a.risk_note,
    } for n, a in shown])
    if not actions:
        st.success("No gaps against the target grades and no failed gate conditions.")

    with st.expander("All controls: recorded, effective and target grade"):
        rows = []
        for service in inp.services:
            for c in inp.controls:
                e = lookup(result.effective, service.code, c)
                rows.append({
                    "Service": ORG if c.scope == "organisation" else service.code, "ID": c.id,
                    "Control": c.title, "Recorded": "" if e.recorded is None else e.recorded,
                    "Effective": "n/a" if e.value is None else e.value, "Target": c.target,
                    "Gap": "" if e.value is None else max(0, c.target - e.value), "Rule applied": e.reason,
                })
        unique = {(r["Service"], r["ID"]): r for r in rows}
        table(list(unique.values()))


def exceptions(ctx: Ctx) -> None:
    s, a = ctx.session, ctx.assessment
    st.header("Exception register")
    st.caption("Decision rule DR10. An approved, in-date exception can waive an unresolved dependency (gate G3) "
               "or a shortfall on ACC-03 with a compensating control (gate G4). No other gate can be waived. "
               "An exception cannot be closed without closure evidence.")
    inp, _ = ctx.run()
    rows = repo.list_exceptions(s, a.id)
    links = {x.id: x for x in repo.list_service_assets(s)}
    engine_exc = {e.id: e for e in inp.exceptions}

    def state(row) -> str:
        e = engine_exc[row.id]
        if e.status == "closed":
            return "Closed"
        if exception_is_overdue(e, inp.assessment_date):
            return "OVERDUE: no longer waives a gate"
        return "Open and approved" if exception_is_valid(e, inp.assessment_date) else "Open, not approved"

    table([{
        "ID": r.id, "Service": r.service.code, "Gate": r.gate, "Rule": r.rule,
        "Relates to": r.control_id or (links[r.service_asset_id].asset.code if r.service_asset_id in links else ""),
        "Description": r.description, "Owner": r.owner, "Treatment": r.treatment.replace("_", " "),
        "Compensating control": r.compensating_control, "Approved by": r.approved_by,
        "Due": r.due_date.isoformat() if r.due_date else "", "State": state(r),
        "Closure evidence": r.closure_evidence,
    } for r in rows])

    services = repo.list_services(s)
    if not services:
        return
    st.subheader("Record an exception")
    c1, c2 = st.columns(2)
    by_code = {r.code: r for r in services}
    svc = by_code[c1.selectbox("Service", list(by_code), key="exc_svc")]
    kind = c2.selectbox("Relates to", ["A dependency (gate G3)", "Control ACC-03 (gate G4)", "Something else (no waiver)"],
                        key="exc_kind")
    svc_links = {x.id: x for x in links.values() if x.service_id == svc.id}
    link = None
    if kind.startswith("A dependency"):
        if not svc_links:
            st.info("This service has no recorded dependency.")
            return
        link = svc_links[st.selectbox(
            "Dependency", list(svc_links), key=f"exc_link_{svc.id}",
            format_func=lambda i: f"{svc_links[i].asset.code} {svc_links[i].asset.name}")]
    with st.form(f"exc_form_{svc.id}_{kind}"):
        description = st.text_area("Description")
        c1, c2 = st.columns(2)
        owner = c1.text_input("Owner")
        treatment = c2.selectbox("Treatment", ["risk_acceptance", "remediation"], format_func=lambda t: t.replace("_", " "))
        compensating = st.text_input("Compensating control")
        c1, c2 = st.columns(2)
        approved_by = c1.text_input("Approved by (leave blank if not yet approved)")
        due = c2.date_input("Due date", value=None)
        submitted = st.form_submit_button("Record exception")
    if submitted:
        data = {"description": description, "owner": owner, "treatment": treatment,
                "compensating_control": compensating, "approved_by": approved_by, "due_date": due,
                "status": "open"}
        if link is not None:
            data.update({"gate": "G3", "rule": "DR3", "service_asset_id": link.id})
        elif kind.startswith("Control"):
            data.update({"gate": "G4", "rule": "DR4", "control_id": "ACC-03"})
        else:
            data.update({"gate": "", "rule": "DR10"})
        save(lambda: repo.save_exception(s, a.id, svc.id, data), "Exception recorded.")

    open_rows = {r.id: r for r in rows if r.status == "open"}
    if open_rows:
        st.subheader("Close an exception")
        with st.form("exc_close"):
            target_id = st.selectbox(
                "Exception", list(open_rows),
                format_func=lambda i: f"{i}: {open_rows[i].service.code} {open_rows[i].description[:60]}")
            evidence = st.text_input("Closure evidence")
            submitted = st.form_submit_button("Close exception")
        if submitted:
            save(lambda: repo.close_exception(s, target_id, evidence), "Exception closed.")
