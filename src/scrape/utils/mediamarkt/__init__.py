# scrape.utils.mediamarkt package facade that keeps the module-level API

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
from .builders import *
from .dataset import *
from .graphql import *
from .http import *
from .parsing import *

__all__: list[str] = [
    "_GRAPHQL_ENDPOINT",
    "_MM_UA",
    "_build_availability",
    "_build_category",
    "_build_custom_data",
    "_build_description",
    "_build_features",
    "_build_highlights",
    "_build_image",
    "_build_installment",
    "_build_name",
    "_build_price",
    "_build_reviews",
    "_build_status",
    "_build_va_services",
    "_decode_mm_html",
    "_execute_persisted_query",
    "_extract_apollo_state",
    "_extract_first_string",
    "_extract_preloaded_state",
    "_feature_entities",
    "_format_price_value",
    "_get_entity",
    "_graphql_headers",
    "_is_placeholder_description_text",
    "_iter_breadcrumbs",
    "_iter_json_ld_payloads",
    "_normalize_json_value",
    "_page_headers",
    "_product_id_from_url",
    "_safe_api_call",
    "_str",
    "build_product_dataset",
    "extract_product_data",
    "extract_product_dataset",
    "extract_product_id",
    "get_loyalty_points_from_graphql",
    "get_product_media_from_graphql",
    "get_raw_html",
    "parse_html",
    "product_dataset_to_json",
    "requests",
]
