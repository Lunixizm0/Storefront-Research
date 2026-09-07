# Preloaded State (`__PRELOADED_STATE__` to `apolloState`)

MediaMarkt's PDP is an Apollo Client app rendered server-side. The React app's initial Apollo cache is embedded in a script assignment:

``` js
window.__PRELOADED_STATE__ = { ..., "apolloState": { ... } }
```

The `apolloState` object is a normalised Apollo cache: a flat map of **entity keys** (`"GraphqlProduct:Media:tr-TR:1232522"`, `"CofrPriceFeature:{\"id\":\"Media:tr:1232522\",...}"`, ...) to entity objects. Entities cross-reference each other with `{ "__ref": "<key>" }`.

Captured from the live test product into `tests/fixtures/mediamarkt/apollo_state.json`:
`https://www.mediamarkt.com.tr/tr/product/_dyson-v15-detect-kablosuz-sarjli-dikey-supurge-sari-nikel-1232522.html` (product id `1232522`).

## Extraction

`_extract_preloaded_state(soup)` / `_extract_apollo_state(soup)` (`src/scrape/utils/mediamarkt/parsing.py`):

1. Scan inline `script` tags for the `__PRELOADED_STATE__` marker.
2. Take the value after the `=`, strip the trailing `;`, and `json.loads` it.
3. Locate the `"apolloState"` key inside, then bracket-match from its first `{` to the matching `}` (honouring string literals/escapes) and `json.loads` that slice.

`extract_product_data(soup, url)` returns `(state, product_id)`. The product id is parsed from the URL with `_product_id_from_url` (regex `-(\d+)\.html$`), with a fallback that scans for any `GraphqlProduct:Media:tr-TR:*` key when the URL is missing/unparseable.

## Key Entities

| Entity key prefix | Purpose |
| --- | --- |
| `GraphqlProduct:Media:tr-TR:{id}` | Product core (title, manufacturer, breadcrumbs, EAN, URL, description) |
| `GraphqlProductAggregate:Media:tr-TR:{id}` | Aggregate root to `product`, `matchingProduct`, `availability` refs |
| `Availability:Media:{id}` | Availability record (`uber` = availability response) |
| `CofrPriceFeature:...` | Price: `price.amount`/`shippingCost`/`installment`, `promoPrice.amount`/`promoIds`, `vatRate`, `currency` |
| `CofrCoreFeature:Media:tr:{id}` | Manufacturer/name, review statistics, `highlightedFeatures[]`, category path refs |
| `CofrCoreFeatureProductFeature:Media:tr:{id}:{featureId}` | Highlight rows (`name`, `values`) |
| `CofrMediaAssetsFeature:Media:tr:{id}` | `productMainImage`, `productImages[]` (`link`, `imageId`, `altText`) |
| `CofrOnlineStatusFeature:Media:tr:{id}` | `onlineStatus`, `isAvailableForDelivery/Pickup/AndBuyable`, `isInAssortment` |
| `CofrDeliveryFeature:Media:tr:{id}` | `delivery.deliveryStatus`/`displayStatus`, `releaseDate` |
| `CofrPickupFeature:Media:tr:{id}` | `pickupStatus`/`displayStatus`, `isProductPickable` |
| `CofrBundleItemsFeature` / `CofrEnergyEfficiencyFeature` / `CofrRefurbishedGoodsFeature` | Bundle / energy label / refurbished offer stubs |
| `GraphqlProductFeatureGroups:{id}` | Feature groups to `features[]` refs |
| `GraphqlProductFeature:{groupId}:{groupedValue}` | Feature rows (`name`, `value`, rendered) |
| `GraphqlServiceProductV2:...` | Value-added services (warranty/insurance offers) |
| `GraphqlReview` / `GraphqlReviewer` | Review entries (rating, title, date, feedback, reviewer ref) |
| `CofrCatalogDataApiCategoryPathElement:{categoryId}` | Category path elements (`categoryName`) |

### `GraphqlProduct` (core)

| Field | Type | Example |
| --- | --- | --- |
| `id` | string | `1232522` |
| `title` | string | `DYSON V15 Detect Absolute Şarjlı Dikey Süpürge` |
| `rawTitle` | string | `V15 DETECT KABLOSUZ SUPURGE.` |
| `kindOfProduct` | string | `CORDLESS_VACUUM_CLEANER` |
| `featureName` | string | `ŞARJLI ELEKTRİKLİ SÜPÜRGE` |
| `manufacturer` / `manufacturerId` | string | `DYSON` / `55` |
| `ean` | string | `5025155081754` |
| `url` | string | `/tr/product/_dyson-v15-...-1232522.html` |
| `breadcrumbs[]` | array | `{ categoryId, name }` - `Ev Aletleri & Yaşam(CAT_TR_MM_465737) to Süpürgeler to Dikey Süpürge to Şarjlı Dikey Süpürge(CAT_TR_MM_806513)` |
| `description` | string | HTML with escaped tags (see *Description decoding* below) |
| `productGroupId` | number | `736` |
| `vat` / `tax` | object / number | `{ rate: 0.2 }` / `20` |
| `globalLoyItemAssessment` | object \| null | Inline loyalty points when present (see [graphql](mediamarkt-graphql)) |

### `CofrPriceFeature` (price)

Key example (`"CofrPriceFeature:{\"id\":\"Media:tr:1232522\",\"price\":{\"installment\":{\"__typename\":\"CofrPriceFeaturePriceInstallment\"}}}"`):

| Field | Type | Example |
| --- | --- | --- |
| `currency` | string | `TRY` |
| `price.amount` | number | `34897` |
| `price.shippingCost` | number | `39.99` |
| `price.installment` | object | `{ duration: 4, monthlyRate: 8724.25, totalAmount: 34897 }` |
| `promoPrice.amount` | number | `34897` (price actually used by the pipeline) |
| `promoPrice.promoIds` | array | `["986422b2-241b-4010-b16a-a896d8068ad2"]` |
| `vatRate` | number | `0.2` |
| `productGroupId` | number | `736` |

Note the `__ref`-style keys always contain the product id, so `_price_values` matches `CofrPriceFeature:` + product id and the *promo* price wins.

### `CofrCoreFeature` (reviews + highlights)

| Field | Type | Example |
| --- | --- | --- |
| `productName` / `manufacturerName` | string | `DYSON V15 Detect Absolute Şarjlı Dikey Süpürge` / `DYSON` |
| `reviewStatistics` | object | `{ averageOverallRating: 4.5909, totalReviewCount: 44, overallRatingRange: 5 }` (Bazaarvoice) |
| `highlightedFeatures[]` | array | refs to `CofrCoreFeatureProductFeature`, e.g. `Ağırlık (Üreticiye Göre) to "3.1 kg"` |
| `breadcrumbs[]` | array | refs to `CofrCatalogDataApiCategoryPathElement` |

### Reviews (`GraphqlReview`, Bazaarvoice)

Each review has `rating`, `title`, `date`, `contentLocale`, `isVerifiedPurchaser`, `feedback.{advantages,disadvantages,full}`, `reviewer` ref, `sourceClient: "mediamarkt-tr"`. The dataset uses the aggregate `reviewStatistics` from `CofrCoreFeature`, not the individual reviews.

### Description decoding

SSR description is delivered with escaped angle brackets: `<lt/>` / `<gt/>`. `_decode_mm_html` (`parsing.py`) restores them, then `_build_description` runs the string through BeautifulSoup to plain text.

## Mapping to the dataset

| Dataset field | Source |
| --- | --- |
| `name` / `brand` | `GraphqlProduct.title` / `manufacturer` |
| `category` | leaf breadcrumb (`_iter_breadcrumbs`, last name) |
| `price` / `currency` | `CofrPriceFeature.promoPrice.amount` (fallback `price.amount`), `currency` |
| `sku` | product id from URL / entity |
| `url` | `GraphqlProduct.url` absolutised against `https://www.mediamarkt.com.tr` |
| `image` | `CofrMediaAssetsFeature.productMainImage.link` (fallback `productImages[0].link`) |
| `description` | decoded + textified `GraphqlProduct.description` |
| `availability` | derived from `CofrOnlineStatusFeature` / `CofrDeliveryFeature` / `CofrPickupFeature` (`OutOfStock`/`InStock`/`PreOrder`) |
| `reviews` | `CofrCoreFeature.reviewStatistics` (`average_rating`, `count`, `overall_rating_range`) |
| `vas` | `GraphqlServiceProductV2` entities (`product_id`, `title`, `price`) |
| `installments` | `CofrPriceFeature.price.installment` |
| `custom_data` | see `_build_custom_data`: price, shipping_cost, promo_ids, vat_rate, product_group_id, ean, tax, manufacturer, feature_name, kind_of_product, raw_title, category_path, loyalty_points, feature_groups, status, highlights, full_features, va_services (+ `graphql` supplementary, + `product_id`/`url` injected by the caller) |

## Notes

- `availability` is not schema.org - it is one of the plain strings `InStock` / `OutOfStock` / `PreOrder` derived from the online/delivery/pickup statuses (`_availability_text` in `builders.py`).
- `item_condition` is always `null` for MediaMarkt (no schema.org offer data).
- The aggregate root entity is `GraphqlProductAggregate:Media:tr-TR:{productId}`; the pipeline reads the `GraphqlProduct:Media:tr-TR:{productId}` node directly.
- Loyalty points may already be present inline (`GraphqlProduct.globalLoyItemAssessment`); when absent, the pipeline falls back to the GraphQL loyalty query (see [graphql](mediamarkt-graphql)).