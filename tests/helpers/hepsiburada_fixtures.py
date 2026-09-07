# Fixture loaders for Hepsiburada unit tests needs zero network
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from bs4 import BeautifulSoup

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "hepsiburada"


@lru_cache(maxsize=1)
def load_product_html() -> str:
    return (FIXTURES / "product_page.html").read_text(encoding="utf-8")


@lru_cache(maxsize=1)
def load_product_bytes() -> bytes:
    return (FIXTURES / "product_page.html").read_bytes()


@lru_cache(maxsize=1)
def load_soup() -> BeautifulSoup:
    return BeautifulSoup(load_product_bytes(), "html.parser")


@lru_cache(maxsize=1)
def load_redux_store() -> dict | None:
    path = FIXTURES / "redux_store.json"
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def load_expected(name: str):
    path = FIXTURES / "expected" / name
    if name.endswith(".json"):
        return json.loads(path.read_text(encoding="utf-8"))
    return path.read_text(encoding="utf-8")


def load_api(name: str):
    path = FIXTURES / "api" / name
    return json.loads(path.read_text(encoding="utf-8"))
