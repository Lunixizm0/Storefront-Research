# Fixture loaders for Trendyol unit tests needs zero network
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from bs4 import BeautifulSoup

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "trendyol"


@lru_cache(maxsize=1)
def load_product_html() -> str:
    return (FIXTURES / "product_page.html").read_text(encoding="utf-8")


@lru_cache(maxsize=1)
def load_product_bytes() -> bytes:
    return (FIXTURES / "product_page.html").read_bytes()


@lru_cache(maxsize=1)
def load_soup() -> BeautifulSoup:
    return BeautifulSoup(load_product_bytes(), "html.parser")


def load_expected(name: str) -> Any:
    path = FIXTURES / "expected" / name
    if name.endswith(".json"):
        return json.loads(path.read_text(encoding="utf-8"))
    return path.read_text(encoding="utf-8")


def load_api(name: str):
    path = FIXTURES / "api" / name
    return json.loads(path.read_text(encoding="utf-8"))
