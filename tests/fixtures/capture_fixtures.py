# One-time script to capture live fixture data

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

FIXTURES = Path(__file__).resolve().parent

# ty
TY_URL = "https://www.trendyol.com/oci/xiaomi-14t-pro-256-g-p-1081766367"
TY_PRODUCT_ID = "1081766367"
TY_SELLER_ID = "624588"
TY_GROUP_ID = "821600500"
TY_LISTING_ID = "e6e8fd8c3d61815b470afae19defb73a"
TY_ITEM_NUMBER = "1494882815"
TY_VIDEO_ID = "6d1ee37d-be18-4bf1-a17f-464d7c2a3643"
TY_DOMAIN = "oci/xiaomi-14t-pro-256-g-p-1081766367"


def _save_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  saved {path.relative_to(FIXTURES)}")


def _save_text(path: Path, text: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    print(f"  saved {path.relative_to(FIXTURES)}")


def capture_trendyol():
    print("\n=== Trendyol ===")
    from scrape.utils.trendyol import (
        _detect_custom_data,
        _extract_listing_entry,
        _extract_reviews_custom,
        _extract_shared_props,
        _find_category_path_in_shared_props,
        _flatten_vas_attributes,
        extract_price,
        extract_product_data,
        get_complete_the_look_from_api,
        get_currencies_from_api,
        get_delivery_date_from_api,
        get_installment_from_api,
        get_merchant_questions_from_api,
        get_product_descriptions_from_api,
        get_product_eligibility_from_api,
        get_raw_html,
        get_reviews_from_api,
        get_seller_acceptance_from_api,
        get_seller_follower_from_api,
        get_seller_store_from_api,
        get_slicing_attributes_from_api,
        get_social_proof_from_api,
        get_stamps_from_api,
        get_stickers_from_api,
        get_vas_from_api,
        get_video_content_from_api,
        parse_html,
    )

    ty = FIXTURES / "trendyol"

    # 1. Fetch product page HTML
    print("  fetching product page...")
    resp = get_raw_html(TY_URL)
    assert resp.status_code == 200, f"HTTP {resp.status_code}"
    html_bytes = resp.content
    (ty / "product_page.html").parent.mkdir(parents=True, exist_ok=True)
    (ty / "product_page.html").write_bytes(html_bytes)
    print(f"  saved product_page.html ({len(html_bytes)} bytes)")

    # 2. Parse and extract local data
    soup = parse_html(html_bytes)
    product_data = extract_product_data(soup)
    price = extract_price(soup)
    shared_props = _extract_shared_props(soup)

    _save_json(ty / "expected" / "product_data.json", product_data)
    _save_text(ty / "expected" / "price.txt", price or "")
    _save_json(ty / "expected" / "shared_props.json", shared_props)

    # Derived expected data
    if shared_props:
        product = shared_props.get("product") or {}
        reviews = _extract_reviews_custom(product_data or {}, shared_props)
        attrs = _flatten_vas_attributes(product.get("attributes"))
        category_path = _find_category_path_in_shared_props(shared_props)
        custom_data = _detect_custom_data(product_data or {}, shared_props)

        _save_json(ty / "expected" / "reviews_custom.json", reviews)
        _save_json(ty / "expected" / "vas_attributes.json", attrs)
        _save_json(ty / "expected" / "category_path.json", category_path)
        _save_json(ty / "expected" / "custom_data.json", custom_data)

        # Listing entry from first merchant
        merchants = product.get("merchantListing") or {}
        merchant_raw = merchants.get("merchant")
        if isinstance(merchant_raw, dict):
            listing_entry = _extract_listing_entry(merchant_raw)
        else:
            listing_entry = None
        _save_json(ty / "expected" / "listing_entry.json", listing_entry)

    # 3. Fetch API responses
    print("  fetching API responses...")
    api = ty / "api"

    _save_json(api / "reviews.json", get_reviews_from_api(TY_PRODUCT_ID))
    _save_json(
        api / "component_read.json", get_product_descriptions_from_api(TY_PRODUCT_ID)
    )
    _save_json(
        api / "delivery_date.json",
        get_delivery_date_from_api(TY_PRODUCT_ID, TY_ITEM_NUMBER, TY_LISTING_ID),
    )
    _save_json(
        api / "installment.json",
        get_installment_from_api(4199, 1058, "eac211e6-2e86-42fa-a755-87479743934a"),
    )
    _save_json(
        api / "merchant_questions.json", get_merchant_questions_from_api(TY_PRODUCT_ID)
    )
    _save_json(
        api / "seller_acceptance.json", get_seller_acceptance_from_api(TY_SELLER_ID)
    )
    _save_json(api / "video_content.json", get_video_content_from_api(TY_VIDEO_ID))
    _save_json(api / "currencies.json", get_currencies_from_api())
    _save_json(api / "stickers.json", get_stickers_from_api("1044"))
    _save_json(
        api / "complete_the_look.json", get_complete_the_look_from_api(TY_PRODUCT_ID)
    )
    _save_json(
        api / "slicing_attributes.json",
        get_slicing_attributes_from_api(TY_GROUP_ID, TY_PRODUCT_ID),
    )
    _save_json(api / "social_proof.json", get_social_proof_from_api(TY_PRODUCT_ID))
    _save_json(api / "seller_store.json", get_seller_store_from_api(TY_SELLER_ID))
    _save_json(api / "seller_follower.json", get_seller_follower_from_api(TY_SELLER_ID))
    _save_json(api / "stamps.json", get_stamps_from_api("4905,8581,9637"))
    _save_json(
        api / "product_eligibility.json",
        get_product_eligibility_from_api(1058, 13, 4199),
    )
    _save_json(api / "vas.json", get_vas_from_api(shared_props=shared_props))


# hepsiburada
HB_URL = "https://www.hepsiburada.com/razer-blackshark-v2-pro-2023-kablosuz-gaming-kulaklik-beyaz-rz04-04530200-r3m1-p-HBCV00004MW5Q6"
HB_SKU = "HBCV00004MW5Q6"


def capture_hepsiburada():
    print("\n=== Hepsiburada ===")
    from scrape.utils.hepsiburada import (
        _build_description,
        _build_vas,
        _detect_category,
        _extract_availability,
        _extract_custom_data,
        _extract_image,
        _extract_product_ctx,
        _extract_redux_product,
        _extract_redux_store,
        _is_generic_hepsiburada_description,
        extract_price,
        extract_product_data,
        get_raw_html,
        get_vas_from_api,
        parse_html,
    )

    hb = FIXTURES / "hepsiburada"

    # 1. Fetch product page HTML
    print("  fetching product page...")
    resp = get_raw_html(HB_URL)
    assert resp.status_code == 200, f"HTTP {resp.status_code}"
    html_bytes = resp.content
    (hb / "product_page.html").write_bytes(html_bytes)
    print(f"  saved product_page.html ({len(html_bytes)} bytes)")

    # 2. Parse and extract local data
    soup = parse_html(html_bytes)
    product_data = extract_product_data(soup)
    price = extract_price(product_data) if product_data else None
    redux = _extract_redux_store(soup)
    redux_product = _extract_redux_product(redux)

    _save_json(hb / "expected" / "product_data.json", product_data)
    _save_text(hb / "expected" / "price.txt", price or "")
    _save_json(hb / "redux_store.json", redux)

    if product_data:
        image = _extract_image(product_data)
        category = _detect_category(product_data, redux_product)
        availability = _extract_availability(product_data, redux_product)
        custom_data = _extract_custom_data(product_data, redux_product)
        ctx = _extract_product_ctx(soup, product_data)
        description = _build_description(soup, product_data)

        _save_text(hb / "expected" / "image.txt", image or "")
        _save_text(hb / "expected" / "category.txt", category)
        _save_text(hb / "expected" / "availability.txt", availability or "")
        _save_json(hb / "expected" / "custom_data.json", custom_data)
        _save_json(hb / "expected" / "product_ctx.json", ctx)
        _save_text(hb / "expected" / "description.txt", description or "")

    # 3. Fetch VAS API response (needs product_data for context)
    print("  fetching VAS API...")
    api = hb / "api"
    try:
        vas_resp = get_vas_from_api(
            HB_SKU, product_url=HB_URL, product_data=product_data, soup=soup
        )
        _save_json(api / "vas.json", vas_resp)
        _save_json(hb / "expected" / "vas_built.json", _build_vas(vas_resp))
    except Exception as e:
        print(f"  VAS API failed: {e}, building from ctx_dict fallback")
        ctx = _extract_product_ctx(soup, product_data)
        try:
            vas_resp = get_vas_from_api(
                HB_SKU,
                product_url=HB_URL,
                product_data=product_data,
                soup=soup,
                ctx_dict=ctx,
            )
            _save_json(api / "vas.json", vas_resp)
            _save_json(hb / "expected" / "vas_built.json", _build_vas(vas_resp))
        except Exception as e2:
            print(f"  VAS API fallback also failed: {e2}")
            _save_json(api / "vas.json", None)
            _save_json(hb / "expected" / "vas_built.json", None)


# mediamarkt
MM_URL = "https://www.mediamarkt.com.tr/tr/product/_dyson-v15-detect-kablosuz-sarjli-dikey-supurge-sari-nikel-1232522.html"


def capture_mediamarkt():
    print("\n=== MediaMarkt ===")
    from scrape.utils.mediamarkt import (
        extract_product_data,
        extract_product_dataset,
        get_raw_html,
        parse_html,
        product_dataset_to_json,
    )

    mm = FIXTURES / "mediamarkt"

    # 1. Fetch product page HTML
    print("  fetching product page...")
    resp = get_raw_html(MM_URL)
    assert resp.status_code == 200, f"HTTP {resp.status_code}"
    html_bytes = resp.content
    (mm / "product_page.html").write_bytes(html_bytes)
    print(f"  saved product_page.html ({len(html_bytes)} bytes)")

    # 2. Parse and extract local data
    soup = parse_html(html_bytes)
    state, product_id = extract_product_data(soup, url=MM_URL)
    assert state is not None, "No apollo state found"

    _save_json(mm / "apollo_state.json", state)
    print(f"  saved apollo_state.json ({len(state)} entities, product_id={product_id})")

    dataset = extract_product_dataset(soup, url=MM_URL)
    assert dataset is not None, "No dataset built"
    _save_json(
        mm / "expected_dataset.json", json.loads(product_dataset_to_json(dataset))
    )
    print(f"  saved expected_dataset.json (source={dataset.source}, sku={dataset.sku})")


if __name__ == "__main__":
    capture_trendyol()
    capture_hepsiburada()
    capture_mediamarkt()
    print("\nDone! Fixtures captured.")
