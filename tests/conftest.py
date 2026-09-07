from __future__ import annotations

import json
from pathlib import Path

import pytest

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"


def pytest_configure(config):
    config.addinivalue_line(
        "markers", "integration: tests that hit live APIs and require network"
    )


def load_fixture(*parts: str, as_json: bool = True):

    # load_fixture("trendyol", "product_page.html", as_json=False) returns str
    # load_fixture("trendyol", "api", "reviews.json")  returns dict
    path = FIXTURES_DIR.joinpath(*parts)
    if not path.exists():
        raise FileNotFoundError(f"Fixture not found: {path}")
    if as_json:
        return json.loads(path.read_text(encoding="utf-8"))
    return path.read_text(encoding="utf-8")


def load_fixture_bytes(*parts: str) -> bytes:
    # Load a file from tests/fixtures/ as raw bytes
    path = FIXTURES_DIR.joinpath(*parts)
    if not path.exists():
        raise FileNotFoundError(f"Fixture not found: {path}")
    return path.read_bytes()
