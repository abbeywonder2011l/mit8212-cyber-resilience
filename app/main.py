"""Streamlit entry point.

Run from the project root:  streamlit run app/main.py
The database file defaults to data/bcr.sqlite3; set BCR_DB to use another path.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv  # noqa: E402
import streamlit as st  # noqa: E402
from streamlit.errors import StreamlitSecretNotFoundError  # noqa: E402

for env_file in (".env", ".env.local"):
    load_dotenv(ROOT / env_file)

from app.common import FICTIONAL, Ctx, show_flash  # noqa: E402
from app.views import assess, outputs, registers  # noqa: E402
from bcr.data import repository as repo  # noqa: E402
from bcr.data.seed import reset_to_profile  # noqa: E402
from bcr.engine.scoring import SCHEMES  # noqa: E402
from bcr.library import LibraryError, load_library  # noqa: E402

PAGES = {
    "Dashboard": outputs.dashboard,
    "1 Services": registers.services,
    "2 Assets and dependencies": registers.assets,
    "3 Risk register": registers.risks,
    "4 Control library": assess.library,
    "5 Assessment": assess.assessment,
    "6 Gaps and remediation": assess.gaps,
    "7 Exceptions": assess.exceptions,
    "Tool 1 Service planning": outputs.tool1,
    "Tool 2 Resumption checklist": outputs.tool2,
    "Sensitivity": outputs.sensitivity_page,
    "Report": outputs.report,
    "Data and setup": outputs.setup,
}


@st.cache_resource
def get_engine(db_target: str):
    if not db_target.startswith(("postgres://", "postgresql://", "postgresql+psycopg://")):
        Path(db_target).parent.mkdir(parents=True, exist_ok=True)
    return repo.make_engine(db_target)


def database_target() -> str:
    """Prefer Neon/PostgreSQL secrets; retain the local SQLite default."""
    target = os.environ.get("DATABASE_URL") or os.environ.get("NEON_DATABASE_URL")
    if not target:
        try:
            target = st.secrets.get("DATABASE_URL") or st.secrets.get("NEON_DATABASE_URL")
        except StreamlitSecretNotFoundError:
            target = None
    return target or os.environ.get("BCR_DB", str(ROOT / "data" / "bcr.sqlite3"))


@st.cache_resource
def get_library():
    return load_library()


def main() -> None:
    st.set_page_config(page_title="Cyber-Resilience Assessment (prototype)", layout="wide")
    try:
        lib = get_library()
    except LibraryError as exc:
        st.error("The control library failed validation, so no assessment can be run.")
        for error in exc.errors:
            st.write(f"- {error}")
        st.stop()

    engine = get_engine(database_target())
    Session = repo.make_session_factory(engine)

    with Session() as probe:
        empty = not repo.list_assessments(probe)
    if empty:
        reset_to_profile(engine, "DEMO", lib)

    with Session() as session:
        assessments = repo.list_assessments(session)
        by_id = {a.id: a for a in assessments}
        st.sidebar.title("Cyber-Resilience Assessment")
        st.sidebar.caption("Academic prototype · MIT 8212 seminar")
        if st.session_state.get("assessment_id") not in by_id:
            st.session_state["assessment_id"] = assessments[-1].id
        st.sidebar.selectbox("Assessment", list(by_id), key="assessment_id",
                             format_func=lambda i: f"{by_id[i].name} ({by_id[i].assessment_date.isoformat()})")
        scheme = st.sidebar.selectbox("Weighting scheme", list(SCHEMES),
                                      format_func=lambda k: f"{k}: {SCHEMES[k].name}")
        page = st.sidebar.radio("Page", list(PAGES))
        st.sidebar.warning(FICTIONAL)

        ctx = Ctx(session=session, lib=lib, assessment=by_id[st.session_state["assessment_id"]],
                  engine=engine, scheme=scheme)
        show_flash()
        PAGES[page](ctx)


main()
