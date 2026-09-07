# Redux Store (`script#reduxStore`)

The Hepsiburada PDP embeds the render state of the React/Redux app in a single script tag with `id="reduxStore"`:

``` html
<script id="reduxStore" type="application/json">{"accountState":{...},"productState":{...},...}</script>
```

Unlike Trendyol's `__envoy__SHARED_PROPS`, this tag contains a **self-contained JSON document**, so it can be parsed with a first-`{`/last-`}` slice followed by `json.loads`.

Captured from the live test product at `redux_store.json`:
`https://www.hepsiburada.com/razer-blackshark-v2-pro-2023-kablosuz-gaming-kulaklik-beyaz-rz04-04530200-r3m1-p-HBCV00004MW5Q6` (sku: `HBCV00004MW5Q6`).

## Extraction

`_extract_redux_store(soup)` (`src/scrape/utils/hepsiburada.py:78`):

1. Selects `script#reduxStore`.
2. Takes `script.string`, finds the first `{` and the last `}`, and `json.loads` the slice.
3. Returns the store dict, or `None` on missing tag / parse failure.

The product-relevant subset is `store.productState.product`, reached via `_extract_redux_product(redux)` (`hepsiburada.py:248`) which unwraps `redux to productState to product`.

## Top-level state slices

The store root has 34 slices. The product page uses the first two; the rest are app scaffolding (search, cart, filters, campaigns, etc.):

| Slice | Purpose |
| --- | --- |
| `accountState` | user info, cookie/visibility flags |
| `productState` | product, variants, buybox, reviews, breadcrumbs, campaigns, VAS (53 keys) |
| `filterState` / `searchState` / `categoryState` / `merchantState` / ... | page/app state (mostly empty on PDP) |
| `seoState` | `seoInfo` and dynamic variables |
| `errorState` / `loadState` / `pendingState` | request lifecycle flags |

## `productState.product` (the data used)

68 keys. Same product as the JSON-LD block, but with the buybox/listing/review details the JSON-LD lacks:

| Field | Type | Example Value |
| --- | --- | --- |
| `sku` | string | `HBCV00004MW5Q6` |
| `productId` | string | `HBC00004Q2IO3` |
| `name` | string | `Razer BlackShark V2 Pro 2023 Kablosuz Gaming Kulaklık, Beyaz RZ04-04530200-R3M1` |
| `slugName` | string | `razer-blackshark-v2-pro-2023-kablosuz-gaming-kulaklik-beyaz-rz04-04530200-r3m1` |
| `barcode` / `gtin` | string | `8887910060131` |
| `definitionId` | number | `297` |
| `definitionName` | string | `Kulaklık - Mikrofon` |
| `taxVatRate` | number | `20` |
| `brandId` / `brand` | number / object | brand metadata |
| `merchantId` / `merchantName` | string | `b38d2d14-6ccf-4fc8-a543-c85dfab931f3`, `Nethouse` (**product owner**) |
| `merchantCity` / `merchantCountry` | string | `İSTANBUL`, `TÜRKİYE` (owner; the winning seller's city is in the listing/ctx, see below) |
| `shipmentDay` / `shippingProfileId` | number / string | `0`, `869cd042-e2cf-42fa-ade3-052b4b39911b` |
| `categories` | array | 5 levels of `{ categoryId, categoryName, categoryLevel, urlKeyword, breadcrumbTitle }` |
| `rootCategoryList` | array | `["2147483646","3013120","18","520","60004548"]` |
| `listings` | array | all seller listings (see below) |
| `reviews` | object | `{ hasMedia, customerReviewScore: 4.6, customerReviewCount: 82 }` |
| `installmentBox` / `numberOfInstallments` | ... | installment options |
| `prices` / `unitPrice` / `winnerFreight` | ... | price context |

### `listings[]`

Each element is one seller offer (2 sellers captured for this product):

| Field | Value |
| --- | --- |
| `merchantId` | `ed81e61b-1bdc-4f7d-8bdf-73ecae0f7334` (EMC&BİLİSİM&TEKN) / `54b07e98-28fa-47f1-aaf3-2e79b5c6f346` (Razer Shop) |
| `listingId` | `c8300905-6f5c-41fc-832b-f21447d3e4e3` (EMC&BİLİSİM&TEKN) / `54b07e98-...` (Razer Shop) |
| `merchantName` | `EMC&BİLİSİM&TEKN` / `Razer Shop` |
| `freeShipping` / `fastShipping` | bool |
| `shipmentDay` / `shipmentType` | `0` / `businessDays` |
| `isSalable` | bool |

## Usage in the pipeline

- `_extract_product_ctx(soup, product_data)` (`hepsiburada.py:395`) builds the product context dict. Order:
    1. **JSON-LD** (`product_data`): `sku`, `url` from `offers.url`.
    2. **Redux store** (`productState.product`, `listings[0]`): any empty field above is backfilled - `sku`, `url`, `product_id`, `definition_id`, `definition_name`, `tax_vat_rate`, `merchant_id`, `listing_id`, `merchant_name`, `warehouse_id`, `shipment_day`, `shipping_profile_id`, `merchant_city`, `merchant_country`; plus `root_category_list` / `root_buying_category_list` from `product.categories` (leaf = buying category).
    3. **URL fallback**: when `url` is missing but `slugName` + sku exist: `https://www.hepsiburada.com/{slugName}-p-{sku}`.
    4. **Raw HTML regex backfill** (`hepsiburada.py:479-511`): regardless of redux presence, missing `definitionId`, `definitionName`, `taxVatRate`, `productId`, and `rootCategoryList` are searched directly in the HTML source (`"definitionId":(\d+)`, `"definitionName":"([^"]+)"`, `"taxVatRate":(\d+)`, `"productId":"([^"]+)"`, `"rootCategoryList":(\[...\])`).
- `_extract_custom_data(product_data, redux_product)` (`:300`) and `_extract_detected_category` style helpers consume `productState.product` for `custom_data` (e.g. merchant, category path, listings) and category detection.
- `_extract_availability(product_data, redux_product)` (`:289`) uses the redux product's `isInStock`/stock fields.

## Notes

- **Owner vs winning seller**: `productState.product.merchantName` = "Nethouse" is the *product owner* (with `merchantCity` `İSTANBUL`). The buybox/context merchant is `listings[0]` - EMC&BİLİSİM&TEKN (`ed81e61b-...`, city `İZMİR` per the ctx) - which is what `_extract_product_ctx` backfills into `merchant_id`/`listing_id`/`merchant_name`.
- `custom_data.merchant` carries the **owner** name ("Nethouse"), while `product_ctx.merchant_name` carries the **winning listing** seller (EMC&BİLİSİM&TEKN).
- The buybox **price** (`7890.00 TL`) matches JSON-LD `offers.price` and `productState.product.prices[1]` (`{"value": 7890, "discountRate": 1}`), NOT the `listings[].price` values (8069.05 / 9349.15 in `custom_data.listings`).
- `definitionId`/`definitionName`/`taxVatRate` are also embedded in the raw HTML as JSON fragments, which is why the regex backfill works even when the redux tag is absent or malformed.
- `reviews.customerReviewScore` (4.6) / `customerReviewCount` (82) match the JSON-LD `aggregateRating`, but with more fields available (`hasMedia`, etc.).