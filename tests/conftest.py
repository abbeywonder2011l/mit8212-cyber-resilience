from __future__ import annotations

import pytest

from bcr.engine import assess
from bcr.library import load_library
from bcr.profiles import build_profile, profile_to_input


@pytest.fixture(scope="session")
def lib():
    return load_library()


@pytest.fixture(scope="session")
def profile(lib):
    def _build(name: str) -> dict:
        return build_profile(name, lib)
    return _build


@pytest.fixture(scope="session")
def run(lib, profile):
    """Assess a named profile and return (input, result)."""
    def _run(name: str, scheme: str = "A"):
        inp = profile_to_input(profile(name), lib)
        return inp, assess(inp, scheme)
    return _run
