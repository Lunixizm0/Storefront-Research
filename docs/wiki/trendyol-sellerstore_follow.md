# Satıcı Takipçi Sayısı

Retrieves the follower count of a merchant's store, along with a human-readable formatted value and coupon availability.

## Endpoint

```
GET https://apigw.trendyol.com/discovery-storefront-trproductgw-service/api/sellerstore-follow/{sellerId}/follower-count
```

## Path Parameters

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| `sellerId` | number | Yes | The merchant/seller id (e.g. `624588`). |

## Query Parameters

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| `culture` | string | NO | Locale used for number formatting, e.g. `tr-TR`. |
| `checkCoupon` | boolean | NO | e.g. `true`. |
| `channelId` | number | Yes | The sales channel identifier. Use `1` for the web channel. |

## Example GET
```
GET https://apigw.trendyol.com/discovery-storefront-trproductgw-service/api/sellerstore-follow/624588/follower-count?channelId=1
```

## Response

``` json
{
    "isSuccess": true,
    "statusCode": 200,
    "result": {
        "count": 184250,
        "text": "184,2B"
    }
}
```

- **`count`** - raw follower count (integer).
- **`text`** - human-readable formatted count (e.g. `184,0B`).
- **`hasCoupon`** - whether the store has a follower coupon.
- **`coupon`** - coupon object (empty `{}` when none).