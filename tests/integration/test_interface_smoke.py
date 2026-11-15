"""Interface smoke tests using Streamlit's own test harness.

They check that every page renders without an exception against the seeded
demonstration profile and that a save through the interface reaches the engine.
They do not replace looking at the application in a browser.
"""
from __future__ import annotations

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

MAIN = Path(__file__).resolve().parents[2] / "app" / "main.py"

PAGES = [
    "Dashboard", "1 Services", "2 Assets and dependencies", "3 Risk register", "4 Control library",
    "5 Assessment", "6 Gaps and remediation", "7 Exceptions", "Tool 1 Service planning",
    "Tool 2 Resumption checklist", "Sensitivity", "Report", "Data and setup",
]


@pytest.fixture
def app(tmp_path, monkeypatch):
    monkeypatch.setenv("BCR_DB", str(tmp_path / "ui.sqlite3"))
    at = AppTest.from_file(str(MAIN), default_timeout=60)
    at.run()
    assert not at.exception, at.exception
    return at


def open_page(at: AppTest, name: str) -> AppTest:
    at.sidebar.radio[0].set_value(name).run()
    assert not at.exception, [e.value for e in at.exception]
    assert not at.error, [e.value for e in at.error]
    return at


@pytest.mark.parametrize("name", PAGES)
def test_every_page_renders(app, name):
    at = open_page(app, name)
    assert at.header, f"{name} shows no header"


def test_dashboard_shows_seeded_results_and_notices(app):
    labels = {m.label: m.value for m in app.metric}
    # Demonstration profile: core banking has no failed gate condition; payments and ATM do.
    assert labels["Services ready"] == "1 of 3"
    assert labels["Overall score"] == "73.3%"
    assert labels["Coverage"].endswith("%")
    assert any("Fictional data" in w.value for w in app.sidebar.warning)
    text = " ".join(m.value for m in app.markdown)
    assert "not a compliance assessment" in text


def test_weighting_scheme_changes_score_but_not_readiness(app):
    # Scheme C is used because A and B differ only in the second decimal for this profile
    # (73.35% and 73.33%), which the one-decimal display does not show.
    before = {m.label: m.value for m in app.metric}
    app.sidebar.selectbox[1].set_value("C").run()
    assert not app.exception
    after = {m.label: m.value for m in app.metric}
    assert after["Services ready"] == before["Services ready"]
    assert (before["Overall score"], after["Overall score"]) == ("73.3%", "74.6%")


def test_tables_never_mix_types_within_a_column():
    """Found in the browser check: a column mixing grades and blanks made the table
    conversion log a traceback on every render."""
    from app.common import uniform_columns
    rows = uniform_columns([
        {"Ref": "A20", "Current": "", "Target": None, "Gap": 4},
        {"Ref": "BKP-02", "Current": 3, "Target": 4, "Gap": 1},
    ])
    for key in ("Ref", "Current", "Target", "Gap"):
        assert len({type(r[key]) for r in rows}) == 1, key
    assert [r["Current"] for r in rows] == ["", "3"]
    assert [r["Target"] for r in rows] == ["", "4"]
    assert [r["Gap"] for r in rows] == [4, 1]  # a clean numeric column is left alone


def test_saving_a_service_with_invalid_input_shows_an_error(app):
    at = open_page(app, "1 Services")
    at.text_input(key="svc_Add new_code").set_value("SVC-NEW")
    at.text_input(key="svc_Add new_name").set_value("")
    at.button[0].click().run()
    assert any("name is required" in e.value for e in at.error)
