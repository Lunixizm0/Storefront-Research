from __future__ import annotations

import os

import pytest


@pytest.fixture(autouse=True)
def _disable_mediamarkt_graphql(monkeypatch):
    # The supplementary GraphQL path hits the live MediaMarkt GraphQL API.
    # Unit tests must stay hermetic, so disable it by default.
    monkeypatch.setenv("SCRAPE_MEDIAMARKT_GRAPHQL", "0")
