# Integration conftest parametrized live URLs, session-scoped fixtures things
from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Add helpers to path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def _get_trendyol_urls(limit=5):
    from tests.helpers._live_helpers import get_trendyol_product_urls

    return get_trendyol_product_urls(limit=limit)


def _get_hepsiburada_urls(limit=5):
    from tests.helpers._live_helpers import get_hepsiburada_product_urls

    return get_hepsiburada_product_urls(limit=limit)


def pytest_generate_tests(metafunc):
    if "trendyol_url" in metafunc.fixturenames:
        urls = _get_trendyol_urls(limit=5)
        metafunc.parametrize("trendyol_url", urls)
    if "hepsiburada_url" in metafunc.fixturenames:
        urls = _get_hepsiburada_urls(limit=5)
        metafunc.parametrize("hepsiburada_url", urls)


@pytest.fixture(scope="session")
def live_trendyol_ids():
    return {
        "product_id": "1081766367",
        "seller_id": "624588",
        "group_id": "821600500",
        "listing_id": "e6e8fd8c3d61815b470afae19defb73a",
        "item_number": "1494882815",
        "video_id": "6d1ee37d-be18-4bf1-a17f-464d7c2a3643",
    }


@pytest.fixture(scope="session")
def live_hepsiburada_sku():
    return "HBCV00004MW5Q6"
