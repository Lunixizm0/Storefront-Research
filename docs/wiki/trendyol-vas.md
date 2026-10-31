# Satışla Birlikte Önerilen Ekstra Ürünler (VAS)

Retrieves value-added services (VAS) offered alongside a product purchase - e.g. extended warranty / insurance packages with a calculated price, seller, category, and marketing description. This is a `POST` endpoint.

## Endpoint

```
POST https://apigw.trendyol.com/discovery-storefront-trproductgw-service/api/vas/
```

## Query Parameters

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| `storefrontId` | number | NO | e.g. `1`. |
| `language` | string | NO | e.g. `tr`. |
| `channelId` | number | NO | The sales channel identifier. Use `1` for the web channel. |

## Request Body (required)

All fields are required. Values are extracted from `shared_props["product"]`.

```json
{
  "categoryId": 1058,
  "brandId": 11079,
  "sellerId": 968,
  "sellingPrice": 3839,
  "attributes": [
    { "key": "Garanti Tipi", "value": "Resmi Distribütör Garantili" }
  ]
}
```

| Field | Source | Description |
| --- | --- | --- |
| `categoryId` | `shared_props["product"]["category"]["id"]` | Product category ID. |
| `brandId` | `shared_props["product"]["brand"]["id"]` | Brand ID. |
| `sellerId` | `shared_props["product"]["merchantListing"]["merchant"]["id"]` | Top seller/merchant ID. |
| `sellingPrice` | `shared_props["product"]["merchantListing"]["winnerVariant"]["price"]["sellingPrice"]["value"]` | Current selling price. |
| `attributes` | `shared_props["product"]["attributes"]` (flattened) | Product attributes. Each entry's `value` must be a **string** (the attribute name), not an object - using `{id, name}` objects causes a `400` deserialization error. |

## Response

Top-level wrapper: `{ "isSuccess", "statusCode", "result" }`. The `result` is an array of VAS offers, each with:

- **`id`** - VAS offer id (UUID).
- **`calculatedPrice`** / **`calculatedPriceText`** / **`calculatedPriceTextWithCurrency`** - price and formatted variants.
- **`currency`** - e.g. `TRY`.
- **`category`** / **`categoryId`** - e.g. `Sigorta` / `1000`.
- **`description`** - array of marketing description lines.
- **`sellerId`** / **`sellerName`** - offering seller.
- **`sellerLandingUrl`** / **`sellerLogoUrl`** - seller links.
- **`subCategory`** / **`subCategoryId`** - e.g. `3 Yıl Ek Garanti` / `1004`.
- **`variant`** - `{ name, message }` selection rules.

## Example Response

``` json
{
  "isSuccess": true,
  "statusCode": 200,
  "result": [
    {
      "id": "234e2a629d5433086e402394cf67037a",
      "calculatedPrice": 881,
      "calculatedPriceText": "881",
      "calculatedPriceTextWithCurrency": "881 TL",
      "currency": "TRY",
      "category": "Sigorta",
      "categoryId": 1000,
      "description": ["2 ay ücretsiz YouTube Premium!", "Garantini 3 yıl daha uzat!"],
      "sellerId": 463180,
      "sellerName": "Trendyol Sigorta",
      "subCategory": "3 Yıl Ek Garanti",
      "subCategoryId": 1004
    }
  ]
}
```