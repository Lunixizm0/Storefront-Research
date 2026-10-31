# Ürün Rozetleri / Damgaları (Stamps)

Retrieves the promotional stamps/rozet badges applied to a product given a set of tag ids (e.g. "Peşin Fiyatına 3 Taksit", "10 Günün En Düşük Fiyatı"). Each tag yields one or more stamp variants (image-based and text-based) with position, priority, and color.

## Endpoint

```
GET https://apigw.trendyol.com/discovery-storefront-trproductgw-service/api/stamps/
```

## Query Parameters

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| `tagIds` | string | Yes | URL-encoded, comma-separated tag ids (e.g. `13217,13212,13685,13207`). |
| `platform` | string | NO | e.g. `WEB`. |
| `channelId` | number | NO | The sales channel identifier. Use `1` for the web channel. |
| `storefrontId` | number | NO | Storefront identifier. |

The `tagIds` come from the product's shared state; each tag id maps to a named stamp.

## Response

Top-level wrapper: `{ "isSuccess", "statusCode", "result" }`. The `result` is an object keyed by `tagId`. Each value has:

- **`name`** - internal name (e.g. `installment_pft3`).
- **`displayName`** - semantic name (e.g. `Peşin Fiyatına 3 Taksit`).
- **`cultures`** - array of locales (e.g. `["tr-TR"]`).
- **`isSearchable`** - boolean.
- **`stamps`** - array of stamp renderings, each with:
    - `stampType` - e.g. `payment`, `LowestPriceDuration`.
    - `type` - `TypeA` (image) or `TypeB` (text).
    - `stampUrl` - image URL for `TypeA`, empty for `TypeB`.
    - `stampText` - text for `TypeB` (e.g. `Peşin Fiyatına 3 Taksit`).
    - `colorCode` - text color for `TypeB`.
    - `position` - overlay position (e.g. `lower-left`, `upper-left`).
    - `priority` - display priority.
    - `aspectRatio` - aspect ratio.

## Example

**Request:**

```
GET https://apigw.trendyol.com/discovery-storefront-trproductgw-service/api/stamps/?tagIds=13217,13212,13685,13207&channelId=1&storefrontId=1&platform=web
```

**Response:**

``` json
{
    "isSuccess": true,
    "statusCode": 200,
    "result": {
        "4905": {
            "name": "installment_pft3",
            "displayName": "Peşin Fiyatına 3 Taksit",
            "cultures": [
                "tr-TR"
            ],
            "stamps": [
                {
                    "stampUrl": "/indexing-sticker-stamp/mars/2eca585d-1905-44a4-898e-965cb78d033a.png",
                    "position": "lower-left",
                    "stampType": "payment",
                    "type": "TypeA",
                    "priority": 900,
                    "aspectRatio": 0.25
                },
                {
                    "stampText": "Peşin Fiyatına 3 Taksit",
                    "stampUrl": "",
                    "position": "lower-left",
                    "stampType": "payment",
                    "type": "TypeB",
                    "colorCode": "#343BBF",
                    "priority": 900,
                    "aspectRatio": 0.25
                }
            ],
            "isSearchable": false
        },
        "8581": {
            "name": "son 10 günün en düşük fiyatı",
            "displayName": "son 10 günün en düşük fiyatı",
            "cultures": [
                "tr-TR"
            ],
            "stamps": [
                {
                    "stampUrl": "/indexing-sticker-stamp/mars/81901534-f3f6-4495-8d32-d2bcc648ec11.png",
                    "position": "upper-left",
                    "stampType": "LowestPriceDuration",
                    "type": "TypeA",
                    "priority": 997,
                    "aspectRatio": 0.25
                },
                {
                    "stampText": "10 Günün En Düşük Fiyatı",
                    "stampUrl": "",
                    "position": "upper-left",
                    "stampType": "LowestPriceDuration",
                    "type": "TypeB",
                    "colorCode": "#BB0000",
                    "priority": 997,
                    "aspectRatio": 0.25
                }
            ],
            "isSearchable": false
        },
        "9637": {
            "name": "eventdeal",
            "displayName": "eventdeal",
            "cultures": [
                "tr-TR"
            ],
            "stamps": [],
            "isSearchable": true
        }
    }
}
```