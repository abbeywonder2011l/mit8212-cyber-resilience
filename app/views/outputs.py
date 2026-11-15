"""Module 7 pages: dashboard, Tool 1, Tool 2, sensitivity, report, and data setup."""
from __future__ import annotations

from datetime import date

import plotly.graph_objects as go
import streamlit as st

from app.common import FICTIONAL, GATE_ICON, STATUS_ICON, Ctx, flash, save, table
from bcr.data import repository as repo
from bcr.data.seed import reset_to_profile
from bcr.engine import GATES, pct, sensitivity
from bcr.engine.gates import GATE_RULES
from bcr.engine.grades import GRADE_LABELS
from bcr.engine.resumption import CHECKS
from bcr.engine.scoring import SCHEMES
from bcr.profiles import profile_names
from bcr.reporting import LIMITATIONS, actions_csv, content_hash, gaps_csv, render_html, tool1_rows
from bcr.service import build_report_data, exercise_views

BLUE, GREY = "#2f6fb0", "#9aa7b4"
# Neutral series colours: red and green are reserved for pass/fail status.
SERIES = ["#1f4e79", "#2f6fb0", "#8fb8de", "#5b6b7a", "#b9c4cf"]
BAND_ORDER = ["Low", "Medium", "High", "Critical"]
ANSWERS = {"Yes": "yes", "No": "no", "Not applicable": "na", "Unanswered": None}


def dashboard(ctx: Ctx) -> None:
    a = ctx.assessment
    st.header("Dashboard")
    st.caption(f"{a.name} · assessment date {a.assessment_date.isoformat()} · weighting scheme "
               f"{ctx.scheme}: {SCHEMES[ctx.scheme].name}")
    inp, result = ctx.run()
    if not inp.services:
        st.info("No services are registered yet. Add one on the Services page or load a profile under Data and setup.")
        return
    p = result.scores.profile
    ready = sum(1 for r in result.readiness.values() if r.status != "Not demonstrated")
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Overall score", pct(result.scores.overall))
    c2.metric("Coverage", pct(p.coverage))
    c3.metric("Demonstrated by test", pct(p.demonstrated_share))
    c4.metric("Services ready", f"{ready} of {len(inp.services)}")
    c5.metric("Open actions", len(result.actions))
    st.caption("Readiness comes from pass/fail gates, not from the score. A high score cannot compensate "
               "for a failed gate. The score is a researcher-developed measure: it is not a NIST CSF Tier "
               "and not the CBN self-assessment maturity level.")

    st.subheader("Readiness by service")
    table([{
        "Service": f"{s.code} {s.name}", "Criticality": s.criticality,
        "Score": pct(result.scores.services[s.code].score),
        "Status": f"{STATUS_ICON[result.status(s.code)]} {result.status(s.code)}",
        **{g: GATE_ICON[result.readiness[s.code].gates[g].result] for g in GATES},
    } for s in inp.services])
    st.caption("; ".join(f"{g} {GATE_RULES[g][1]} ({GATE_RULES[g][0]})" for g in GATES))
    failed = [{"Service": s.code, "Gate": g, "Condition": c.ref,
               "State": "Waived by exception" if c.waived else "Not met", "Detail": c.detail}
              for s in inp.services for g in GATES
              for c in result.readiness[s.code].gates[g].conditions if not c.met]
    if failed:
        with st.expander(f"Gate conditions not met ({len(failed)})", expanded=True):
            table(failed)

    left, right = st.columns(2)
    with left:
        st.subheader("Score by control domain")
        fig = go.Figure()
        for n, s in enumerate(inp.services):
            scores = result.scores.services[s.code].domain_scores
            fig.add_bar(name=s.code, x=list(ctx.lib.domains), marker_color=SERIES[n % len(SERIES)],
                        y=[None if scores.get(d) is None else round(scores[d] * 100, 1) for d in ctx.lib.domains])
        fig.update_layout(barmode="group", yaxis={"title": "Score (%)", "range": [0, 100]},
                          margin={"l": 10, "r": 10, "t": 10, "b": 10}, height=320,
                          legend={"orientation": "h", "y": -0.15})
        st.plotly_chart(fig, key="chart_domains")
    with right:
        st.subheader("Implemented and outstanding controls")
        fig = go.Figure(go.Bar(x=[f"{g}" for g in range(5)], y=[p.distribution[g] for g in range(5)],
                               marker_color=[GREY, GREY, GREY, BLUE, BLUE],
                               text=[p.distribution[g] for g in range(5)]))
        fig.update_layout(xaxis={"title": "Effective evidence grade"}, yaxis={"title": "Controls"},
                          margin={"l": 10, "r": 10, "t": 10, "b": 10}, height=320)
        st.plotly_chart(fig, key="chart_grades")
        st.caption("Grades: " + "; ".join(f"{g} = {label}" for g, label in GRADE_LABELS.items()))

    left, right = st.columns(2)
    with left:
        st.subheader("Risk distribution")
        counts = {b: sum(1 for r in inp.risks if r.band == b) for b in BAND_ORDER}
        fig = go.Figure(go.Bar(x=BAND_ORDER, y=[counts[b] for b in BAND_ORDER], marker_color=BLUE,
                               text=[counts[b] for b in BAND_ORDER]))
        fig.update_layout(yaxis={"title": "Threat scenarios"}, margin={"l": 10, "r": 10, "t": 10, "b": 10}, height=280)
        st.plotly_chart(fig, key="chart_risk")
    with right:
        st.subheader("Top remediation priorities")
        table([{"Tier": x.tier, "Service": x.service_code, "Ref": x.ref, "Action": x.action_type, "Item": x.title}
               for x in result.actions[:8]])
        if not result.actions:
            st.success("No open actions.")

    with st.expander("Assessment limitations", expanded=True):
        for line in LIMITATIONS:
            st.markdown(f"- {line}")


def tool1(ctx: Ctx) -> None:
    st.header("Tool 1: service dependency and recovery planning matrix")
    st.caption("Table 4.4 of the paper, filled from the registers and the assessment for one service.")
    inp, result = ctx.run()
    if not inp.services:
        st.info("No services are registered yet.")
        return
    by_code = {s.code: s for s in inp.services}
    code = st.selectbox("Service", list(by_code), format_func=lambda c: f"{c} {by_code[c].name}")
    status = result.status(code)
    st.markdown(f"**Readiness status:** {STATUS_ICON[status]} {status}")
    table([{"Field": k, "Entry": v} for k, v in tool1_rows(inp, result, code)])


def tool2(ctx: Ctx) -> None:
    s, a = ctx.session, ctx.assessment
    st.header("Tool 2: safe service-resumption checklist")
    st.caption("Decision rules DR7 to DR9. Resume only if every applicable check is Yes. Resume conditionally only "
               "if the sole gaps are reconciliation checks, checks 5.1, 5.2 and 6.1 are Yes, and each condition has "
               "an owner and an expiry date. Otherwise withhold. Technical restoration alone never authorises resumption.")
    views = exercise_views(s, a.id)
    if not views:
        st.caption("No exercise or incident has been recorded for this assessment.")
    for x in views:
        with st.expander(f"{x['service']} · {x['date']} · {x['kind']} · Decision: {x['decision']}"):
            st.write(x["scenario"])
            table([{"#": n, "Section": section, "Check": text, "Rule": rule,
                    "Result": next(k for k, val in ANSWERS.items() if val == x["results"].get(n)),
                    "Evidence": x["evidence"].get(n, "")}
                   for n, section, text, rule in CHECKS])
            if x["conditions"]:
                table([{"Condition": c["text"], "Owner": c["owner"], "Expiry": c["expiry_date"]} for c in x["conditions"]])
            st.markdown(f"**Decision: {x['decision']}.** " + "; ".join(x["reasons"]))

    services = repo.list_services(s)
    if not services:
        return
    st.subheader("Record a checklist")
    by_code = {r.code: r for r in services}
    with st.form("tool2_form"):
        c1, c2, c3 = st.columns(3)
        code = c1.selectbox("Service", list(by_code))
        when = c2.date_input("Date", value=a.assessment_date)
        kind = c3.selectbox("Kind", ["exercise", "incident"])
        scenario = st.text_input("Scenario")
        results, evidence = {}, {}
        for n, section, text, rule in CHECKS:
            c1, c2, c3 = st.columns([5, 2, 2])
            c1.markdown(f"**{n}** {text}  \n*{section} · {rule}*")
            results[n] = ANSWERS[c2.selectbox(f"Result {n}", list(ANSWERS), index=3, label_visibility="collapsed")]
            evidence[n] = c3.text_input(f"Evidence {n}", placeholder="Evidence reference", label_visibility="collapsed")
        st.markdown("**Conditions for conditional resumption** (one per line: description | owner | expiry date as YYYY-MM-DD)")
        raw = st.text_area("Conditions", label_visibility="collapsed")
        submitted = st.form_submit_button("Save checklist")
    if submitted:
        conditions, errors = [], []
        for line in [x for x in raw.splitlines() if x.strip()]:
            parts = [x.strip() for x in line.split("|")]
            if len(parts) != 3:
                errors.append(f"Condition not understood (use description | owner | date): {line}")
                continue
            try:
                expiry = date.fromisoformat(parts[2])
            except ValueError:
                errors.append(f"Expiry date must be YYYY-MM-DD: {line}")
                continue
            conditions.append({"text": parts[0], "owner": parts[1], "expiry_date": expiry})
        if errors:
            for e in errors:
                st.error(e)
            return
        data = {"exercise_date": when, "kind": kind, "scenario": scenario}
        save(lambda: repo.save_exercise(s, a.id, by_code[code].id, data, results, evidence, conditions),
             "Checklist saved. The decision is shown above.")


def sensitivity_page(ctx: Ctx) -> None:
    st.header("Sensitivity to weighting")
    st.caption("Scores are recomputed under three weighting schemes. Gate results do not use weights, so "
               "readiness status must be the same under every scheme.")
    inp, _ = ctx.run()
    if not inp.services:
        st.info("No services are registered yet.")
        return
    sens = sensitivity(inp)
    table([{
        "Scheme": f"{key}: {v['name']}", "Overall": pct(v["overall"]),
        **{s.code: pct(v["services"][s.code]) for s in inp.services},
        "Ranking by score": " > ".join(v["ranking"]),
    } for key, v in sens.items()])
    fig = go.Figure()
    for n, (key, v) in enumerate(sens.items()):
        fig.add_bar(name=f"{key}: {v['name']}", x=[s.code for s in inp.services],
                    marker_color=SERIES[n % len(SERIES)],
                    y=[None if v["services"][s.code] is None else round(v["services"][s.code] * 100, 1)
                       for s in inp.services])
    fig.update_layout(barmode="group", yaxis={"title": "Score (%)", "range": [0, 100]},
                      margin={"l": 10, "r": 10, "t": 10, "b": 10}, height=340)
    st.plotly_chart(fig, key="chart_sensitivity")
    rankings = {tuple(v["ranking"]) for v in sens.values()}
    statuses = {tuple(sorted(v["status"].items())) for v in sens.values()}
    if len(rankings) == 1:
        st.info("The ranking of services by score is the same under all three schemes.")
    else:
        st.warning("The ranking of services by score changes with the weighting scheme. Treat the ranking as an assumption-dependent result.")
    if len(statuses) == 1:
        st.success("Readiness status is identical under all three schemes.")
    else:
        st.error("Readiness status differs between schemes. This should not happen and indicates a defect.")
    table([{"Scheme": k, "Control weight": "1 or 2 as catalogued" if sc.use_control_weights else "1",
            "Domain weight": ", ".join(f"{d} x{w}" for d, w in sc.domain_weights.items()) or "1",
            "Service weight": "Criticality" if sc.use_criticality else "1"} for k, sc in SCHEMES.items()])


def report(ctx: Ctx) -> None:
    st.header("Assessment report")
    a = ctx.assessment
    data = build_report_data(ctx.session, a.id, ctx.lib, ctx.scheme)
    html = render_html(data)
    stem = f"assessment-{a.id}-{a.assessment_date.isoformat()}-scheme-{ctx.scheme}"
    st.write("The report is one self-contained HTML file. It includes the fictional-data notice, readiness by "
             "service, domain scores, the risk register, the remediation plan, exceptions, Tool 1 and Tool 2 "
             "records, the sensitivity table and the limitations.")
    c1, c2, c3 = st.columns(3)
    c1.download_button("Download report (HTML)", html, file_name=f"{stem}.html", mime="text/html")
    c2.download_button("Download actions (CSV)", actions_csv(data.result), file_name=f"{stem}-actions.csv", mime="text/csv")
    c3.download_button("Download all grades (CSV)", gaps_csv(data.inp, data.result), file_name=f"{stem}-grades.csv", mime="text/csv")
    st.caption(f"Report content hash (SHA-256): {content_hash(html)}")
    st.caption("The report carries no generation time, so the same assessment always gives the same hash.")


def setup(ctx: Ctx) -> None:
    s, lib = ctx.session, ctx.lib
    st.header("Data and setup")
    st.warning(FICTIONAL)
    st.subheader("Load a synthetic profile")
    st.write("Loading a profile deletes everything in the database and replaces it with the chosen profile.")
    names = profile_names()
    key = st.selectbox("Profile", list(names), format_func=lambda k: f"{k}: {names[k]}")
    confirm = st.checkbox("I understand this replaces all current data")
    if st.button("Load profile", disabled=not confirm):
        s.close()
        reset_to_profile(ctx.engine, key, lib)
        st.session_state.pop("assessment_id", None)
        flash(f"Loaded profile {key}: {names[key]}")
        st.rerun()

    st.subheader("Start a new assessment")
    rows = repo.list_assessments(s)
    by_id = {r.id: r for r in rows}
    with st.form("new_assessment"):
        name = st.text_input("Name")
        c1, c2, c3 = st.columns(3)
        when = c1.date_input("Assessment date", value=date.today())
        assessor = c2.text_input("Assessor")
        validity = c3.number_input("Validity period for tests (days)", min_value=1, value=365, step=1)
        copy_from = st.selectbox("Start from", [0] + list(by_id),
                                 format_func=lambda i: "A blank assessment" if i == 0 else f"A copy of: {by_id[i].name}")
        submitted = st.form_submit_button("Create assessment")
    if submitted:
        data = {"name": name, "assessment_date": when, "assessor": assessor, "validity_days": int(validity)}

        def write():
            row = repo.create_assessment(s, data, lib, copy_from or None)
            st.session_state["assessment_id"] = row.id

        save(write, f"Assessment '{name}' created and selected.")
    table([{"ID": r.id, "Name": r.name, "Date": r.assessment_date.isoformat(), "Assessor": r.assessor,
            "Library": r.library_version, "Validity (days)": r.validity_days} for r in rows])
