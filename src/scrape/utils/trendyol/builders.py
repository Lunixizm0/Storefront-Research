# In-tree package module. Do not use directly. import from scrape.utils.{pkg}

from scrape.debug import debug, warn

from . import api
from .common import _safe_api_call
from .shared_props import (
    _sp_category_id,
    _sp_delivery,
    _sp_group_tag_ids,
    _sp_p_group_id,
    _sp_product_id,
    _sp_seller_id,
    _sp_selling_price,
    _sp_sticker_ids,
    _sp_tag_ids,
    _sp_video_id,
)

__all__ = [
    "_build_complete_the_look",
    "_build_currencies",
    "_build_delivery",
    "_build_installments",
    "_build_merchant_questions",
    "_build_product_eligibility",
    "_build_reviews",
    "_build_seller_acceptance",
    "_build_seller_follower",
    "_build_seller_store",
    "_build_slicing_attributes",
    "_build_social_proof",
    "_build_stamps",
    "_build_stickers",
    "_build_vas",
    "_build_video",
]


def _build_reviews(product_data, shared_props):
    pid = _sp_product_id(product_data, shared_props)
    if pid is None:
        return None
    data = _safe_api_call(api.get_reviews_from_api, pid)
    if not isinstance(data, dict):
        return None
    result = data.get("result")
    if not isinstance(result, dict):
        return None
    summary = result.get("summary") if isinstance(result.get("summary"), dict) else {}
    if not isinstance(summary, dict):
        summary = {}
    reviews = []
    for r in result.get("reviews") or []:
        if not isinstance(r, dict):
            continue
        entry = {}
        if r.get("rate") is not None:
            entry["rating"] = r["rate"]
        text = r.get("comment") or r.get("originalText")
        if text:
            entry["comment"] = text
        seller = r.get("seller")
        if isinstance(seller, dict) and seller.get("name"):
            entry["seller"] = seller["name"]
        if r.get("trusted") is not None:
            entry["trusted"] = r["trusted"]
        if entry:
            reviews.append(entry)
    out = {}
    if summary.get("averageRating") is not None:
        out["score"] = summary["averageRating"]
    if summary.get("totalRatingCount") is not None:
        out["total_rating_count"] = summary["totalRatingCount"]
    if result.get("aiSummary"):
        out["ai_summary"] = result["aiSummary"]
    if reviews:
        out["reviews"] = reviews[:5]
    return out if out else None


def _build_vas(product_data, shared_props):
    pid = _sp_product_id(product_data, shared_props)
    data = _safe_api_call(
        api.get_vas_from_api, product_id=pid, shared_props=shared_props
    )
    if not isinstance(data, dict) or not data.get("isSuccess"):
        debug(
            "api.builder.skip",
            builder="_build_vas",
            reason="response_not_successful",
            response_type=type(data).__name__,
            is_success=data.get("isSuccess") if isinstance(data, dict) else None,
        )
        return None
    result = data.get("result")
    if not isinstance(result, list):
        warn("api.builder.skip", builder="_build_vas", reason="result_not_a_list")
        return None
    offers = []
    for offer in result:
        if not isinstance(offer, dict):
            continue
        entry = {
            "name": offer.get("subCategory")
            or offer.get("category")
            or offer.get("variant", {}).get("name"),
            "price": offer.get("calculatedPrice") or offer.get("calculatedPriceText"),
            "user_friendly_price": offer.get("calculatedPriceTextWithCurrency"),
            "currency": offer.get("currency"),
            "category": offer.get("category"),
            "seller": offer.get("sellerName"),
        }
        entry = {k: v for k, v in entry.items() if v is not None}
        if offer.get("description"):
            entry["description"] = offer["description"]
        if entry:
            offers.append(entry)
    if not offers:
        warn("api.builder.skip", builder="_build_vas", reason="no_usable_offers")
        return None
    return offers


def _build_installments(product_data, shared_props):
    amount = _sp_selling_price(shared_props)
    category_id = _sp_category_id(shared_props)
    if amount is None or category_id is None:
        return None
    group_tag_ids = _sp_group_tag_ids(shared_props) or ""
    data = _safe_api_call(
        api.get_installment_from_api, amount, category_id, group_tag_ids
    )
    if not isinstance(data, dict):
        return None
    result = data.get("result")
    if not isinstance(result, dict):
        return None
    out = {}
    summary = result.get("summary")
    if isinstance(summary, dict):
        zero = summary.get("zeroInstallment")
        if isinstance(zero, dict):
            out["zero_installment"] = {
                "term": zero.get("term"),
                "banks": zero.get("bankDetails"),
            }
        max_inst = summary.get("maxInstallment")
        if isinstance(max_inst, dict):
            out["max_installment"] = {
                "term": max_inst.get("term"),
                "monthly_fee": max_inst.get("monthlyFee"),
            }
    offers = []
    for offer in result.get("installmentOffers") or []:
        if not isinstance(offer, dict):
            continue
        issuer = offer.get("issuerName") or offer.get("displayName")
        plans = []
        for inst in offer.get("installements") or []:
            if not isinstance(inst, dict):
                continue
            plans.append(
                {
                    "term": inst.get("term"),
                    "monthly_fee": inst.get("totalTermPrice"),
                    "total_price": inst.get("totalPrice"),
                    "interest_rate": inst.get("interestRate"),
                }
            )
        plans = [p for p in plans if p.get("term") is not None]
        if issuer and plans:
            offers.append({"bank": issuer, "plans": plans})
    if offers:
        out["offers"] = offers
    return out if out else None


def _build_delivery(product_data, shared_props):
    pid = _sp_product_id(product_data, shared_props)
    if pid is None:
        return None
    item_number, listing_id = _sp_delivery(shared_props)
    if item_number is None or listing_id is None:
        return None
    data = _safe_api_call(api.get_delivery_date_from_api, pid, item_number, listing_id)
    if not isinstance(data, dict):
        return None
    result = data.get("result")
    if not isinstance(result, dict):
        return None
    dates = result.get("deliveryDates")
    if not isinstance(dates, list) or not dates:
        return None
    entry = dates[0]
    out = {
        "delivery_start": entry.get("deliveryStartDate"),
        "delivery_end": entry.get("deliveryEndDate"),
        "cargo_start": entry.get("cargoStartDate"),
        "cargo_companies": entry.get("cargoCompanies") or [],
    }
    out = {k: v for k, v in out.items() if v is not None}
    fast = entry.get("fastDeliveryOptions")
    if isinstance(fast, list) and fast:
        out["fast_delivery_options"] = fast
    return out if out else None


def _build_merchant_questions(product_data, shared_props):
    pid = _sp_product_id(product_data, shared_props)
    if pid is None:
        return None
    data = _safe_api_call(api.get_merchant_questions_from_api, pid)
    if not isinstance(data, dict):
        return None
    questions = data.get("questions")
    if not isinstance(questions, dict):
        questions = (
            data.get("result", {}).get("questions")
            if isinstance(data.get("result"), dict)
            else None
        )
    if not isinstance(questions, dict):
        return None
    out = {}
    if questions.get("totalElements") is not None:
        out["total"] = questions["totalElements"]
    entries = []
    for q in questions.get("content") or []:
        if not isinstance(q, dict):
            continue
        entry = {"question": q.get("text")}
        answer = q.get("answer")
        if isinstance(answer, dict):
            ans_text = answer.get("text") or answer.get("originalText")
            if ans_text:
                entry["answer"] = ans_text
        if q.get("sellerName"):
            entry["seller"] = q["sellerName"]
        if q.get("answeredDateMessage"):
            entry["answered"] = q["answeredDateMessage"]
        if entry:
            entries.append(entry)
    if entries:
        out["questions"] = entries[:4]
    return out if out else None


def _build_seller_store(product_data, shared_props):
    seller_id = _sp_seller_id(shared_props)
    if seller_id is None:
        return None
    data = _safe_api_call(api.get_seller_store_from_api, seller_id)
    if not isinstance(data, dict):
        return None
    result = data.get("result")
    if not isinstance(result, dict):
        return None
    out = {
        "name": result.get("name") or result.get("officialName"),
        "score": result.get("score"),
        "product_count": result.get("productCount"),
        "official_name": result.get("officialName"),
        "store_url": result.get("storeUrl"),
    }
    out = {k: v for k, v in out.items() if v is not None}
    ranking = result.get("rankingInfo")
    if isinstance(ranking, dict) and ranking.get("text"):
        out["ranking"] = ranking["text"]
    metrics = []
    for m in result.get("sellerMetrics") or []:
        if isinstance(m, dict) and m.get("title") is not None:
            metrics.append(
                {"title": m.get("title"), "value": m.get("value"), "id": m.get("id")}
            )
    if metrics:
        out["metrics"] = metrics
    return out if out else None


def _build_seller_follower(product_data, shared_props):
    seller_id = _sp_seller_id(shared_props)
    if seller_id is None:
        return None
    data = _safe_api_call(api.get_seller_follower_from_api, seller_id)
    if not isinstance(data, dict):
        return None
    result = data.get("result")
    if not isinstance(result, dict):
        return None
    out = {}
    if result.get("count") is not None:
        out["count"] = result["count"]
    if result.get("text"):
        out["text"] = result["text"]
    if result.get("hasCoupon") is not None:
        out["has_coupon"] = result["hasCoupon"]
    return out if out else None


def _build_seller_acceptance(product_data, shared_props):
    seller_id = _sp_seller_id(shared_props)
    if seller_id is None:
        return None
    data = _safe_api_call(api.get_seller_acceptance_from_api, seller_id)
    if not isinstance(data, dict):
        return None
    if data.get("isSellerAcceptQuestions") is not None:
        return {"accepts_questions": data["isSellerAcceptQuestions"]}
    return None


def _build_product_eligibility(product_data, shared_props):
    category_id = _sp_category_id(shared_props)
    price = _sp_selling_price(shared_props)
    if category_id is None or price is None:
        return None
    data = _safe_api_call(api.get_product_eligibility_from_api, category_id, 13, price)
    if not isinstance(data, dict):
        return None
    result = data.get("result")
    if not isinstance(result, dict):
        return None
    out = {}
    if result.get("eligible") is not None:
        out["eligible"] = result["eligible"]
    if result.get("maxLoanTerm") is not None:
        out["max_loan_term"] = result["maxLoanTerm"]
    if result.get("productDetailSlogan"):
        out["slogan"] = result["productDetailSlogan"]
    banners = result.get("banners")
    if isinstance(banners, list) and banners:
        clean = []
        for b in banners:
            if isinstance(b, dict) and b.get("title"):
                clean.append({"title": b["title"], "content": b.get("content")})
        if clean:
            out["banners"] = clean
    return out if out else None


def _build_slicing_attributes(product_data, shared_props):
    pid = _sp_product_id(product_data, shared_props)
    group_id = _sp_p_group_id(shared_props)
    if pid is None or group_id is None:
        return None
    data = _safe_api_call(api.get_slicing_attributes_from_api, group_id, pid)
    if not isinstance(data, dict):
        return None
    result = data.get("result")
    if not isinstance(result, list) or not result:
        return None
    attrs = []
    for attr in result:
        if not isinstance(attr, dict):
            continue
        values = []
        for v in attr.get("values") or []:
            if not isinstance(v, dict):
                continue
            values.append(
                {
                    "name": v.get("name") or v.get("beautifiedName"),
                    "is_selected": v.get("isSelected"),
                    "product_count": len(v.get("products") or [])
                    if isinstance(v.get("products"), list)
                    else None,
                }
            )
        values = [x for x in values if x.get("name")]
        if attr.get("title") and values:
            attrs.append(
                {"title": attr["title"], "type": attr.get("type"), "values": values}
            )
    return attrs if attrs else None


def _build_complete_the_look(product_data, shared_props):
    pid = _sp_product_id(product_data, shared_props)
    if pid is None:
        return None
    data = _safe_api_call(api.get_complete_the_look_from_api, pid)
    if not isinstance(data, dict):
        return None
    result = data.get("result")
    if isinstance(result, dict) and isinstance(result.get("markers"), list):
        return result["markers"]
    if isinstance(result, list):
        return result
    return None


def _build_social_proof(product_data, shared_props):
    pid = _sp_product_id(product_data, shared_props)
    if pid is None:
        return None
    data = _safe_api_call(api.get_social_proof_from_api, str(pid))
    if not isinstance(data, dict):
        return None
    out = {}
    for val in data.values():
        if not isinstance(val, dict):
            continue
        for proof in val.get("socialProofs") or []:
            if isinstance(proof, dict) and proof.get("id"):
                out[proof["id"]] = proof.get("count")
    return out if out else None


def _build_video(product_data, shared_props):
    video_id = _sp_video_id(shared_props)
    if video_id is None:
        warn("api.builder.skip", builder="_build_video", reason="video_id_missing")
        return None
    data = _safe_api_call(api.get_video_content_from_api, video_id)
    if not isinstance(data, dict):
        return None
    result = data.get("result")
    if not isinstance(result, dict):
        return None
    out = {
        "url": result.get("url"),
        "thumbnail": result.get("thumbnail"),
        "duration": result.get("duration"),
        "view_count": result.get("viewCount"),
    }
    out = {k: v for k, v in out.items() if v is not None}
    return out if out else None


def _build_stickers(product_data, shared_props):
    sticker_ids = _sp_sticker_ids(shared_props)
    if sticker_ids is None:
        warn(
            "api.builder.skip", builder="_build_stickers", reason="sticker_ids_missing"
        )
        return None
    if isinstance(sticker_ids, (list, tuple)):
        sticker_ids = ",".join(str(x) for x in sticker_ids)
    data = _safe_api_call(api.get_stickers_from_api, sticker_ids)
    if not isinstance(data, dict):
        return None
    result = data.get("result")
    if not isinstance(result, list) or not result:
        return None
    stickers = []
    for s in result:
        if isinstance(s, dict) and (s.get("stickerImageUrl") or s.get("description")):
            stickers.append(
                {
                    "image": s.get("stickerImageUrl"),
                    "description": s.get("description"),
                    "is_authorized_seller": s.get("isAuthorizedSellerSticker"),
                }
            )
    return stickers if stickers else None


def _build_stamps(product_data, shared_props):
    tag_ids = _sp_tag_ids(shared_props)
    if tag_ids is None:
        return None
    if isinstance(tag_ids, (list, tuple)):
        tag_ids = ",".join(str(x) for x in tag_ids)
    data = _safe_api_call(api.get_stamps_from_api, tag_ids)
    if not isinstance(data, dict):
        warn(
            "api.builder.skip", builder="_build_stamps", reason="response_not_an_object"
        )
        return None
    result = data.get("result")
    if not isinstance(result, dict) or not result:
        warn(
            "api.builder.skip",
            builder="_build_stamps",
            reason="result_empty_or_not_an_object",
        )
        return None
    stamps = []
    for stamp_info in result.values():
        if not isinstance(stamp_info, dict):
            continue
        display = stamp_info.get("displayName") or stamp_info.get("name")
        for stamp in stamp_info.get("stamps") or []:
            if isinstance(stamp, dict) and stamp.get("stampUrl"):
                stamps.append(
                    {
                        "image": stamp["stampUrl"],
                        "display_name": display,
                        "position": stamp.get("position"),
                        "type": stamp.get("stampType") or stamp.get("type"),
                    }
                )
    if not stamps:
        warn(
            "api.builder.skip",
            builder="_build_stamps",
            reason="no_stamp_url_in_response",
        )
        return None
    return stamps


def _build_currencies(product_data, shared_props):
    data = _safe_api_call(api.get_currencies_from_api)
    if not isinstance(data, dict):
        return None
    result = data.get("result")
    if not isinstance(result, list) or not result:
        return None
    currencies = []
    for c in result:
        if isinstance(c, dict) and c.get("currencyName"):
            currencies.append({"name": c["currencyName"], "rate": c.get("tcmbRate")})
    return currencies if currencies else None
