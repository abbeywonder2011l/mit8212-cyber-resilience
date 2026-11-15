"""Module 1 pages: services, assets and dependencies, risk register."""
from __future__ import annotations

import streamlit as st

from app.common import Ctx, fmt_number, parse_number, save, table
from bcr import validation as v
from bcr.data import repository as repo
from bcr.engine.models import risk_band

NEW = "Add new"


def services(ctx: Ctx) -> None:
    st.header("Services and recovery requirements")
    st.caption("Stages S1 and S2. Decision rules DR1 (owners, criticality) and DR2 (approved recovery requirements).")
    s = ctx.session
    rows = repo.list_services(s)
    code_of = {r.id: r.code for r in rows}
    deps = repo.depends_on_map(s)
    table([{
        "Code": r.code, "Service": r.name, "Criticality": r.criticality,
        "Business owner": r.business_owner, "Technical owner": r.technical_owner,
        "Max tolerable downtime (h)": r.mtd_hours, "RTO (h)": r.rto_hours, "RPO (min)": r.rpo_minutes,
        "Approved": "Yes" if r.requirements_approved else "No",
        "Depends on": ", ".join(code_of[d] for d in deps.get(r.id, [])),
    } for r in rows])

    st.subheader("Add or edit a service")
    choice = st.selectbox("Service", [NEW] + [r.code for r in rows], key="svc_choice")
    row = next((r for r in rows if r.code == choice), None)
    k = f"svc_{choice}_"
    with st.form(k + "form"):
        c1, c2, c3 = st.columns([1, 2, 1])
        code = c1.text_input("Code", value=row.code if row else "", key=k + "code")
        name = c2.text_input("Name", value=row.name if row else "", key=k + "name")
        criticality = c3.selectbox("Criticality (1 low, 5 high)", [1, 2, 3, 4, 5],
                                   index=(row.criticality - 1) if row else 2, key=k + "crit")
        description = st.text_input("Description", value=row.description if row else "", key=k + "desc")
        c1, c2 = st.columns(2)
        business_owner = c1.text_input("Business owner", value=row.business_owner if row else "", key=k + "bo")
        technical_owner = c2.text_input("Technical owner", value=row.technical_owner if row else "", key=k + "to")
        st.markdown("**Recovery requirements** (leave blank if not yet recorded)")
        c1, c2, c3 = st.columns(3)
        mtd_t = c1.text_input("Maximum tolerable downtime (hours)", value=fmt_number(row.mtd_hours) if row else "", key=k + "mtd")
        rto_t = c2.text_input("RTO (hours)", value=fmt_number(row.rto_hours) if row else "", key=k + "rto")
        rpo_t = c3.text_input("RPO (minutes)", value=fmt_number(row.rpo_minutes) if row else "", key=k + "rpo")
        approved = st.checkbox("Approved in writing by the business owner and the risk function",
                               value=bool(row.requirements_approved) if row else False, key=k + "appr")
        others = [r for r in rows if row is None or r.id != row.id]
        current = [code_of[d] for d in deps.get(row.id, [])] if row else []
        depends_on = st.multiselect("Depends on these services", [r.code for r in others],
                                    default=[c for c in current if c in [r.code for r in others]], key=k + "deps")
        submitted = st.form_submit_button("Save service")
    if submitted:
        numbers, errors = {}, []
        for field, text, label in (("mtd_hours", mtd_t, "Maximum tolerable downtime"),
                                   ("rto_hours", rto_t, "RTO"), ("rpo_minutes", rpo_t, "RPO")):
            numbers[field], err = parse_number(text, label)
            if err:
                errors.append(err)
        if errors:
            for e in errors:
                st.error(e)
            return
        data = {"code": code, "name": name, "description": description, "criticality": criticality,
                "business_owner": business_owner, "technical_owner": technical_owner,
                "requirements_approved": approved, **numbers}

        def write():
            saved = repo.save_service(s, data, row.id if row else None)
            id_of = {r.code: r.id for r in repo.list_services(s)}
            repo.set_service_dependencies(s, saved.id, [id_of[c] for c in depends_on])

        save(write, f"Service {code} saved.")


def assets(ctx: Ctx) -> None:
    st.header("Assets and dependencies")
    st.caption("Stage S3. Decision rule DR3: a dependency is unresolved if it is a single point of failure "
               "with no tested alternative, or a third party with no tested recovery coordination.")
    s = ctx.session
    asset_rows = repo.list_assets(s)
    service_rows = repo.list_services(s)
    links = repo.list_service_assets(s)
    used_by: dict[int, list[str]] = {}
    for link in links:
        used_by.setdefault(link.asset_id, []).append(link.service.code)

    tab_assets, tab_links = st.tabs(["Asset register", "Service dependencies"])
    with tab_assets:
        table([{
            "Code": a.code, "Asset": a.name, "Type": a.type, "Site": a.site, "Criticality": a.criticality,
            "Owner": a.owner, "Third party": "Yes" if a.is_third_party else "No", "Provider": a.provider,
            "Used by": ", ".join(used_by.get(a.id, [])),
        } for a in asset_rows])
        st.subheader("Add or edit an asset")
        choice = st.selectbox("Asset", [NEW] + [a.code for a in asset_rows], key="asset_choice")
        row = next((a for a in asset_rows if a.code == choice), None)
        k = f"asset_{choice}_"
        with st.form(k + "form"):
            c1, c2 = st.columns([1, 3])
            code = c1.text_input("Code", value=row.code if row else "", key=k + "code")
            name = c2.text_input("Name", value=row.name if row else "", key=k + "name")
            c1, c2, c3 = st.columns(3)
            types = list(v.ASSET_TYPES)
            type_ = c1.selectbox("Type", types, index=types.index(row.type) if row and row.type in types else 0, key=k + "type")
            site = c2.text_input("Site", value=row.site if row else "", key=k + "site")
            criticality = c3.selectbox("Criticality", [1, 2, 3, 4, 5], index=(row.criticality - 1) if row else 2, key=k + "crit")
            c1, c2, c3 = st.columns(3)
            owner = c1.text_input("Owner", value=row.owner if row else "", key=k + "owner")
            third = c2.checkbox("Third-party asset or service", value=bool(row.is_third_party) if row else False, key=k + "third")
            provider = c3.text_input("Provider", value=row.provider if row else "", key=k + "prov")
            submitted = st.form_submit_button("Save asset")
        if submitted:
            data = {"code": code, "name": name, "type": type_, "site": site, "criticality": criticality,
                    "owner": owner, "is_third_party": third, "provider": provider}
            save(lambda: repo.save_asset(s, data, row.id if row else None), f"Asset {code} saved.")

    with tab_links:
        table([{
            "Service": link.service.code, "Asset": f"{link.asset.code} {link.asset.name}",
            "Third party": "Yes" if link.asset.is_third_party else "No",
            "Single point of failure": "Yes" if link.single_point_of_failure else "No",
            "Tested alternative": "Yes" if link.tested_alternative else "No",
            "Recovery coordination tested": "Yes" if link.recovery_coordination_tested else "No",
            "Unresolved (DR3)": "YES" if (
                (link.single_point_of_failure and not link.tested_alternative)
                or (link.asset.is_third_party and not link.recovery_coordination_tested)) else "",
            "Note": link.note,
        } for link in links])
        st.subheader("Link a service to an asset, or update the link")
        if not service_rows or not asset_rows:
            st.info("Add at least one service and one asset first.")
            return
        c1, c2 = st.columns(2)
        svc_by = {r.code: r for r in service_rows}
        ast_by = {a.code: a for a in asset_rows}
        svc = svc_by[c1.selectbox("Service", list(svc_by), key="link_svc",
                                  format_func=lambda c: f"{c} {svc_by[c].name}")]
        ast = ast_by[c2.selectbox("Asset", list(ast_by), key="link_ast",
                                  format_func=lambda c: f"{c} {ast_by[c].name}")]
        link = next((x for x in links if x.service_id == svc.id and x.asset_id == ast.id), None)
        k = f"link_{svc.id}_{ast.id}_"
        with st.form(k + "form"):
            spof = st.checkbox("Single point of failure for this service",
                               value=bool(link.single_point_of_failure) if link else False, key=k + "spof")
            alt = st.checkbox("An alternative exists and has been tested",
                              value=bool(link.tested_alternative) if link else True, key=k + "alt")
            coord = st.checkbox("Recovery coordination with the provider has been tested (third parties)",
                                value=bool(link.recovery_coordination_tested) if link else True, key=k + "coord")
            note = st.text_input("Note", value=link.note if link else "", key=k + "note")
            submitted = st.form_submit_button("Save dependency")
        if submitted:
            data = {"single_point_of_failure": spof, "tested_alternative": alt,
                    "recovery_coordination_tested": coord, "note": note}
            save(lambda: repo.save_service_asset(s, svc.id, ast.id, data),
                 f"Dependency {svc.code} to {ast.code} saved.")


def risks(ctx: Ctx) -> None:
    st.header("Risk register")
    st.caption("Component C2. Rating = likelihood x impact on 1-5 scales (the researcher's own anchors). "
               "Bands: Low 1-4, Medium 5-9, High 10-14, Critical 15-25. Used only to order remediation actions.")
    s = ctx.session
    rows = repo.list_risks(s)
    service_rows = repo.list_services(s)
    table([{
        "ID": r.id, "Service": r.service.code, "Threat scenario": r.title, "Category": r.category,
        "Likelihood": r.likelihood, "Impact": r.impact, "Rating": r.likelihood * r.impact,
        "Band": risk_band(r.likelihood * r.impact),
        "Affects recovery environment": "Yes" if r.affects_recovery_environment else "No",
    } for r in sorted(rows, key=lambda r: -(r.likelihood * r.impact))])

    if not service_rows:
        st.info("Add a service first.")
        return
    st.subheader("Add a threat scenario")
    with st.form("risk_form"):
        c1, c2 = st.columns([1, 3])
        svc_by = {r.code: r for r in service_rows}
        svc_code = c1.selectbox("Service", list(svc_by))
        title = c2.text_input("Threat scenario")
        c1, c2, c3 = st.columns(3)
        category = c1.selectbox("Category", list(v.RISK_CATEGORIES))
        likelihood = c2.selectbox("Likelihood (1 rare, 5 almost certain)", [1, 2, 3, 4, 5], index=2)
        impact = c3.selectbox("Impact (1 negligible, 5 severe)", [1, 2, 3, 4, 5], index=2)
        affects = st.checkbox("Could also affect the recovery environment")
        submitted = st.form_submit_button("Add scenario")
    if submitted:
        data = {"title": title, "category": category, "likelihood": likelihood, "impact": impact,
                "affects_recovery_environment": affects}
        save(lambda: repo.save_risk(s, svc_by[svc_code].id, data), "Threat scenario added.")

    if rows:
        st.subheader("Remove a threat scenario")
        by_id = {r.id: r for r in rows}
        target_id = st.selectbox("Scenario", list(by_id),
                                 format_func=lambda i: f"{i}: {by_id[i].service.code} {by_id[i].title}")
        if st.button("Remove scenario"):
            save(lambda: repo.delete_risk(s, target_id), "Threat scenario removed.")
