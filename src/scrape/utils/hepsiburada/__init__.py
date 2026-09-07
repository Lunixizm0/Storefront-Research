# scrape.utils.hepsiburada package facade that keeps the module-level API

from ..trendyol.common import (
    _extract_first_string,
    _format_price_value,
    _is_placeholder_description_text,
    _iter_json_ld_payloads,
    _normalize_json_value,
    _safe_api_call,
    _str,
    parse_html,
    product_dataset_to_json,
)
from . import api, builders, dataset, http, parsing

__all__: list[str] = (
    [
        "parse_html",
        "product_dataset_to_json",
        "_safe_api_call",
        "_extract_first_string",
        "_format_price_value",
        "_normalize_json_value",
        "_str",
        "_is_placeholder_description_text",
        "_iter_json_ld_payloads",
    ]
    + api.__all__
    + builders.__all__
    + dataset.__all__
    + http.__all__
    + parsing.__all__
)

for _module in (api, builders, dataset, http, parsing):
    for _name in _module.__all__:
        globals()[_name] = getattr(_module, _name)
del _module, _name
