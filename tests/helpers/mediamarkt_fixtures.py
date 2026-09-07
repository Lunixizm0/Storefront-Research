# Fixture loaders for MediaMarkt unit tests needs zero network
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from bs4 import BeautifulSoup

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "mediamarkt"


def _load_json(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def load_apollo_state() -> dict:
    return _load_json("apollo_state.json")


@lru_cache(maxsize=1)
def load_expected_dataset() -> dict:
    return _load_json("expected_dataset.json")


@lru_cache(maxsize=1)
def load_soup() -> BeautifulSoup:
    # Build a minimal HTML document that embeds __PRELOADED_STATE__ whose
    # apolloState sub-object match the fixture. Used to exercise the SSRed
    # extraction path without shipping the full mb document.
    state = load_apollo_state()
    body = '{"apolloState": ' + json.dumps(state, ensure_ascii=False) + "}"
    html = (
        "<html><body><script>"
        "window.__PRELOADED_STATE__ = " + body + ";"
        "</script></body></html>"
    )
    return BeautifulSoup(html, "html.parser")
