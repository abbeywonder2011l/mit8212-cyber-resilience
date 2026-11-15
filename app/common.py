"""Shared helpers for the interface. No business rules live here."""
from __future__ import annotations

from dataclasses import dataclass

import streamlit as st
from sqlalchemy.orm import Session

from bcr.engine import AssessmentInput, AssessmentResult
from bcr.library import Library
from bcr.service import run_assessment
from bcr.validation import ValidationError

FICTIONAL = ("Fictional data. 'Bank X' is not a real bank, and nothing shown here describes any real "
             "institution. This is an academic prototype, not a compliance assessment.")

STATUS_ICON = {"Ready": "🟢", "Ready with accepted exceptions": "🟡", "Not demonstrated": "🔴"}
GATE_ICON = {"PASS": "✅ Pass", "PASS_WITH_EXCEPTION": "🟡 Exception", "FAIL": "❌ Fail"}


@dataclass
class Ctx:
    session: Session
    lib: Library
    assessment: object  # bcr.data.models.Assessment
    engine: object
    scheme: str

    def run(self) -> tuple[AssessmentInput, AssessmentResult]:
        return run_assessment(self.session, self.assessment.id, self.lib, self.scheme)


def flash(message: str, kind: str = "success") -> None:
    st.session_state.setdefault("flash", []).append((kind, message))


def show_flash() -> None:
    for kind, message in st.session_state.pop("flash", []):
        getattr(st, kind)(message)


def save(action, success: str) -> bool:
    """Run a write; show validation errors as plain messages. Returns True on success."""
    try:
        result = action()
    except ValidationError as exc:
        for error in exc.errors:
            st.error(error)
        return False
    flash(success)
    for warning in result if isinstance(result, list) else []:
        flash(str(warning), "warning")
    st.rerun()
    return True


def parse_number(text: str, label: str) -> tuple[float | None, str | None]:
    """Blank means 'not recorded'. Returns (value, error)."""
    text = (text or "").strip()
    if not text:
        return None, None
    try:
        return float(text), None
    except ValueError:
        return None, f"{label} must be a number or left blank."


def fmt_number(value) -> str:
    return "" if value is None else f"{float(value):g}"


def uniform_columns(rows: list[dict]) -> list[dict]:
    """Make every column a single type so the table converts cleanly.

    A column that mixes types (for example grades and blanks) is shown as text.
    """
    out = [dict(r) for r in rows]
    for key in {k for r in out for k in r}:
        values = [r.get(key) for r in out]
        if len({type(v) for v in values}) > 1 or any(v is None for v in values):
            for r in out:
                r[key] = "" if r.get(key) is None else str(r[key])
    return out


def table(rows: list[dict]) -> None:
    if rows:
        st.dataframe(uniform_columns(rows), hide_index=True)
    else:
        st.caption("Nothing recorded.")
